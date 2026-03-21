from fastapi import APIRouter, Depends, Query, Request, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.translation_ops_schema import (
    TranslationTaskCreate,
    TranslationTaskDetailResponse,
    TranslationTaskUpdate,
)
from app.services.audit_service import create_audit_log
from app.services.translation_ops_service import (
    create_translation_task,
    get_translation_task_detail,
    get_translation_task_or_404,
    infer_missing_translations,
    list_translation_tasks,
    update_translation_task,
)
from app.utils.dependencies import get_current_editor_user

router = APIRouter(prefix="/admin/translations", tags=["translation-ops"])


@router.get("/tasks", response_model=list[TranslationTaskDetailResponse], summary="List translation tasks")
def get_translation_tasks(
    language: str | None = Query(default=None),
    status_value: str | None = Query(default=None, alias="status"),
    assigned_to_user_id: int | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> list[TranslationTaskDetailResponse]:
    return list_translation_tasks(
        session,
        language=language,
        status_value=status_value,
        assigned_to_user_id=assigned_to_user_id,
        limit=limit,
    )


@router.get("/tasks/{task_id}", response_model=TranslationTaskDetailResponse, summary="Get one translation task")
def get_translation_task(
    task_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> TranslationTaskDetailResponse:
    return get_translation_task_detail(session, task_id=task_id)


@router.post("/tasks", response_model=TranslationTaskDetailResponse, status_code=status.HTTP_201_CREATED, summary="Create translation task")
def post_translation_task(
    payload: TranslationTaskCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> TranslationTaskDetailResponse:
    task = create_translation_task(
        session,
        book_id=payload.book_id,
        language=payload.language,
        status_value=payload.status,
        assigned_to_user_id=payload.assigned_to_user_id,
        source_version_label=payload.source_version_label,
        notes=payload.notes,
        due_at=payload.due_at,
    )
    create_audit_log(
        session,
        action_type="translation_task_created",
        entity_type="translation_task",
        entity_id=str(task.id),
        summary=f"Created translation task for book {task.book_id} in {task.language}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"book_id": task.book_id, "language": task.language, "status": task.status},
    )
    return get_translation_task_detail(session, task_id=task.id)


@router.patch("/tasks/{task_id}", response_model=TranslationTaskDetailResponse, summary="Update translation task")
def patch_translation_task(
    task_id: int,
    payload: TranslationTaskUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> TranslationTaskDetailResponse:
    task = get_translation_task_or_404(session, task_id)
    updated = update_translation_task(session, task=task, payload=payload)
    create_audit_log(
        session,
        action_type="translation_task_updated",
        entity_type="translation_task",
        entity_id=str(updated.id),
        summary=f"Updated translation task for book {updated.book_id} in {updated.language}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(exclude_unset=True),
    )
    return get_translation_task_detail(session, task_id=updated.id)


@router.get("/missing", response_model=list[TranslationTaskDetailResponse], summary="List missing translation opportunities")
def get_missing_translations(
    language: str | None = Query(default=None),
    age_band: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> list[TranslationTaskDetailResponse]:
    return infer_missing_translations(session, language=language, age_band=age_band, limit=limit)
