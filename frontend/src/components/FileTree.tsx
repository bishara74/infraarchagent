import { Link } from 'react-router';
import type { PackageResult } from '../api/types';
import { WindowedRows } from './WindowedRows';
export function FileTree({item,runId,selected}:{item:PackageResult;runId:string;selected?:string}){
 const paths=Object.keys(item.files).sort();if(!paths.length)return <p className="muted">No files available.</p>;
 return <WindowedRows count={paths.length} label={`${item.variant} package files`} className="file-tree" row={index=>{const path=paths[index]!;const changed=item.original_files!==null&&item.original_files[path]!==item.files[path];return <div className="file-row" key={path}><Link aria-current={selected===path?'page':undefined} to={`/runs/${runId}/packages/${item.variant}?file=${encodeURIComponent(path)}`} title={path}>{path}{changed&&<span className="changed"> changed</span>}</Link></div>;}}/>;
}
