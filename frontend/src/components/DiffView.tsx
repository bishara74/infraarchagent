import type { PackageResult } from '../api/types';
import { unifiedDiff } from '../lib/diff';
import { fileRules } from '../lib/reportView';
import { WindowedRows } from './WindowedRows';
export function DiffView({item,path}:{item:PackageResult;path:string}){
 const diff=unifiedDiff(item.original_files?.[path],item.files[path]??'');const rules=fileRules(item,path);
 return <section className="panel diff"><h2 className="mono">{path}</h2><p className="muted">{!diff.baseline?'Original files unavailable; showing current content.':diff.changed?'Changes from the generated original':'No changes from the generated original'}{rules.length>0&&` · Linked rules: ${rules.join(', ')}`}</p><WindowedRows count={diff.rows.length} label="Unified file diff" row={index=>{const row=diff.rows[index]!;return <div key={index} className={`diff-row ${row.kind}`}><span className="line-number">{row.oldLine??''}</span><span className="line-number">{row.newLine??''}</span><span className="marker">{row.kind==='add'?'+':row.kind==='remove'?'-':' '}</span><span>{row.content}</span></div>;}}/></section>;
}
