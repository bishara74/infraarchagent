export interface FileTreeRow { path: string; label: string; depth: number; directory: boolean }
/** Directory labels come only from prefixes of returned file paths. */
export function fileTree(paths: string[]): FileTreeRow[] {
  const rows: FileTreeRow[] = [];
  const directories = new Set<string>();
  for (const path of [...paths].sort()) {
    const parts = path.split('/');
    for (let depth = 0; depth < parts.length - 1; depth++) {
      const prefix = parts.slice(0, depth + 1).join('/');
      if (!directories.has(prefix)) {
        directories.add(prefix);
        rows.push({ path: prefix, label: `${parts[depth]}/`, depth, directory: true });
      }
    }
    rows.push({ path, label: parts.at(-1)!, depth: parts.length - 1, directory: false });
  }
  return rows;
}
