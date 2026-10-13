import {mkdir,writeFile} from 'node:fs/promises';
import path from 'node:path';
export interface LatencySample {seq:number;badge:string;at:number;server_timestamp:string;latency_ms:number}
export function latencyEvidence(samples:LatencySample[]) {
 const sorted=samples.map(sample=>sample.latency_ms).sort((a,b)=>a-b);
 return {sample_count:samples.length,min_ms:sorted[0]??null,max_ms:sorted.at(-1)??null,
  median_ms:sorted.length?(sorted.length%2?sorted[Math.floor(sorted.length/2)]!:((sorted[sorted.length/2-1]!+sorted[sorted.length/2]!)/2)):null,
  measurement:'Stub live-event evidence; initial run only, historical reload replay excluded.',samples};
}
export async function writePerfEvidence(samples:LatencySample[],directory='test-results') {
 const evidence=latencyEvidence(samples);await mkdir(directory,{recursive:true});
 await writeFile(path.join(directory,'pr02.json'),JSON.stringify(evidence,null,2));return evidence;
}
