import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router';
import {afterEach,expect,it,vi} from 'vitest';
import {api,ApiError} from '../api/client';
import type {FeedbackInsightsData} from '../api/types';
import {FeedbackInsights} from './FeedbackInsights';
import {ReviewHistorySettings} from './ReviewHistorySettings';

const fixture:FeedbackInsightsData={total:3,filters:{},by_category:[{value:'security_concern',count:2,filters:{category:'security_concern'}}],by_variant:[{value:'cost',count:2,filters:{variant:'cost'}}],by_decision:[{value:'reject',count:3,filters:{decision:'reject'}}],blocking_rules:[{rule_id:'CKV_1',count:2,filters:{decision:'reject',blocking_rule:'CKV_1'}}],rejected_total:3,blocking_snapshot_available:2,blocking_snapshot_unavailable:1};
afterEach(()=>vi.restoreAllMocks());

it('FR-UI-07 links deterministic counts to filtered decisions and labels missing snapshots',async()=>{
  vi.spyOn(api,'request').mockResolvedValue(fixture);
  render(<MemoryRouter><FeedbackInsights query="view=insights"/></MemoryRouter>);
  expect(await screen.findByText('2 of 3 rejected decisions have recorded blocking-rule snapshots. 1 unavailable.')).toBeVisible();
  expect(screen.getByRole('link',{name:'View 2 decisions: security concern'})).toHaveAttribute('href','/settings/review-history?category=security_concern');
  expect(screen.getByRole('link',{name:'View 2 rejected decisions for CKV_1'})).toHaveAttribute('href','/settings/review-history?decision=reject&blocking_rule=CKV_1');
});

it('FR-UI-07 switches history views in the URL without loading both endpoints',async()=>{
  const request=vi.spyOn(api,'request').mockResolvedValue(fixture);
  render(<MemoryRouter initialEntries={['/settings/review-history?view=insights']}><ReviewHistorySettings/></MemoryRouter>);
  expect(await screen.findByRole('heading',{name:'Feedback insights'})).toBeVisible();
  expect(request).toHaveBeenCalledExactlyOnceWith('/api/reviews/history/insights?view=insights','GET',undefined,expect.any(AbortSignal));
  request.mockResolvedValue({items:[],total:0,page:1,page_size:25,filters:{}});
  fireEvent.click(screen.getByRole('button',{name:'Decisions'}));
  expect(await screen.findByText('No recorded decisions match these filters.')).toBeVisible();
  await waitFor(()=>expect(request).toHaveBeenLastCalledWith('/api/reviews/history?','GET',undefined,expect.any(AbortSignal)));
});

it('FR-UI-07 supports loading, retry and empty deterministic insights',async()=>{
  vi.spyOn(api,'request').mockRejectedValueOnce(new ApiError(503,'unavailable','Insights are unavailable.')).mockResolvedValueOnce({...fixture,total:0,by_category:[],by_variant:[],by_decision:[],blocking_rules:[],rejected_total:0,blocking_snapshot_available:0,blocking_snapshot_unavailable:0});
  render(<MemoryRouter><FeedbackInsights query=""/></MemoryRouter>);
  expect(screen.getByRole('status')).toHaveTextContent('Loading feedback insights');
  expect(await screen.findByRole('alert')).toHaveTextContent('Insights are unavailable.');
  fireEvent.click(screen.getByRole('button',{name:'Retry insights'}));
  expect(await screen.findByText('No recorded blocking rules match these filters.')).toBeVisible();
});

it('NFR-01 treats rule strings as text and does not create HTML',async()=>{
  const untrusted='<img src=x onerror=alert(1)>';
  vi.spyOn(api,'request').mockResolvedValue({...fixture,blocking_rules:[{rule_id:untrusted,count:1,filters:{decision:'reject'}}]});
  const {container}=render(<MemoryRouter><FeedbackInsights query=""/></MemoryRouter>);
  expect(await screen.findByRole('rowheader',{name:untrusted})).toBeVisible();
  expect(container.querySelector('img')).toBeNull();
});
