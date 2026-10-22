import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {expect,it,vi} from 'vitest';
import {api,ApiError} from '../api/client';
import {DownloadButton} from './DownloadButton';
it('FR-UI-06 downloads show safe errors and permit retry',async()=>{
 const download=vi.spyOn(api,'download').mockRejectedValue(new ApiError(409,'not_downloadable','Review the package first.'));
 render(<DownloadButton runId="run" variant="cost"/>);await userEvent.click(screen.getByRole('button',{name:'Download ZIP'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('Review the package first.');expect(download).toHaveBeenCalledWith('run','cost');expect(screen.getByRole('button',{name:'Download ZIP'})).toBeEnabled();
});
