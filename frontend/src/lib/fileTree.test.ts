import { expect, it } from 'vitest';
import { fileTree } from './fileTree';
it('FR-UI-03 derives directory hierarchy without duplicated or invented folders', () => {
  const rows=fileTree(['terraform/variables.tf','helm/web/values.yaml','terraform/main.tf','Jenkinsfile']);
  expect(rows.filter(row=>row.directory).map(row=>row.path)).toEqual(['helm','helm/web','terraform']);
  expect(rows.find(row=>row.path==='helm/web/values.yaml')).toEqual({path:'helm/web/values.yaml',label:'values.yaml',depth:2,directory:false});
  expect(rows.filter(row=>!row.directory).map(row=>row.path)).toEqual(['Jenkinsfile','helm/web/values.yaml','terraform/main.tf','terraform/variables.tf']);
});
it('empty files produce an empty tree',()=>expect(fileTree([])).toEqual([]));
