import {expect,test} from '@playwright/test';
import {mkdir} from 'node:fs/promises';
import {USERNAME,PASSWORD} from './support/flow';

test('FR-UI-01 NFR-01 login landing, one-use deep link and logout reset',async({page})=>{
 await page.setViewportSize({width:1280,height:800});
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 const login=async()=>{await page.getByLabel('Username',{exact:true}).fill(USERNAME);await page.getByLabel('Password',{exact:true}).fill(PASSWORD);await page.getByRole('button',{name:'Log in',exact:true}).click();};
 const logout=async()=>{await page.getByRole('button',{name:USERNAME,exact:true}).click();await page.getByRole('menuitem',{name:'Log out'}).click();await expect(page).toHaveURL(/\/login$/);};
 await page.goto('/');await login();await expect(page).toHaveURL(/\/$/);
 await page.goto('/settings/account');await logout();await login();await expect(page).toHaveURL(/\/$/);
 await logout();await page.goto('/settings/account?from=deep#account');await expect(page).toHaveURL(/\/login$/);await login();await expect(page).toHaveURL(/\/settings\/account\?from=deep#account$/);
 await mkdir('../docs/evals/phase9j-ui/round3',{recursive:true});await page.screenshot({path:'../docs/evals/phase9j-ui/round3/login-deep-link.png'});
 await logout();await page.screenshot({path:'../docs/evals/phase9j-ui/round3/login.png'});await login();await expect(page).toHaveURL(/\/$/);await expect(page.getByLabel('Infrastructure description')).toHaveValue('');
 expect(errors).toEqual([]);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
