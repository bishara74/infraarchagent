import {expect,type Page} from '@playwright/test';
import {mkdir} from 'node:fs/promises';
import path from 'node:path';
export async function captureUi(page:Page,name:string,viewport={width:1280,height:800}) {
 await page.setViewportSize(viewport);
 await page.evaluate(async()=>{await document.fonts.ready;});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'No horizontal page overflow at 1280×800').toBe(true);
 const directory=path.resolve('..','docs','evals','phase9j-ui','round2',...(viewport.width===1280?[]:['1920']));await mkdir(directory,{recursive:true});
 await page.screenshot({path:path.join(directory,`${name}.png`),fullPage:false,animations:'disabled'});
}
