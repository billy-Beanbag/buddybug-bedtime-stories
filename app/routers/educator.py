from fastapi import APIRouter, Depends, Request, Response, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.educator_schema import (
    ClassroomSetCreate,
    ClassroomSetDetailResponse,
    ClassroomSetItemCreate,
    ClassroomSetItemRead,
    ClassroomSetRead,
    ClassroomSetUpdate,
)
from app.services.audit_service import create_audit_log
from app.services.educator_service import (
    add_classroom_set_item,
    create_classroom_set,
    delete_classroom_set,
    get_classroom_set_detail,
    get_classroom_set_item_or_404,
    get_classroom_set_or_404,
    list_classroom_sets_for_educator,
    remove_classroom_set_item,
    update_classroom_set,
    validate_educator_ownership,
)
from app.utils.dependencies import get_current_educator_user

router = APIRouter(prefix="/educator", tags=["educator"])


@router.get("/classroom-sets", response_model=list[ClassroomSetRead], summary="List classroom sets")
def list_classroom_sets(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_educator_user),
) -> list[ClassroomSetRead]:
    return list_classroom_sets_for_educator(session, current_user=current_user)


@router.get("/classroom-sets/{set_id}", response_model=ClassroomSetDetailResponse, summary="Get one classroom set")
def get_one_classroom_set(
    set_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_educator_user),
) -> ClassroomSetDetailResponse:
    classroom_set = get_classroom_set_or_404(session, set_id=set_id)
    validate_educator_ownership(current_user=current_user, classroom_set=classroom_set)
    return get_classroom_set_detail(session, classroom_set=classroom_set)


@router.post("/classroom-sets", response_model=ClassroomSetRead, status_code=status.HTTP_201_CREATED, summary="Create classroom set")
def post_classroom_set(
    payload: ClassroomSetCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_educator_user),
) -> ClassroomSetRead:
    classroom_set = create_classroom_set(session, current_user=current_user, payload=payload)
    create_audit_log(
        session,
        action_type="classroom_set_created",
        entity_type="classroom_set",
        entity_id=str(classroom_set.id),
        summary=f"Created classroom set '{classroom_set.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"age_band": classroom_set.age_band, "language": classroom_set.language},
    )
    return classroom_set


@router.patch("/classroom-sets/{set_id}", response_model=ClassroomSetRead, summary="Update classroom set")
def patch_classroom_set(
    set_id: int,
    payload: ClassroomSetUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_educator_user),
) -> ClassroomSetRead:
    classroom_set = get_classroom_set_or_404(session, set_id=set_id)
    validate_educator_ownership(current_user=current_user, classroom_set=classroom_set)
    updated = update_classroom_set(session, classroom_set=classroom_set, payload=payload)
    create_audit_log(
        session,
        action_type="classroom_set_updated",
        entity_type="classroom_set",
        entity_id=str(updated.id),
        summary=f"Updated classroom set '{updated.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(exclude_unset=True),
    )
    return updated


@router.delete("/classroom-sets/{set_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete classroom set")
def delete_one_classroom_set(
    set_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_educator_user),
) -> Response:
    classroom_set = get_classroom_set_or_404(session, set_id=set_id)
    validate_educator_ownership(current_user=current_user, classroom_set=classroom_set)
    delete_classroom_set(session, classroom_set=classroom_set)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/classroom-sets/{set_id}/items",
    response_model=ClassroomSetItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add classroom set item",
)
def post_classroom_set_item(
    set_id: int,
    payload: ClassroomSetItemCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_educator_user),
) -> ClassroomSetItemRead:
    classroom_set = get_classroom_set_or_404(session, set_id=set_id)
    validate_educator_ownership(current_user=current_user, classroom_set=classroom_set)
    item = add_classroom_set_item(session, classroom_set=classroom_set, payload=payload)
    create_audit_log(
        session,
        action_type="classroom_set_item_added",
        entity_type="classroom_set_item",
        entity_id=str(item.id),
        summary=f"Added book {item.book_id} to classroom set '{classroom_set.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"classroom_set_id": classroom_set.id, "book_id": item.book_id},
    )
    return item


@router.delete("/classroom-set-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete classroom set item")
def delete_one_classroom_set_item(
    item_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_educator_user),
) -> Response:
    item = get_classroom_set_item_or_404(session, item_id=item_id)
    classroom_set = get_classroom_set_or_404(session, set_id=item.classroom_set_id)
    validate_educator_ownership(current_user=current_user, classroom_set=classroom_set)
    remove_classroom_set_item(session, item=item)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
