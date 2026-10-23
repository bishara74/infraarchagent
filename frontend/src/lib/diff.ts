import { diffArrays,structuredPatch } from 'diff';
export interface DiffRow { kind:'context'|'add'|'remove'|'hunk'|'formatting'; content:string; oldLine:number|null; newLine:number|null }
export function unifiedDiff(original:string|undefined,current:string):{rows:DiffRow[];baseline:boolean;changed:boolean} {
 if(original===undefined || original===current) return {baseline:original!==undefined,changed:false,rows:current.replace(/\n$/,'').split('\n').map((content,index)=>({kind:'context',content,oldLine:original===undefined?null:index+1,newLine:index+1}))};
 const patch=structuredPatch('original','current',original,current,'','',{context:3}); const rows:DiffRow[]=[];
 for(const hunk of patch.hunks){let oldLine=hunk.oldStart;let newLine=hunk.newStart; rows.push({kind:'hunk',content:`@@ -${hunk.oldStart},${hunk.oldLines} +${hunk.newStart},${hunk.newLines} @@`,oldLine:null,newLine:null});
 for(const line of hunk.lines){const marker=line[0]; if(marker==='\\') {rows.push({kind:'hunk',content:line,oldLine:null,newLine:null});continue;} const kind=marker==='+'?'add':marker==='-'?'remove':'context'; rows.push({kind,content:line.slice(1),oldLine:kind==='add'?null:oldLine++,newLine:kind==='remove'?null:newLine++});}}
 return {rows,baseline:true,changed:true};
}

/** Presentation only: source strings and the retained raw diff are never rewritten. */
export function presentedDiff(original:string|undefined,current:string,hideWhitespace:boolean) {
 const raw=unifiedDiff(original,current);
 if(!hideWhitespace||original===undefined||original===current)return {...raw,changedLines:raw.rows.filter(row=>row.kind==='add'||row.kind==='remove').length,formattingHidden:0};
 const lines=(value:string)=>value===''?[]:value.replace(/\n$/,'').split('\n').map(content=>({content,key:content.replace(/\s/g,'')}));
 const before=lines(original),after=lines(current);
 const aligned:Array<DiffRow&{formatting?:boolean}>=[];
 let oldLine=1,newLine=1;
 for(const part of diffArrays(before,after,{comparator:(a,b)=>a.key===b.key})) {
  for(const line of part.value) {
   if(part.added||part.removed) {
    const formatting=line.key==='';
    aligned.push({kind:formatting?'context':part.added?'add':'remove',content:line.content,oldLine:part.added?null:oldLine++,newLine:part.removed?null:newLine++,formatting});
   } else {
    const previous=before[oldLine-1]!;
    aligned.push({kind:'context',content:line.content,oldLine:oldLine++,newLine:newLine++,formatting:previous.content!==line.content});
   }
  }
 }
 if(original.endsWith('\n')!==current.endsWith('\n')) {
  const last=aligned.at(-1);
  if(last?.kind==='context')last.formatting=true;
 }
 const ranges:Array<{start:number;end:number}>=[];
 aligned.forEach((row,index)=>{
  if(row.kind==='context'&&!row.formatting)return;
  const start=Math.max(0,index-3),end=Math.min(aligned.length,index+4),previous=ranges.at(-1);
  if(previous&&start<=previous.end)previous.end=end;else ranges.push({start,end});
 });
 const rows:DiffRow[]=[];
 for(const {start,end} of ranges) {
  const hunk=aligned.slice(start,end),formattingOnly=hunk.every(row=>row.kind==='context');
  const old=hunk.filter(row=>row.oldLine!==null),next=hunk.filter(row=>row.newLine!==null);
  rows.push({kind:formattingOnly?'formatting':'hunk',content:formattingOnly?'Formatting only (terraform fmt)':`@@ -${old[0]?.oldLine??0},${old.length} +${next[0]?.newLine??0},${next.length} @@`,oldLine:null,newLine:null},...hunk);
 }
 return {...raw,rows,changedLines:aligned.filter(row=>row.kind==='add'||row.kind==='remove').length,formattingHidden:aligned.filter(row=>row.formatting).length};
}
