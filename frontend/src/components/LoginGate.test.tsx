import {render,screen} from '@testing-library/react';
import {MemoryRouter,Route,Routes,useLocation} from 'react-router';
import {expect,it} from 'vitest';
import {LoginGate} from './LoginGate';

function Destination(){const location=useLocation();return <p>{location.pathname+location.search+location.hash} · {JSON.stringify(location.state)}</p>;}
it.each(['/', '/login'])('FR-UI-01 normal login at %s lands on New request',path=>{
 render(<MemoryRouter initialEntries={[path]}><Routes><Route path="/login" element={<LoginGate authenticated/>}/><Route path="/" element={<Destination/>}/></Routes></MemoryRouter>);
 expect(screen.getByText('/ · null')).toBeVisible();
});
it('FR-UI-01 consumes the deep link with query and fragment',()=>{
 render(<MemoryRouter initialEntries={[{pathname:'/login',state:{returnTo:'/runs/fixture/packages/cost?tab=review#reason'}}]}><Routes><Route path="/login" element={<LoginGate authenticated/>}/><Route path="*" element={<Destination/>}/></Routes></MemoryRouter>);
 expect(screen.getByText('/runs/fixture/packages/cost?tab=review#reason · null')).toBeVisible();
});
it.each(['https://outside.invalid','//outside.invalid','/login','/unknown'])('NFR-01 ignores invalid return target %s',returnTo=>{
 render(<MemoryRouter initialEntries={[{pathname:'/login',state:{returnTo}}]}><Routes><Route path="/login" element={<LoginGate authenticated/>}/><Route path="/" element={<Destination/>}/></Routes></MemoryRouter>);
 expect(screen.getByText('/ · null')).toBeVisible();
});
