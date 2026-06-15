import asyncio
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select

from app.db import SessionLocal
from app.deps import CurrentUser, SessionDep
from app.models import ImportJob
from app.routes.inspirations import _extract_share_draft, _extracted_text
from app.schemas.import_job import InspirationImportJobOut
from app.schemas.inspiration import InspirationFromShareIn, InspirationShareDraftOut

router = APIRouter(prefix="/import-jobs", tags=["import-jobs"])

_JOB_TTL = timedelta(minutes=15)
_ACTIVE_STATUSES = {"pending", "running"}
_RUNNING_TASKS: set[asyncio.Task[None]] = set()
logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


def _build_share_draft(
    extracted: dict[str, object], source_url: str | None
) -> InspirationShareDraftOut:
    return InspirationShareDraftOut(
        destination=_extracted_text(extracted, "destination")[:64],
        source_url=source_url,
        note=_extracted_text(extracted, "note")[:500] or None,
        plan_detail=_extracted_text(extracted, "planDetail")[:4000] or None,
        events=list(extracted.get("events") or []),
    )


def _job_out(job: ImportJob) -> InspirationImportJobOut:
    result = None
    if isinstance(job.result_json, dict):
        result = InspirationShareDraftOut.model_validate(job.result_json)
    return InspirationImportJobOut.model_validate(
        {
            "id": job.id,
            "status": job.status,
            "result": result,
            "error_message": job.error_message,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "expires_at": job.expires_at,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
        }
    )


async def _expire_if_needed(session: SessionDep, job: ImportJob) -> ImportJob:
    if job.status not in _ACTIVE_STATUSES or job.expires_at > _now():
        return job

    job.status = "expired"
    job.error_message = "任务已超时，请重新导入"
    job.finished_at = _now()
    job.updated_at = _now()
    await session.commit()
    await session.refresh(job)
    return job


async def _mark_job_running(job_id: UUID) -> str | None:
    async with SessionLocal() as session:
        job = await session.scalar(select(ImportJob).where(ImportJob.id == job_id))
        if job is None:
            return None
        if job.status not in _ACTIVE_STATUSES:
            return None
        if job.expires_at <= _now():
            job.status = "expired"
            job.error_message = "任务已超时，请重新导入"
            job.finished_at = _now()
            job.updated_at = _now()
            await session.commit()
            return None

        job.status = "running"
        job.started_at = job.started_at or _now()
        job.error_message = None
        job.updated_at = _now()
        shared_text = job.shared_text
        await session.commit()
        return shared_text


async def _finish_job(
    job_id: UUID,
    *,
    status_value: str,
    result: InspirationShareDraftOut | None = None,
    source_url: str | None = None,
    error_message: str | None = None,
) -> None:
    async with SessionLocal() as session:
        job = await session.scalar(select(ImportJob).where(ImportJob.id == job_id))
        if job is None:
            return
        job.status = status_value
        job.source_url = source_url
        job.result_json = result.model_dump(mode="json") if result is not None else None
        job.error_message = error_message
        job.finished_at = _now()
        job.updated_at = _now()
        await session.commit()


async def _process_share_import_job(job_id: UUID | str) -> None:
    parsed_job_id = UUID(str(job_id))
    shared_text = await _mark_job_running(parsed_job_id)
    if shared_text is None:
        return

    try:
        extracted, source_url = await _extract_share_draft(shared_text)
        draft = _build_share_draft(extracted, source_url)
    except HTTPException as e:
        await _finish_job(
            parsed_job_id,
            status_value="failed",
            error_message=str(e.detail or "整理失败，请稍后再试"),
        )
    except ValidationError:
        await _finish_job(
            parsed_job_id,
            status_value="failed",
            error_message="整理结果格式异常，请稍后重试",
        )
    except Exception:
        logger.exception("share import job failed", extra={"job_id": str(parsed_job_id)})
        await _finish_job(
            parsed_job_id,
            status_value="failed",
            error_message="整理失败，请稍后再试",
        )
    else:
        await _finish_job(
            parsed_job_id,
            status_value="succeeded",
            result=draft,
            source_url=source_url,
        )


def _schedule_share_import_job(job_id: UUID) -> None:
    task = asyncio.create_task(_process_share_import_job(job_id))
    _RUNNING_TASKS.add(task)
    task.add_done_callback(_RUNNING_TASKS.discard)


@router.post(
    "/from-share",
    response_model=InspirationImportJobOut,
    response_model_by_alias=True,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_share_import_job(
    payload: InspirationFromShareIn,
    user: CurrentUser,
    session: SessionDep,
) -> InspirationImportJobOut:
    job = ImportJob(
        user_id=user.id,
        kind="share_inspiration",
        status="pending",
        shared_text=payload.shared_text,
        expires_at=_now() + _JOB_TTL,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    _schedule_share_import_job(job.id)
    return _job_out(job)


@router.get(
    "/{job_id}",
    response_model=InspirationImportJobOut,
    response_model_by_alias=True,
)
async def get_import_job(
    job_id: UUID,
    user: CurrentUser,
    session: SessionDep,
) -> InspirationImportJobOut:
    job = await session.scalar(
        select(ImportJob).where(ImportJob.id == job_id, ImportJob.user_id == user.id)
    )
    if job is None:
        raise HTTPException(status_code=404, detail="import job not found")

    job = await _expire_if_needed(session, job)
    return _job_out(job)
