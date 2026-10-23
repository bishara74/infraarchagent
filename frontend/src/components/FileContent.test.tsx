import {render,screen} from '@testing-library/react';
import {expect,it} from 'vitest';
import {FileContent} from './FileContent';
it('FR-UI-03 NFR-01 current file content is escaped with real line numbers',()=>{
 render(<FileContent path="main.tf" content={'<script>untrusted()</script>\nsecond line\n'}/>);
 expect(screen.getByRole('heading',{name:'main.tf'})).toBeVisible();expect(screen.getByText('<script>untrusted()</script>')).toBeVisible();expect(document.querySelector('script')).toBeNull();expect(document.querySelectorAll('.line-number')[1]).toHaveTextContent('2');
});
