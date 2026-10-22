import { Link } from 'react-router';
import { errorMessage } from '../api/client';
import { retryHydration, usePreferences } from '../lib/preferences';
export function RecentRunsScreen() {
    const prefs = usePreferences();
    return <><h1>Recent runs</h1><p>Runs submitted or opened by this account. The workspace is shared; a run link can be opened by another reviewer.</p>
        {prefs.loadError ? <div className="notice" role="alert"><p>Unable to load recent runs. {errorMessage(prefs.loadError)}</p><button onClick={() => void retryHydration()}>Retry</button>{prefs.recent.length > 0 && <p>Showing cached runs.</p>}</div> : null}
        {!prefs.ready ? <p role="status">Loading recent runs…</p> : prefs.recent.length ? <ul className="recent-runs">{prefs.recent.map(run => <li key={run.id}><Link to={`/runs/${run.id}`}>{run.title}</Link><span>{run.status} · {new Date(run.time).toLocaleString()}</span></li>)}</ul> : !prefs.loadError && <section className="panel"><p>No runs yet — start one from New request</p><Link className="button primary" to="/">New request</Link></section>}
    </>;
}
