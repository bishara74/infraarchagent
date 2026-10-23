import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import {expect,it,vi} from 'vitest';
import {api,ApiError} from '../api/client';
import {DownloadAllButton} from './DownloadAllButton';
it('FR-UI-06 bundle downloads require all variants and expose safe retry errors',async()=>{
 const request=vi.spyOn(api,'downloadAll').mockRejectedValue(new ApiError(409,'not_downloadable','Resolve each review first.'));
 const root=render(<DownloadAllButton runId="run" available={false}/>);expect(screen.getByRole('button')).toBeDisabled();expect(screen.getByText(/All three variants need readiness labels/)).toBeVisible();
 root.rerender(<DownloadAllButton runId="run" available/>);fireEvent.click(screen.getByRole('button'));expect(await screen.findByRole('alert')).toHaveTextContent('Resolve each review first.');await waitFor(()=>expect(screen.getByRole('button')).toBeEnabled());expect(request).toHaveBeenCalledExactlyOnceWith('run');
});
