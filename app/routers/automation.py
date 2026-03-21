from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.automation_schema import (
    AutomationQueueResponse,
    AutomationScheduleCreate,
    AutomationScheduleRead,
    AutomationScheduleRunResponse,
    AutomationScheduleUpdate,
)
from app.services.automation_service import (
    activate_schedule,
    automation_schedule_to_read,
    create_schedule,
    deactivate_schedule,
    delete_schedule,
    get_automation_schedule_or_404,
    get_due_schedules,
    list_automation_schedules,
    run_due_schedules,
    run_schedule,
    update_schedule,
)
from app.utils.dependencies import get_current_admin_user

router = APIRouter(
    prefix="/automation",
    tags=["automation"],
    dependencies=[Depends(get_current_admin_user)],
)


@router.get("/schedules", response_model=AutomationQueueResponse, summary="List automation schedules")
def list_schedules(
    is_active: bool | None = Query(default=None),
    job_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
) -> AutomationQueueResponse:
    items = list_automation_schedules(session, is_active=is_active, job_type=job_type, limit=limit)
    return AutomationQueueResponse(items=[automation_schedule_to_read(item) for item in items])


@router.get("/schedules/{schedule_id}", response_model=AutomationScheduleRead, summary="Get one automation schedule")
def get_schedule(
    schedule_id: int,
    session: Session = Depends(get_session),
) -> AutomationScheduleRead:
    return automation_schedule_to_read(get_automation_schedule_or_404(session, schedule_id))


@router.post("/schedules", response_model=AutomationScheduleRead, summary="Create an automation schedule")
def create_automation_schedule(
    payload: AutomationScheduleCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> AutomationScheduleRead:
    schedule = create_schedule(
        session,
        payload=payload,
        created_by_user_id=current_user.id,
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
    )
    return automation_schedule_to_read(schedule)


@router.patch("/schedules/{schedule_id}", response_model=AutomationScheduleRead, summary="Update an automation schedule")
def update_automation_schedule(
    schedule_id: int,
    payload: AutomationScheduleUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> AutomationScheduleRead:
    schedule = get_automation_schedule_or_404(session, schedule_id)
    updated = update_schedule(
        session,
        schedule=schedule,
        payload=payload,
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
    )
    return automation_schedule_to_read(updated)


@router.delete("/schedules/{schedule_id}", summary="Delete an automation schedule")
def delete_automation_schedule(
    schedule_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> dict[str, bool]:
    schedule = get_automation_schedule_or_404(session, schedule_id)
    delete_schedule(
        session,
        schedule=schedule,
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
    )
    return {"deleted": True}


@router.post("/schedules/{schedule_id}/activate", response_model=AutomationScheduleRead, summary="Activate an automation schedule")
def activate_automation_schedule(
    schedule_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> AutomationScheduleRead:
    schedule = get_automation_schedule_or_404(session, schedule_id)
    activated = activate_schedule(
        session,
        schedule=schedule,
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
    )
    return automation_schedule_to_read(activated)


@router.post("/schedules/{schedule_id}/deactivate", response_model=AutomationScheduleRead, summary="Deactivate an automation schedule")
def deactivate_automation_schedule(
    schedule_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> AutomationScheduleRead:
    schedule = get_automation_schedule_or_404(session, schedule_id)
    deactivated = deactivate_schedule(
        session,
        schedule=schedule,
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
    )
    return automation_schedule_to_read(deactivated)


@router.post("/schedules/{schedule_id}/run", response_model=AutomationScheduleRunResponse, summary="Run an automation schedule now")
def run_automation_schedule(
    schedule_id: int,
    background_tasks: BackgroundTasks,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> AutomationScheduleRunResponse:
    schedule = get_automation_schedule_or_404(session, schedule_id)
    return run_schedule(
        session,
        schedule=schedule,
        background_tasks=background_tasks,
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        force=True,
    )


@router.get("/due", response_model=AutomationQueueResponse, summary="List due automation schedules")
def list_due_automation_schedules(
    limit: int = Query(default=100, ge=1, le=300),
    session: Session = Depends(get_session),
) -> AutomationQueueResponse:
    items = get_due_schedules(session, limit=limit)
    return AutomationQueueResponse(items=[automation_schedule_to_read(item) for item in items])


@router.post("/run-due", response_model=list[AutomationScheduleRunResponse], summary="Run due automation schedules")
def run_due_automation_schedules(
    background_tasks: BackgroundTasks,
    request: Request,
    limit: int = Query(default=10, ge=1, le=50),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> list[AutomationScheduleRunResponse]:
    return run_due_schedules(
        session,
        limit=limit,
        background_tasks=background_tasks,
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
    )
