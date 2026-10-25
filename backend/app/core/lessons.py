"""Human lesson governance; no model is involved in curation."""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.auth import token_hash
from app.core.config import Settings
from app.core.safety import PublicDataSafety
from app.db.models import LessonConfirmation, LessonRevision, LessonSet, User
from app.db.repositories.lessons import LessonRepository, lesson_entry
from app.domain.lessons import (
    LessonAudit,
    LessonInput,
    content_hash,
    empty_snapshot,
    render_lessons,
)
from app.events.log import EventLog
from app.security.lesson_filter import screen


class LessonError(ValueError):
    def __init__(self, status: int, code: str, message: str, **details: Any):
        self.status, self.code, self.message, self.details = (
            status,
            code,
            message,
            details,
        )
        super().__init__(message)


class LessonService:
    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        settings: Settings,
        events: EventLog,
    ):
        self.sessions, self.settings, self.events = sessions, settings, events
        self.safety = PublicDataSafety(settings)

    def check(self, lesson: LessonInput) -> dict[str, Any]:
        result = screen(lesson.text)
        if self.safety.text(lesson.text) != lesson.text:
            result = {
                **result,
                "passed": False,
                "reasons": [
                    *result["reasons"],
                    {
                        "id": "secret",
                        "message": "Remove possible credentials or secrets.",
                    },
                ],
            }
        return result

    async def snapshot(self, auth_mode: str) -> dict[str, Any]:
        if auth_mode != "account":
            return empty_snapshot(
                "benchmark" if auth_mode == "shared_key" else "unconfigured"
            )
        if not self.settings.lessons_enabled:
            return empty_snapshot("server_disabled")
        async with self.sessions() as session, session.begin():
            control = await LessonRepository(session).control()
            if not control.runtime_enabled:
                return empty_snapshot("runtime_disabled")
            active = await session.get(LessonSet, control.set_version)
            assert active is not None
            return {
                "lessons_enabled": True,
                "set_version": active.version,
                "set_hash": active.sha256,
                "entries": active.entries,
                "disable_generation": control.disable_generation,
                "self_approved": any(row["self_approved"] for row in active.entries),
                "reason": "eligible" if active.entries else "no_lessons",
            }

    def screened(self, lesson: LessonInput) -> dict[str, Any]:
        result = self.check(lesson)
        if not result["passed"]:
            raise LessonError(
                422,
                "lesson_filter_rejected",
                "The lesson did not pass the deterministic filter.",
                filter_result=result,
            )
        return result

    async def _view(
        self, session: AsyncSession, row: LessonRevision, *, admin: bool
    ) -> dict[str, Any]:
        proposer = await session.get(User, row.proposer_id)
        approver = await session.get(User, row.approved_by) if row.approved_by else None
        result = {
            **lesson_entry(row),
            "status": row.status,
            "previous_id": str(row.previous_id) if row.previous_id else None,
            "decision_id": str(row.decision_id),
            "proposer_id": str(row.proposer_id),
            "proposer": proposer.username if proposer else None,
            "approved_by": str(row.approved_by) if row.approved_by else None,
            "approver": approver.username if approver else None,
            "approved_at": row.approved_at.isoformat() if row.approved_at else None,
            "created_at": row.created_at.isoformat(),
            "filter_result": self.check(
                LessonInput.model_validate(
                    {
                        "scope_role": row.scope_role,
                        "applies_to": row.applies_to,
                        "category": row.category,
                        "text": row.text,
                    }
                )
            ),
            "proposal_filter_result": row.filter_result,
            "approval_filter_result": row.approval_filter_result,
        }
        if admin:
            decision = await LessonRepository(session).decision(row.decision_id)
            details = (
                (decision.payload.get("review_decision") or {}) if decision else {}
            )
            result["source_decision"] = (
                {
                    "id": str(decision.event_id),
                    "run_id": str(decision.run_id),
                    "variant": decision.payload.get("variant"),
                    "timestamp": decision.timestamp.isoformat(),
                    **{
                        key: details.get(key)
                        for key in (
                            "action",
                            "reviewer_name",
                            "user_id",
                            "reason",
                            "category",
                            "decided_at",
                            "identity_basis",
                        )
                    },
                }
                if decision
                else None
            )
        return self.safety.value(result)  # type: ignore[no-any-return]

    async def propose(
        self,
        actor: User,
        decision_id: UUID,
        lesson: LessonInput,
        previous_id: UUID | None = None,
    ) -> dict[str, Any]:
        filtered = self.screened(lesson)
        async with self.sessions() as session, session.begin():
            repo = LessonRepository(session)
            control = await repo.control()
            decision = await repo.decision(decision_id)
            if decision is None:
                raise LessonError(404, "not_found", "Review decision not found.")
            details = decision.payload.get("review_decision") or {}
            if (
                details.get("user_id") != str(actor.id)
                or details.get("identity_basis") != "authenticated account"
            ):
                raise LessonError(
                    403,
                    "forbidden",
                    "Propose lessons only from your own authenticated decisions.",
                )
            previous = await repo.get(previous_id) if previous_id else None
            if previous_id and (
                previous is None
                or previous.proposer_id != actor.id
                or previous.decision_id != decision_id
            ):
                raise LessonError(
                    403,
                    "forbidden",
                    "Only the proposal owner may create its next version.",
                )
            if previous and previous.revision != await repo.latest(previous.lesson_id):
                raise LessonError(
                    409,
                    "lesson_conflict",
                    "Create the next version from the latest revision.",
                )
            if previous and previous.status == "proposed":
                previous.status = "rejected"
                await self.events.append(
                    LessonAudit(
                        actor.id,
                        "superseded",
                        previous.id,
                        previous.previous_id,
                        decision.run_id,
                        control.set_version,
                    ),
                    audit_session=session,
                )
            row = LessonRevision(
                id=uuid4(),
                lesson_id=previous.lesson_id if previous else uuid4(),
                revision=previous.revision + 1 if previous else 1,
                previous_id=previous.id if previous else None,
                decision_id=decision_id,
                proposer_id=actor.id,
                status="proposed",
                filter_result=filtered,
                created_at=datetime.now(UTC),
                self_approved=False,
                **lesson.model_dump(),
            )
            session.add(row)
            await session.flush()
            await self.events.append(
                LessonAudit(
                    actor.id,
                    "proposed",
                    row.id,
                    row.previous_id,
                    decision.run_id,
                    control.set_version,
                    {"actor": actor.username, "filter_result": filtered},
                ),
                audit_session=session,
            )
            return await self._view(session, row, admin=actor.role == "admin")

    async def _preview(
        self, repo: LessonRepository, row: LessonRevision
    ) -> dict[str, Any]:
        entries = [
            lesson_entry(item)
            for item in await repo.active()
            if item.lesson_id != row.lesson_id
        ]
        entries.append(lesson_entry(row))
        roles = (
            [row.scope_role]
            if row.scope_role != "all_generators"
            else ["generator_cost", "generator_performance", "generator_security"]
        )
        blocks = {}
        for role in roles:
            block, ids = render_lessons(entries, role)
            blocks[role] = {
                "block": block,
                "selected_ids": ids,
                "included": str(row.id) in ids,
            }
        return {
            "filter_result": self.check(
                LessonInput.model_validate(
                    {
                        "scope_role": row.scope_role,
                        "applies_to": row.applies_to,
                        "category": row.category,
                        "text": row.text,
                    }
                )
            ),
            "roles": blocks,
        }

    async def detail(self, identity: UUID) -> dict[str, Any]:
        async with self.sessions() as session, session.begin():
            repo = LessonRepository(session)
            await repo.control()
            row = await repo.get(identity)
            if row is None:
                raise LessonError(404, "not_found", "Lesson not found.")
            previous = await repo.get(row.previous_id) if row.previous_id else None
            return {
                "lesson": await self._view(session, row, admin=True),
                "previous": await self._view(session, previous, admin=True)
                if previous
                else None,
                "preview": await self._preview(repo, row),
            }

    async def listing(
        self, status: str | None, page: int, lesson_id: UUID | None = None
    ) -> dict[str, Any]:
        async with self.sessions() as session, session.begin():
            repo = LessonRepository(session)
            await repo.control()
            rows, total = await repo.listing(status, page, lesson_id)
            return {
                "items": [await self._view(session, row, admin=True) for row in rows],
                "total": total,
                "page": page,
                "page_size": 25,
            }

    async def history(self, page: int) -> dict[str, Any]:
        async with self.sessions() as session:
            rows, total = await LessonRepository(session).history(page)
            result: dict[str, Any] = self.safety.value(
                {
                    "items": [
                        {
                            "id": str(row.id),
                            "seq": row.seq,
                            "actor_id": str(row.actor_id),
                            "action": row.action,
                            "revision_id": str(row.revision_id)
                            if row.revision_id
                            else None,
                            "previous_version": str(row.previous_version)
                            if row.previous_version
                            else None,
                            "set_version": row.set_version,
                            "timestamp": row.timestamp.isoformat(),
                            "payload": row.payload,
                        }
                        for row in rows
                    ],
                    "page": page,
                    "page_size": 25,
                    "total": total,
                }
            )
            return result

    async def controls(self) -> dict[str, Any]:
        async with self.sessions() as session, session.begin():
            row = await LessonRepository(session).control()
            active = await session.get(LessonSet, row.set_version)
            assert active is not None
            return {
                "server_enabled": self.settings.lessons_enabled,
                "runtime_enabled": row.runtime_enabled,
                "enabled": self.settings.lessons_enabled and row.runtime_enabled,
                "require_second_approver": (
                    self.settings.lessons_require_second_approver
                ),
                "disable_generation": row.disable_generation,
                "set_version": active.version,
                "set_hash": active.sha256,
                "lesson_count": len(active.entries),
            }

    async def set_enabled(self, actor: User, enabled: bool) -> dict[str, Any]:
        if enabled and not self.settings.lessons_enabled:
            raise LessonError(
                409,
                "lessons_server_disabled",
                "Enable LESSONS_ENABLED on the server first.",
            )
        async with self.sessions() as session, session.begin():
            row = await LessonRepository(session).control()
            row.runtime_enabled = enabled
            if not enabled:
                row.disable_generation += 1
            await self.events.append(
                LessonAudit(
                    actor.id,
                    "enabled" if enabled else "disabled",
                    set_version=row.set_version,
                    data={
                        "actor": actor.username,
                        "disable_generation": row.disable_generation,
                    },
                ),
                audit_session=session,
            )
        return await self.controls()

    async def _approval_data(
        self, repo: LessonRepository, row: LessonRevision, version: int
    ) -> dict[str, Any]:
        return {
            "lesson": lesson_entry(row),
            "preview": await self._preview(repo, row),
            "set_version": version,
            "require_second_approver": (self.settings.lessons_require_second_approver),
        }

    async def confirmation(
        self, actor: User, session_hash: str, identity: UUID
    ) -> dict[str, Any]:
        async with self.sessions() as session, session.begin():
            repo = LessonRepository(session)
            control = await repo.control()
            row = await repo.get(identity)
            if row is None:
                raise LessonError(404, "not_found", "Lesson not found.")
            if row.status != "proposed":
                raise LessonError(
                    409, "lesson_conflict", "Only a proposed lesson can be approved."
                )
            if (
                self.settings.lessons_require_second_approver
                or row.proposer_id != actor.id
            ):
                raise LessonError(
                    403,
                    "second_approver_required",
                    "Self-approval confirmation is unavailable under this policy.",
                )
            self.screened(
                LessonInput.model_validate(
                    {
                        "scope_role": row.scope_role,
                        "applies_to": row.applies_to,
                        "category": row.category,
                        "text": row.text,
                    }
                )
            )
            data = await self._approval_data(repo, row, control.set_version)
            token = secrets.token_urlsafe(32)
            expiry = datetime.now(UTC) + timedelta(minutes=5)
            session.add(
                LessonConfirmation(
                    token_hash=token_hash(token),
                    actor_id=actor.id,
                    session_hash=session_hash,
                    revision_id=row.id,
                    preview_hash=content_hash(data),
                    expires_at=expiry,
                )
            )
            return {
                "confirmation_token": token,
                "expires_at": expiry.isoformat(),
                **data,
                "warning": (
                    "Four-eyes review is off. You are approving your own lesson."
                ),
            }

    async def transition(
        self,
        actor: User,
        session_hash: str,
        identity: UUID,
        action: Literal["approve", "reject", "retire"],
        confirmation_token: str | None = None,
    ) -> dict[str, Any]:
        async with self.sessions() as session, session.begin():
            repo = LessonRepository(session)
            control = await repo.control()
            row = await repo.get(identity)
            if row is None:
                raise LessonError(404, "not_found", "Lesson not found.")
            if row.status != ("approved" if action == "retire" else "proposed"):
                raise LessonError(
                    409, "lesson_conflict", "The lesson changed. Reload before acting."
                )
            filtered = None
            if action == "approve":
                filtered = self.screened(
                    LessonInput.model_validate(
                        {
                            "scope_role": row.scope_role,
                            "applies_to": row.applies_to,
                            "category": row.category,
                            "text": row.text,
                        }
                    )
                )
                if confirmation_token is not None and row.proposer_id != actor.id:
                    raise LessonError(
                        409,
                        "lesson_confirmation_mismatch",
                        "Self-approval confirmation does not match this proposal.",
                    )
                if row.proposer_id == actor.id:
                    if self.settings.lessons_require_second_approver:
                        raise LessonError(
                            403,
                            "second_approver_required",
                            "A different named administrator must approve this lesson.",
                        )
                    token = (
                        await session.get(
                            LessonConfirmation, token_hash(confirmation_token)
                        )
                        if confirmation_token
                        else None
                    )
                    data = await self._approval_data(repo, row, control.set_version)
                    if (
                        token is None
                        or token.actor_id != actor.id
                        or token.session_hash != session_hash
                        or token.revision_id != row.id
                        or token.consumed_at is not None
                        or token.expires_at <= datetime.now(UTC)
                        or token.preview_hash != content_hash(data)
                    ):
                        raise LessonError(
                            409,
                            "self_approval_confirmation_required",
                            "Review the filter result and prompt preview "
                            "in a fresh confirmation first.",
                        )
                    token.consumed_at = datetime.now(UTC)
                for active in await repo.active():
                    if active.lesson_id == row.lesson_id:
                        active.status = "retired"
                        await session.flush()
                        await self.events.append(
                            LessonAudit(
                                actor.id,
                                "superseded_active",
                                active.id,
                                active.previous_id,
                                set_version=control.set_version,
                                data={"replacement_id": str(row.id)},
                            ),
                            audit_session=session,
                        )
                row.approved_by, row.approved_at = actor.id, datetime.now(UTC)
                row.self_approved = row.proposer_id == actor.id
                row.approval_filter_result = filtered
            row.status = {
                "approve": "approved",
                "reject": "rejected",
                "retire": "retired",
            }[action]
            await session.flush()
            if action != "reject":
                await repo.new_set(control)
            await self.events.append(
                LessonAudit(
                    actor.id,
                    row.status,
                    row.id,
                    row.previous_id,
                    set_version=control.set_version,
                    data={
                        "actor": actor.username,
                        "self_approved": row.self_approved,
                        "filter_result": filtered,
                    },
                ),
                audit_session=session,
            )
            return await self._view(session, row, admin=True)
