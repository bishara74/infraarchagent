import { useEffect, useState, type ReactNode } from 'react';
import { stageElapsed, type StageItem } from '../lib/runReducer';
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
  const icon = stage.status === 'completed' ? 'M7 12l3 3 7-7'
    : stage.status === 'failed' ? 'M8 8l8 8M16 8l-8 8'
    : stage.status === 'running' ? 'M6 12a6 6 0 0 1 12 0' : 'M12 7v5l3 2';
  return (
    <section className="panel stage">
      <svg className={`stage-icon state-${stage.status}`} aria-hidden="true" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" />
        <path d={icon} fill="none" stroke="currentColor" strokeWidth="1.5" />
      </svg>
      <div className="stage-heading">
        <h2>{name}</h2>
        <StatusBadge status={stage.status} seq={stage.seq} testId={`stage-${id}`} />
        <time className="elapsed muted">{stageElapsed(stage, now)}</time>
      </div>
      <p className="muted stage-message" title={stage.message ?? undefined}>{stage.message ?? 'Waiting to start'}</p>
      {children && <div className="stage-variants">{children}</div>}
    </section>
  );
}
