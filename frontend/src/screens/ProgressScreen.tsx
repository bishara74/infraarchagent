// AI assistance: written with OpenAI Codex from the author's task
// descriptions; reviewed and modified by the author. See AI_USE.md.
import { ActionButton } from "../components/ActionGate";
import { useRef, useState, useSyncExternalStore } from "react";
import { Link, useParams } from "react-router";
import { api, ApiError, errorMessage } from "../api/client";
import { useRunStream } from "../hooks/useRunStream";
import { stageFor, blankStage } from "../lib/runReducer";
import { StageCard } from "../components/StageCard";
import { StatusBadge } from "../components/StatusBadge";
import { LiveLog } from "../components/LiveLog";
import { PageState } from "../components/PageState";
import { RunNotice } from "../components/RunNotice";
import { isTerminalRun, variants } from "../api/types";
import { LessonUsage } from "../components/LessonUsage";
import { getSessionStatus, subscribeSession } from "../lib/sessionState";
export function ProgressScreen() {
  const { runId = "" } = useParams();
  const stream = useRunStream(runId);
  const terminal = isTerminalRun(stream.model.runStatus);
  if (stream.error) return <PageState error={stream.error} onRetry={stream.reconnect} />;
  if (!stream.results && !stream.events.length)
    return <PageState loading onRetry={stream.reconnect} />;
  return (
    <>
      <p className="muted run-meta" title={stream.results?.run.input_text}>
        Run <code>{runId}</code> · {stream.results?.run.input_text}
      </p>
      <div className="page-heading">
        <h1>Pipeline progress</h1>
        <StatusBadge status={stream.model.runStatus} />
        {terminal ? (
          <Link className="button primary" to={`/runs/${runId}/compare`}>
            View results
          </Link>
        ) : (
          <>
            <CancelRunButton key={runId} runId={runId} reconnect={stream.reconnect} />
            <ActionButton
              disabled
              unavailableReason="The run is still processing."
              nextStep="Watch progress; results become available when the run settles."
            >
              View results
            </ActionButton>
          </>
        )}
      </div>
      <RunNotice state={stream.state} onReconnect={stream.reconnect} />
      <LessonUsage manifest={stream.results?.run.lessons} events={stream.events} />
      {stream.results?.run.error_message && <p role="alert">{stream.results.run.error_message}</p>}
      <div className="stages">
        <StageCard
          name="ArchitectAgent"
          id="architect"
          stage={stageFor(stream.model, "architect")}
        />
        <StageCard
          name="GeneratorAgents"
          id="generators"
          stage={stageFor(stream.model, "generators")}
        >
          {variants.map((variant) => {
            const stage = stream.model.stages[`generator_${variant}:${variant}`] ?? blankStage();
            return (
              <div className="generator-row" key={variant}>
                <span className="capitalize">{variant} variant</span>
                <StatusBadge
                  status={stage.status}
                  seq={stage.seq}
                  testId={`stage-generator-${variant}`}
                />
              </div>
            );
          })}
        </StageCard>
        <StageCard name="SecurityAgent" id="security" stage={stageFor(stream.model, "security")} />
        <StageCard
          name="ValidatorAgent"
          id="validator"
          stage={stageFor(stream.model, "validator")}
        />
      </div>
      <LiveLog events={stream.events} live={!terminal && stream.state !== "closed"} />
    </>
  );
}

function CancelRunButton({ runId, reconnect }: { runId: string; reconnect: () => void }) {
  const session = useSyncExternalStore(subscribeSession, getSessionStatus);
  const requiresName = !session?.user;
  const dialog = useRef<HTMLDialogElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const [reviewerName, setReviewerName] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<unknown>(null);

  async function cancel() {
    setError(null);
    setPending(true);
    try {
      await api.cancelRun(runId, requiresName ? reviewerName.trim() : undefined);
    } catch (cause) {
      setPending(false);
      setError(cause);
      if (cause instanceof ApiError && cause.code === "not_cancellable") reconnect();
    }
  }

  return (
    <>
      <ActionButton
        ref={trigger}
        type="button"
        disabled={pending}
        unavailableReason="Cancellation is in progress."
        nextStep="Wait for the run to settle."
        onClick={() => dialog.current?.showModal()}
      >
        Cancel run
      </ActionButton>
      {pending && <span role="status">Stopping run…</span>}
      {error ? <span role="alert">{errorMessage(error)}</span> : null}
      <dialog
        ref={dialog}
        aria-labelledby="cancel-run-title"
        aria-describedby="cancel-run-description"
        onClose={() => trigger.current?.focus()}
      >
        <h2 id="cancel-run-title">Stop this run?</h2>
        <p id="cancel-run-description">
          Packages without a label are discarded; finished packages are kept.
        </p>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            if (pending || (requiresName && !reviewerName.trim())) return;
            dialog.current?.close();
            void cancel();
          }}
        >
          {requiresName && (
            <label>
              Reviewer name
              <input
                name="reviewer_name"
                autoComplete="name"
                value={reviewerName}
                onChange={(event) => setReviewerName(event.target.value)}
                maxLength={120}
                required
              />
            </label>
          )}
          <div className="actions">
            <button type="button" autoFocus onClick={() => dialog.current?.close()}>
              Keep running
            </button>
            <button className="destructive" type="submit">
              Stop run
            </button>
          </div>
        </form>
      </dialog>
    </>
  );
}
