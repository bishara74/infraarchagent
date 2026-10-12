import {expect,it} from 'vitest';
import {render,screen,fireEvent} from '@testing-library/react';
import {WindowedRows} from './WindowedRows';
it('large lists render a bounded window and scrolling reveals later rows',()=>{render(<WindowedRows count={200} label="Recorded rows" row={index=><div key={index} data-testid="row">Row {index}</div>}/>);expect(screen.getAllByTestId('row')).toHaveLength(45);const region=screen.getByRole('region',{name:'Recorded rows'});fireEvent.scroll(region,{target:{scrollTop:2400}});expect(screen.getAllByTestId('row')).toHaveLength(45);expect(screen.getByText('Row 100')).toBeVisible();expect(screen.queryByText('Row 0')).toBeNull();});
