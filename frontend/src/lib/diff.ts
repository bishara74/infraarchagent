import { structuredPatch } from 'diff';
export interface DiffRow { kind:'context'|'add'|'remove'|'hunk'; content:string; oldLine:number|null; newLine:number|null }
export function unifiedDiff(original:string|undefined,current:string):{rows:DiffRow[];baseline:boolean;changed:boolean} {
 if(original===undefined || original===current) return {baseline:original!==undefined,changed:false,rows:current.replace(/\n$/,'').split('\n').map((content,index)=>({kind:'context',content,oldLine:original===undefined?null:index+1,newLine:index+1}))};
 const patch=structuredPatch('original','current',original,current,'','',{context:3}); const rows:DiffRow[]=[];
 for(const hunk of patch.hunks){let oldLine=hunk.oldStart;let newLine=hunk.newStart; rows.push({kind:'hunk',content:`@@ -${hunk.oldStart},${hunk.oldLines} +${hunk.newStart},${hunk.newLines} @@`,oldLine:null,newLine:null});
 for(const line of hunk.lines){const marker=line[0]; if(marker==='\\') continue; const kind=marker==='+'?'add':marker==='-'?'remove':'context'; rows.push({kind,content:line.slice(1),oldLine:kind==='add'?null:oldLine++,newLine:kind==='remove'?null:newLine++});}}
 return {rows,baseline:true,changed:true};
}
