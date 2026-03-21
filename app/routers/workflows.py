from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.workflow_schema import (
    AssembleBookJobRequest,
    FullStoryPipelineJobRequest,
    GenerateDraftJobRequest,
    GenerateDailyStorySuggestionJobRequest,
    GenerateIdeasJobRequest,
    GenerateIllustrationPlanJobRequest,
    GenerateNarrationJobRequest,
    GeneratePageIllustrationsJobRequest,
    WorkflowJobCreate,
    WorkflowJobRead,
    WorkflowJobRunResponse,
    WorkflowQueueResponse,
)
from app.services.admin_service import delete_workflow_record
from app.services.workflow_service import (
    cancel_job,
    create_and_start_background_job,
    create_job,
    get_workflow_job_or_404,
    list_workflow_jobs,
    run_job,
    run_queued_jobs,
)
from app.utils.dependencies import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/workflows", tags=["workflows"])
admin_router = APIRouter(prefix="/admin/workflows", tags=["workflows-admin"])


def _job_snapshot(job) -> WorkflowJobRunResponse:
    return WorkflowJobRunResponse(job=WorkflowJobRead.model_validate(job))


def _list_jobs_for_requester(
    session: Session,
    *,
    current_user: User,
    status_value: str | None,
    job_type: str | None,
    created_by_user_id: int | None,
    limit: int,
) -> list:
    effective_created_by = created_by_user_id if current_user.is_admin else current_user.id
    return list_workflow_jobs(
        session,
        status_value=status_value,
        job_type=job_type,
        created_by_user_id=effective_created_by,
        limit=limit,
    )


