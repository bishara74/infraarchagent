import {expect,it,vi} from 'vitest';
import {mkdir,writeFile} from 'node:fs/promises';
import {latencyEvidence,writePerfEvidence,type LatencySample} from '../../e2e/support/perfEvidence';
vi.mock('node:fs/promises',async importOriginal=>{const actual=await importOriginal<typeof import('node:fs/promises')>();const mkdir=vi.fn().mockResolvedValue(undefined);const writeFile=vi.fn().mockResolvedValue(undefined);return {...actual,mkdir,writeFile,default:{...actual,mkdir,writeFile}};});
const sample=(latency_ms:number):LatencySample=>({seq:1,badge:'stage-architect',at:latency_ms,server_timestamp:'2026-01-01T00:00:00Z',latency_ms});
it('PR-02 preserves raw samples and even/odd medians',()=>{
 expect(latencyEvidence([sample(30),sample(10)])).toMatchObject({sample_count:2,min_ms:10,max_ms:30,median_ms:20});
 expect(latencyEvidence([sample(30),sample(10),sample(20)]).median_ms).toBe(20);
 expect(latencyEvidence([])).toMatchObject({sample_count:0,max_ms:null,median_ms:null});
});
it('PR-02 writes phase9 evidence before a failing latency assertion',async()=>{
 const result=await writePerfEvidence([sample(1001)],'/tmp/phase9-fixture');
 expect(mkdir).toHaveBeenCalledWith('/tmp/phase9-fixture',{recursive:true});
 expect(writeFile).toHaveBeenCalledWith('/tmp/phase9-fixture/pr02.json',JSON.stringify(result,null,2));
 expect(result.max_ms).toBe(1001);
});
