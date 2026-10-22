import { useEffect, useState, type ReactNode } from 'react';
import { stageElapsed, type StageItem } from '../lib/runReducer';
import { Icon } from './Icon';
import { StatusBadge } from './StatusBadge';

export function StageCard({ name, stage, id, children }: {
  name: string; stage: StageItem; id: string; children?: ReactNode;
}) {
  const [now, setNow] = useState(Date.now);
  useEffect(() => {
    if (stage.status !== 'running') return;
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, [stage.status]);
  return (
    <section className="panel stage">
      <span className={`stage-icon state-${stage.status}`}><Icon name={stage.status==='completed'?'check':stage.status==='failed'?'close':stage.status==='running'?'loading':'watch'} spin={stage.status==='running'}/></span>
      <div className="stage-heading">
        <h2>{name}</h2>
        <StatusBadge status={stage.status} seq={stage.seq} testId={`stage-${id}`} />
        <time className="elapsed muted">{stageElapsed(stage, now)}</time>
      </div>
      <p className="muted stage-message" title={stage.message ?? undefined}>{stage.message ?? 'Waiting to start'}</p>
      {children && <details className="stage-variants" open><summary>Generator variants</summary><div className="generator-variants">{children}</div></details>}
    </section>
  );
}