@router.get("/jobs", response_model=WorkflowQueueResponse, summary="List workflow jobs")
def get_workflow_jobs(
    status_value: str | None = Query(default=None, alias="status"),
    job_type: str | None = Query(default=None),
    created_by_user_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> WorkflowQueueResponse:
    items = _list_jobs_for_requester(
        session,
        current_user=current_user,
        status_value=status_value,
        job_type=job_type,
        created_by_user_id=created_by_user_id,
        limit=limit,
    )
    return WorkflowQueueResponse(items=[WorkflowJobRead.model_validate(item) for item in items])


@router.get("/jobs/{job_id}", response_model=WorkflowJobRead, summary="Get one workflow job")
def get_workflow_job(
    job_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> WorkflowJobRead:
    job = get_workflow_job_or_404(session, job_id)
    if not current_user.is_admin and job.created_by_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this workflow job")
    return WorkflowJobRead.model_validate(job)


@router.post("/jobs", response_model=WorkflowJobRunResponse, summary="Create a generic workflow job")
def create_generic_workflow_job(
    payload: WorkflowJobCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> WorkflowJobRunResponse:
    job = create_job(
        session,
        job_type=payload.job_type,
        payload_json=payload.payload_json,
        created_by_user_id=current_user.id,
        priority=payload.priority,
        scheduled_for=payload.scheduled_for,
        max_attempts=payload.max_attempts,
        parent_job_id=payload.parent_job_id,
        request_id=get_request_id_from_request(request),
    )
    return _job_snapshot(job)


@router.post("/jobs/{job_id}/run", response_model=WorkflowJobRunResponse, summary="Run a queued or failed job now")
def run_workflow_job_now(
    job_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> WorkflowJobRunResponse:
    job = get_workflow_job_or_404(session, job_id)
    if not current_user.is_admin and job.created_by_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to run this workflow job")
    job = run_job(
        session,
        job=job,
        actor_user_id=current_user.id,
        request_id=get_request_id_from_request(request),
    )
    return _job_snapshot(job)


@router.post("/jobs/{job_id}/cancel", response_model=WorkflowJobRunResponse, summary="Cancel a queued job")
def cancel_workflow_job(
    job_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> WorkflowJobRunResponse:
    job = get_workflow_job_or_404(session, job_id)
    if not current_user.is_admin and job.created_by_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to cancel this workflow job")
    job = cancel_job(
        session,
        job=job,
        actor_user_id=current_user.id,
        request_id=get_request_id_from_request(request),
    )
    return _job_snapshot(job)


@router.post("/generate-ideas", response_model=WorkflowJobRunResponse, summary="Enqueue and run a story ideas job")
def enqueue_generate_ideas_job(
    payload: GenerateIdeasJobRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> WorkflowJobRunResponse:
    job = create_and_start_background_job(
        background_tasks=background_tasks,
        session=session,
        job_type="generate_story_ideas",
        payload=payload.model_dump(mode="json"),
        created_by_user_id=current_user.id,
        request_id=get_request_id_from_request(request),
    )
    return _job_snapshot(job)


@router.post("/generate-draft", response_model=WorkflowJobRunResponse, summary="Enqueue and run a draft generation job")
def enqueue_generate_draft_job(
    payload: GenerateDraftJobRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> WorkflowJobRunResponse:
    job = create_and_start_background_job(
        background_tasks=background_tasks,
        session=session,
        job_type="generate_story_draft",
        payload=payload.model_dump(mode="json"),
        created_by_user_id=current_user.id,
        request_id=get_request_id_from_request(request),
    )
    return _job_snapshot(job)


@router.post(
    "/generate-illustration-plan",
    response_model=WorkflowJobRunResponse,
    summary="Enqueue and run an illustration plan job",
)
def enqueue_generate_illustration_plan_job(
    payload: GenerateIllustrationPlanJobRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> WorkflowJobRunResponse:
    job = create_and_start_background_job(
        background_tasks=background_tasks,
        session=session,
        job_type="generate_illustration_plan",
        payload=payload.model_dump(mode="json"),
        created_by_user_id=current_user.id,
        request_id=get_request_id_from_request(request),
    )
    return _job_snapshot(job)


@router.post(
    "/generate-page-illustrations",
    response_model=WorkflowJobRunResponse,
    summary="Enqueue and run a page illustration generation job",
)
def enqueue_generate_page_illustrations_job(
    payload: GeneratePageIllustrationsJobRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> WorkflowJobRunResponse:
    job = create_and_start_background_job(
        background_tasks=background_tasks,
        session=session,
        job_type="generate_page_illustrations",
        payload=payload.model_dump(mode="json"),
        created_by_user_id=current_user.id,
        request_id=get_request_id_from_request(request),
    )
    return _job_snapshot(job)


@router.post(
    "/generate-narration",
    response_model=WorkflowJobRunResponse,
    summary="Enqueue and run a narration generation job",
)
def enqueue_generate_narration_job(
    payload: GenerateNarrationJobRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> WorkflowJobRunResponse:
    job = create_and_start_background_job(
        background_tasks=background_tasks,
        session=session,
        job_type="generate_book_narration",
        payload=payload.model_dump(mode="json"),
        created_by_user_id=current_user.id,
        request_id=get_request_id_from_request(request),
    )
    return _job_snapshot(job)


@router.post(
    "/generate-daily-story",
    response_model=WorkflowJobRunResponse,
    summary="Enqueue and run a daily story suggestion job",
)
def enqueue_generate_daily_story_job(
    payload: GenerateDailyStorySuggestionJobRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> WorkflowJobRunResponse:
    job = create_and_start_background_job(
        background_tasks=background_tasks,
        session=session,
        job_type="generate_daily_story_suggestion",
        payload=payload.model_dump(mode="json"),
        created_by_user_id=current_user.id,
        request_id=get_request_id_from_request(request),
    )
    return _job_snapshot(job)


@router.post("/assemble-book", response_model=WorkflowJobRunResponse, summary="Enqueue and run a book assembly job")
def enqueue_assemble_book_job(
    payload: AssembleBookJobRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> WorkflowJobRunResponse:
    job = create_and_start_background_job(
        background_tasks=background_tasks,
        session=session,
        job_type="assemble_book",
        payload=payload.model_dump(mode="json"),
        created_by_user_id=current_user.id,
        request_id=get_request_id_from_request(request),
    )
    return _job_snapshot(job)


@router.post("/full-pipeline", response_model=WorkflowJobRunResponse, summary="Enqueue and run a safe full story pipeline job")
def enqueue_full_pipeline_job(
    payload: FullStoryPipelineJobRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> WorkflowJobRunResponse:
    job = create_and_start_background_job(
        background_tasks=background_tasks,
        session=session,
        job_type="full_story_pipeline",
        payload=payload.model_dump(mode="json"),
        created_by_user_id=current_user.id,
        request_id=get_request_id_from_request(request),
    )
    return _job_snapshot(job)


@admin_router.get("/queue", response_model=WorkflowQueueResponse, summary="Admin workflow queue view")
def get_admin_workflow_queue(
    status_value: str | None = Query(default=None, alias="status"),
    job_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
) -> WorkflowQueueResponse:
    items = list_workflow_jobs(
        session,
        status_value=status_value,
        job_type=job_type,
        created_by_user_id=None,
        limit=limit,
    )
    return WorkflowQueueResponse(items=[WorkflowJobRead.model_validate(item) for item in items])


@admin_router.delete(
    "/record",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a story workflow record (book, draft, idea) and all dependencies",
)
def remove_workflow_record(
    book_id: int | None = Query(default=None),
    draft_id: int | None = Query(default=None),
    idea_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_admin_user),
):
    if not any([book_id is not None, draft_id is not None, idea_id is not None]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of book_id, draft_id, or idea_id is required",
        )
    try:
        delete_workflow_record(session, book_id=book_id, draft_id=draft_id, idea_id=idea_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        ) from e


@admin_router.post("/run-queued", response_model=WorkflowQueueResponse, summary="Run queued jobs in order")
def run_admin_queued_jobs(
    request: Request,
    limit: int = Query(default=10, ge=1, le=50),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> WorkflowQueueResponse:
    items = run_queued_jobs(
        session,
        limit=limit,
        actor_user_id=current_user.id,
        request_id=get_request_id_from_request(request),
    )
    return WorkflowQueueResponse(items=[WorkflowJobRead.model_validate(item) for item in items])
