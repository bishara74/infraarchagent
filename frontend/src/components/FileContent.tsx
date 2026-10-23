import {WindowedRows} from './WindowedRows';
export function FileContent({path,content}:{path:string;content:string}) {
 const lines=content.replace(/\n$/,'').split('\n');
 return <section className="panel diff"><h2 className="mono">{path}</h2><p className="muted">Current package content</p><WindowedRows count={lines.length} label="Current file content" row={index=><div className="diff-row context" key={index}><span className="line-number">{index+1}</span><span>{lines[index]}</span></div>}/></section>;
}
