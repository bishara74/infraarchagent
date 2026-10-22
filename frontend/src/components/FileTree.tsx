import { Icon } from './Icon';
import { Link } from 'react-router';
import type { PackageResult } from '../api/types';
import { fileTree } from '../lib/fileTree';
import { WindowedRows } from './WindowedRows';

export function FileTree({ item, runId, selected }: {
  item: PackageResult; runId: string; selected?: string;
}) {
  const rows = fileTree(Object.keys(item.files));
  if (!rows.length) return <p className="muted">No files available.</p>;
  return <WindowedRows count={rows.length} label={`${item.variant} package files`} className="file-tree" row={index => {
    const row = rows[index]!;
    if (row.directory) return <div className="file-row muted" key={`directory:${row.path}`} style={{ paddingLeft: `calc(${row.depth} * var(--space-3) + var(--space-2))` }}><Icon name="folder"/> {row.label}</div>;
    const changed = item.original_files !== null && item.original_files[row.path] !== item.files[row.path];
    return <div className="file-row" key={row.path} style={{ paddingLeft: `calc(${row.depth} * var(--space-3))` }}>
      <Link aria-current={selected === row.path ? 'page' : undefined} aria-label={`${row.path}${changed ? ' changed' : ''}`} to={`/runs/${runId}/packages/${item.variant}?file=${encodeURIComponent(row.path)}`} title={row.path}>
        <Icon name="file"/> {row.label}{changed && <span className="changed"> changed</span>}
      </Link>
    </div>;
  }} />;
}
