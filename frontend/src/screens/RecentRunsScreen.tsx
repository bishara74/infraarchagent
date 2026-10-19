import { useEffect } from 'react';
import { Link } from 'react-router';
import { getSessionStatus } from '../lib/sessionState';
import { hydratePreferences, usePreferences } from '../lib/preferences';
export function RecentRunsScreen() { const prefs = usePreferences(); useEffect(() => { void hydratePreferences(getSessionStatus()?.user?.id ?? null); }, []); return <><h1>Recent runs</h1><p>Runs submitted or opened by this account. The workspace is shared; a run link can be opened by another reviewer.</p>{!prefs.ready ? <p role="status">Loading recent runs…</p> : prefs.recent.length ? <ul className="recent-runs">{prefs.recent.map(run => <li key={run.id}><Link to={`/runs/${run.id}`}>{run.title}</Link><span>{run.status} · {new Date(run.time).toLocaleString()}</span></li>)}</ul> : <p>No recent runs. <Link to="/">Create a new request</Link>.</p>}</>; }
