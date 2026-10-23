import type { PackageResult } from '../api/types';
import {useMemo} from 'react';
import { presentedDiff } from '../lib/diff';
import {usePreferences,updatePreferences} from '../lib/preferences';
import { fileRules } from '../lib/reportView';
import { WindowedRows } from './WindowedRows';
export function DiffView({item,path}:{item:PackageResult;path:string}){
 const prefs=usePreferences();const hide=prefs.data.ui.hide_whitespace_only_changes;
 const original=item.original_files?.[path],current=item.files[path]??'';
 const diff=useMemo(()=>presentedDiff(original,current,hide),[original,current,hide]);const rules=fileRules(item,path);
 return <section className="panel diff"><h2 className="mono">{path}</h2><p className="muted">{!diff.baseline?'Original files unavailable; showing current content.':diff.changed?'Changes from the generated original':'No changes from the generated original'}{rules.length>0&&` · Linked rules: ${rules.join(', ')}`}</p><label className="checkbox diff-toggle"><input type="checkbox" checked={hide} onChange={event=>updatePreferences({ui:{...prefs.data.ui,hide_whitespace_only_changes:event.target.checked}})}/>Hide whitespace-only changes</label><p className="muted diff-count" role="status">{diff.changedLines} changed lines · {diff.formattingHidden} formatting-only lines hidden</p><WindowedRows count={diff.rows.length} label="Unified file diff" row={index=>{const row=diff.rows[index]!;return <div key={index} className={`diff-row ${row.kind}`}><span className="line-number">{row.oldLine??''}</span><span className="line-number">{row.newLine??''}</span><span className="marker">{row.kind==='add'?'+':row.kind==='remove'?'-':' '}</span><span className="diff-content">{row.content}</span></div>;}}/></section>;
}
