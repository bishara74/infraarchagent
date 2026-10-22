import {render,screen,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {MemoryRouter} from 'react-router';
import {expect,it,vi} from 'vitest';
import {api} from '../api/client';
import {hydratePreferences} from '../lib/preferences';
import {RecentRunsScreen} from './RecentRunsScreen';
it('FR-UI-01 recent history errors provide Retry and recover a populated list',async()=>{
 const request=vi.spyOn(api,'request').mockRejectedValue(new Error('offline'));
 await hydratePreferences('recent-error-test');render(<MemoryRouter><RecentRunsScreen/></MemoryRouter>);
 expect(screen.getByRole('alert')).toHaveTextContent('Unable to load recent runs');expect(screen.queryByText('No runs yet — start one from New request')).toBeNull();
 request.mockImplementation(async url=>(url.endsWith('recent-runs')?[{id:'saved-run',title:'Saved infrastructure request',time:'2026-10-22T12:00:00Z',status:'success',last_seq:8}]:{revision:1,data:{}}) as never);
 await userEvent.click(screen.getByRole('button',{name:'Retry'}));await waitFor(()=>expect(screen.getByRole('link',{name:'Saved infrastructure request'})).toHaveAttribute('href','/runs/saved-run'));expect(screen.queryByRole('alert')).toBeNull();
});
it('FR-UI-01 genuinely empty recent history provides the New request action',async()=>{
 vi.spyOn(api,'request').mockImplementation(async url=>(url.endsWith('recent-runs')?[]:{revision:1,data:{}}) as never);await hydratePreferences('recent-empty-test');render(<MemoryRouter><RecentRunsScreen/></MemoryRouter>);
 expect(screen.getByText('No runs yet — start one from New request')).toBeVisible();expect(screen.getByRole('link',{name:'New request'})).toHaveAttribute('href','/');
});
