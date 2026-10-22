import {fireEvent,render,screen,waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {expect,it,vi} from 'vitest';
import {MemoryRouter} from 'react-router';
import {Authentication} from './Authentication';
import {AccountMenu} from './AccountMenu';
import {api,ApiError} from '../api/client';
it('NFR-01 login has password visibility Caps Lock and safe generic failures',async()=>{
 vi.spyOn(api,'login').mockRejectedValue(new ApiError(401,'unauthorized','internal must not display'));
 render(<Authentication onSaved={vi.fn()}/>);
 const password=screen.getByLabelText('Password',{exact:true});
 fireEvent.keyDown(password,{key:'A',modifierCapsLock:true});
 expect(screen.getByText('Caps Lock is on.')).toBeVisible();
 await userEvent.click(screen.getByRole('button',{name:'Show password'}));expect(password).toHaveAttribute('type','text');
 fireEvent.change(screen.getByLabelText('Username'),{target:{value:'reviewer'}});fireEvent.change(password,{target:{value:'synthetic-password'}});
 fireEvent.submit(password.closest('form')!);
 expect(await screen.findByText('Username or password is incorrect')).toBeVisible();expect(screen.queryByText('internal must not display')).toBeNull();
 expect(password).toHaveValue('');expect(screen.getByText(/Forgot your password/)).toBeVisible();
});
it('NFR-01 first administrator requires matching passwords',()=>{
 const login=vi.spyOn(api,'login');render(<Authentication setup onSaved={vi.fn()}/>);
 fireEvent.change(screen.getByLabelText('Password',{exact:true}),{target:{value:'synthetic-password'}});
 fireEvent.submit(screen.getByLabelText('Password',{exact:true}).closest('form')!);
 expect(screen.getByText('Passwords must match.')).toBeVisible();expect(login).not.toHaveBeenCalled();
});
it('NFR-01 account menu supports keyboard dismissal outside click and logout',async()=>{
 const logout=vi.spyOn(api,'logout').mockResolvedValue(undefined);
 render(<MemoryRouter><AccountMenu username="reviewer"/><button>Outside</button></MemoryRouter>);
 const trigger=screen.getByRole('button',{name:'reviewer'});
 fireEvent.keyDown(trigger,{key:'ArrowDown'});expect(screen.getByRole('menuitem',{name:'Account'})).toHaveFocus();
 fireEvent.keyDown(document.activeElement!,{key:'ArrowDown'});expect(screen.getByRole('menuitem',{name:'Log out'})).toHaveFocus();
 fireEvent.keyDown(document.activeElement!,{key:'Escape'});expect(trigger).toHaveFocus();expect(screen.queryByRole('menu')).toBeNull();
 await userEvent.click(trigger);fireEvent.pointerDown(screen.getByRole('button',{name:'Outside'}));expect(screen.queryByRole('menu')).toBeNull();
 await userEvent.click(trigger);await userEvent.click(screen.getByRole('menuitem',{name:'Log out'}));await waitFor(()=>expect(logout).toHaveBeenCalledOnce());
});
