import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {MemoryRouter} from 'react-router';
import {afterEach,expect,it,vi} from 'vitest';
import {api,ApiError} from '../api/client';
import {setSessionStatus} from '../lib/sessionState';
import {SettingsScreen} from './SettingsScreen';
import {ReviewHistorySettings,type History} from './ReviewHistorySettings';
const data:History={items:[{run_id:'fixture',variant:'cost',label_before:'checks_passed',label_after:'rejected',decision:'reject',category:'too_expensive',reason:'Engineering judgement',reviewer:'Engineer',timestamp:'2026-10-24T12:00:00+00:00'}],total:30,page:1,page_size:25,filters:{category:'too_expensive'}};
afterEach(()=>{vi.restoreAllMocks();setSessionStatus(null);});
it('FR-UI-07 history filters reset pages, exports all matching rows and displays active count',async()=>{
 const request=vi.spyOn(api,'request').mockResolvedValue(data);
 const exported=vi.spyOn(api,'reviewHistoryExport').mockResolvedValue({blob:new Blob(['csv']),filename:'review-history.csv'});
 vi.spyOn(URL,'createObjectURL').mockReturnValue('blob:fixture');vi.spyOn(URL,'revokeObjectURL').mockImplementation(()=>undefined);vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(()=>undefined);
 render(<MemoryRouter initialEntries={['/settings/review-history?category=too_expensive&page=2']}><ReviewHistorySettings/></MemoryRouter>);
 expect(await screen.findByText('Export 30 decisions · filters: category = too expensive')).toBeVisible();expect(screen.getByText('Engineering judgement')).toBeVisible();
 fireEvent.click(screen.getByRole('button',{name:'Export CSV'}));await waitFor(()=>expect(exported).toHaveBeenCalledExactlyOnceWith('category=too_expensive','csv'));
 exported.mockRejectedValueOnce(new ApiError(503,'unavailable','Could not export review history.'));fireEvent.click(screen.getByRole('button',{name:'Export JSON'}));expect(await screen.findByRole('alert')).toHaveTextContent('Could not export review history.');expect(screen.getByRole('button',{name:'Export JSON'})).toBeEnabled();
 fireEvent.change(screen.getByLabelText('Decision'),{target:{value:'reject'}});await waitFor(()=>expect(request).toHaveBeenLastCalledWith('/api/reviews/history?category=too_expensive&decision=reject','GET',undefined,expect.any(AbortSignal)));
});
it('FR-UI-07 history loading, failure retry, empty state and historical category null',async()=>{
 const request=vi.spyOn(api,'request').mockRejectedValueOnce(new ApiError(500,'internal_error','Could not load history.')).mockResolvedValueOnce({...data,total:0,items:[],filters:{}}).mockResolvedValueOnce({...data,items:[{...data.items[0],category:null}],filters:{}});
 render(<MemoryRouter><ReviewHistorySettings/></MemoryRouter>);expect(screen.getByRole('status')).toHaveTextContent('Loading review history');expect(await screen.findByRole('alert')).toHaveTextContent('Could not load history.');fireEvent.click(screen.getByRole('button',{name:'Retry'}));expect(await screen.findByText('No recorded decisions match these filters.')).toBeVisible();expect(screen.getByText('Export 0 decisions · filters: none (all decisions)')).toBeVisible();fireEvent.change(screen.getByLabelText('Category'),{target:{value:'not_recorded'}});expect(await screen.findByRole('cell',{name:'not recorded'})).toBeVisible();expect(request).toHaveBeenCalledTimes(3);
});
it('NFR-01 reviewer cannot see or load the admin history tab',()=>{
 setSessionStatus({authenticated:true,auth_required:true,mode:'account',user:{id:'u',username:'Reviewer',role:'reviewer'}});
 const request=vi.spyOn(api,'request');render(<MemoryRouter><SettingsScreen/></MemoryRouter>);expect(screen.queryByRole('link',{name:'Review history'})).toBeNull();expect(request).not.toHaveBeenCalled();
});
