import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import App from './App';
import {beforeEach,vi} from 'vitest';
import {api} from './api/client';
import {setSessionStatus} from './lib/sessionState';
beforeEach(()=>{const status={auth_required:false,authenticated:false,mode:'local' as const};setSessionStatus(status);vi.spyOn(api,'session').mockResolvedValue(status);});

describe('application shell', () => {
  it('renders the input screen in the main landmark', () => {
    render(<App />);

    expect(screen.getByRole('main')).toContainElement(
      screen.getByRole('heading', { name: 'Generate infrastructure', level: 1 }),
    );
  });

  it('offers a keyboard-reachable skip link to the focusable main content', async () => {
    const user = userEvent.setup();
    render(<App />);

    await user.tab();

    expect(screen.getByRole('link', { name: 'Skip to content' })).toHaveFocus();
    expect(screen.getByRole('link', { name: 'Skip to content' })).toHaveAttribute(
      'href',
      `#${screen.getByRole('main').id}`,
    );
    expect(screen.getByRole('main')).toHaveAttribute('tabindex', '-1');
  });
});

it('FR-UI-01 authenticated Recent runs hydrates once and remains mounted', async () => {
  window.history.replaceState(null, '', '/recent');
  const status = {auth_required:true,authenticated:true,mode:'account' as const,user:{id:'recent-regression',username:'reviewer',role:'reviewer' as const}};
  setSessionStatus(status);vi.mocked(api.session).mockResolvedValue(status);
  const request=vi.spyOn(api,'request').mockImplementation(async url => (url.endsWith('recent-runs') ? [] : {revision:1,data:{}}) as never);
  render(<App/>);
  expect(await screen.findByText('No runs yet — start one from New request')).toBeVisible();
  await userEvent.click(screen.getByRole('link',{name:'Recent runs'}));
  expect(screen.getByText('No runs yet — start one from New request')).toBeVisible();
  expect(request.mock.calls.filter(([url])=>url==='/api/me/preferences')).toHaveLength(1);
  expect(request.mock.calls.filter(([url])=>url==='/api/me/recent-runs')).toHaveLength(1);
  window.history.replaceState(null,'','/');
});

it('NFR-01 unauthenticated shell shows the logo without navigation or an account menu',async()=>{
 const status={auth_required:true,authenticated:false,mode:'account' as const};setSessionStatus(status);vi.mocked(api.session).mockResolvedValue(status);
 render(<App/>);expect(await screen.findByRole('heading',{name:'Log in'})).toBeVisible();
 expect(screen.queryByRole('navigation',{name:'Main'})).toBeNull();expect(screen.queryByRole('button',{name:'Log out'})).toBeNull();
 expect(screen.getByRole('link',{name:'InfraArchAgent'})).toBeVisible();
});

it('FR-UI-03 query-only navigation preserves control focus and screen changes focus main',async()=>{
 window.history.replaceState(null,'','/?tab=fixture');
 vi.spyOn(api,'request').mockResolvedValue({provider:'stub',credential_id:null,models:[],defaults:{}});
 render(<App/>);const request=screen.getByRole('link',{name:'New request'});await userEvent.click(request);expect(request).toHaveFocus();
 await userEvent.click(screen.getByRole('link',{name:'Recent runs'}));expect(screen.getByRole('main')).toHaveFocus();window.history.replaceState(null,'','/');
});

it('NFR-01 schema mismatch is actionable at the app boundary',async()=>{
 const {ApiError}=await import('./api/client');
 vi.mocked(api.session).mockRejectedValue(new ApiError(503,'database_schema_mismatch','Database schema is at 0012, code expects 0014 — run `make migrate`, then restart the server.'));
 render(<App/>);
 expect(await screen.findByText(/Database schema is at 0012/)).toHaveTextContent('run `make migrate`');
 expect(screen.queryByRole('heading',{name:'Log in'})).toBeNull();
});

it('NFR-01 preference hydration preserves the schema repair message',async()=>{
 const {ApiError}=await import('./api/client');
 const status={auth_required:true,authenticated:true,mode:'account' as const,user:{id:'schema-regression',username:'reviewer',role:'reviewer' as const}};
 setSessionStatus(status);vi.mocked(api.session).mockResolvedValue(status);
 vi.spyOn(api,'request').mockRejectedValue(new ApiError(503,'database_schema_mismatch','Database schema is behind — run `make migrate`, then restart the server.'));
 render(<App/>);
 expect(await screen.findByText('Database schema is behind — run `make migrate`, then restart the server.')).toBeVisible();
 expect(screen.queryByText(/Saved preferences could not be loaded/)).toBeNull();
});
