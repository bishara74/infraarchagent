import {expect,test} from '@playwright/test';
import {mkdir,writeFile} from 'node:fs/promises';
import {createSseParser,eventFromFrame} from '../src/api/sse';
import type {RunEvent} from '../src/api/types';
import {submit} from './support/flow';
interface Observation {seq:number;badge:string;at:number}
test('PR-02 @perf live server event → badge mutation ≤1000ms',async({page})=>{
 const events=new Map<number,RunEvent>();const captures:Promise<void>[]=[];
 page.on('response',response=>{if(response.url().endsWith('/stream'))captures.push((async()=>{const raw=await response.text();createSseParser(frame=>{const event=eventFromFrame(frame);events.set(event.seq,event);}).feed(raw);})());});
 await page.addInitScript(()=>{
  const observed:Observation[]=[];(window as unknown as {phase8Observations:Observation[]}).phase8Observations=observed;
  const observer=new MutationObserver(mutations=>{mutations.forEach((mutation,index)=>{
   if(mutation.type==='attributes'&&mutation.target instanceof Element){const node=mutation.target;const badge=node.getAttribute('data-testid');if(!badge?.startsWith('stage-'))return;
   const later=mutations.slice(index+1).find(item=>item.target===node&&item.attributeName==='data-seq');const value=later?later.oldValue:node.getAttribute('data-seq');const seq=Number(value);if(seq>0)observed.push({seq,badge,at:Date.now()});}
  });});observer.observe(document,{subtree:true,attributes:true,attributeOldValue:true,attributeFilter:['data-seq']});
 });
 const before=Date.now();await submit(page);await expect(page.getByRole('link',{name:'View results'})).toBeVisible();await expect(page.getByTestId('stream-state')).toHaveAttribute('data-state','closed');await Promise.all(captures);
 const observations=await page.evaluate(()=>(window as unknown as {phase8Observations:Observation[]}).phase8Observations);
 const samples=observations.flatMap(observation=>{const event=events.get(observation.seq);if(!event||Date.parse(event.timestamp)<before)return[];return[{...observation,server_timestamp:event.timestamp,latency_ms:observation.at-Date.parse(event.timestamp)}];});
 for(const badge of ['stage-architect','stage-generators','stage-security','stage-validator'])expect(new Set(samples.filter(sample=>sample.badge===badge).map(sample=>sample.seq)).size,`Live transitions missing for ${badge}`).toBeGreaterThanOrEqual(2);
 const sorted=samples.map(sample=>sample.latency_ms).sort((a,b)=>a-b);expect(sorted.length).toBeGreaterThan(0);const max=sorted.at(-1)!;const median=sorted.length%2?sorted[Math.floor(sorted.length/2)]!:((sorted[sorted.length/2-1]!+sorted[sorted.length/2]!)/2);
 await mkdir('test-results',{recursive:true});await writeFile('test-results/pr02.json',JSON.stringify({sample_count:samples.length,max_ms:max,median_ms:median,measurement:'Development evidence; initial live run only, no historical reload replay.',samples},null,2));expect(sorted[0]).toBeGreaterThanOrEqual(0);expect(max).toBeLessThanOrEqual(1000);
});
