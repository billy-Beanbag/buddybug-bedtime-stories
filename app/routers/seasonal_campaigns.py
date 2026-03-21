from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import User
from app.schemas.seasonal_campaign_schema import (
    SeasonalCampaignCreate,
    SeasonalCampaignDetailResponse,
    SeasonalCampaignItemCreate,
    SeasonalCampaignItemRead,
    SeasonalCampaignRead,
    SeasonalCampaignUpdate,
)
from app.services.audit_service import create_audit_log
from app.services.seasonal_campaign_service import (
    add_campaign_item,
    delete_campaign,
    get_active_campaigns,
    get_campaign_detail,
    get_campaign_item_or_404,
    get_campaign_or_404,
    list_campaigns_for_admin,
    remove_campaign_item,
    create_campaign,
    update_campaign,
)
from app.utils.dependencies import get_current_editor_user, get_optional_current_user

router = APIRouter(prefix="/campaigns", tags=["campaigns"])
admin_router = APIRouter(prefix="/admin/campaigns", tags=["admin-campaigns"])
admin_item_router = APIRouter(prefix="/admin/campaign-items", tags=["admin-campaigns"])


@router.get("/active", response_model=list[SeasonalCampaignRead], summary="List active seasonal campaigns")
def list_active_campaigns(
    language: str | None = Query(default=None),
    age_band: str | None = Query(default=None),
    content_lane_key: str | None = Query(default=None),
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> list[SeasonalCampaignRead]:
    return get_active_campaigns(
        session,
        language=language,
        age_band=age_band,
        content_lane_key=content_lane_key,
        current_user=current_user,
        child_profile_id=child_profile_id,
    )


@router.get("/{campaign_key}", response_model=SeasonalCampaignDetailResponse, summary="Get one active campaign")
def get_public_campaign_detail(
    campaign_key: str,
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> SeasonalCampaignDetailResponse:
    return get_campaign_detail(
        session,
        campaign_key=campaign_key,
        current_user=current_user,
        child_profile_id=child_profile_id,
        active_only=True,
    )


@admin_router.get("", response_model=list[SeasonalCampaignRead], summary="List seasonal campaigns")
def list_admin_campaigns(
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> list[SeasonalCampaignRead]:
    return list_campaigns_for_admin(session)


@admin_router.post("", response_model=SeasonalCampaignRead, status_code=status.HTTP_201_CREATED, summary="Create campaign")
def post_campaign(
    payload: SeasonalCampaignCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> SeasonalCampaignRead:
    campaign = create_campaign(session, payload=payload, created_by_user_id=current_user.id)
    create_audit_log(
        session,
        action_type="seasonal_campaign_created",
        entity_type="seasonal_campaign",
        entity_id=str(campaign.id),
        summary=f"Created seasonal campaign '{campaign.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"key": campaign.key},
    )
    return campaign


@admin_router.patch("/{campaign_id}", response_model=SeasonalCampaignRead, summary="Update campaign")
def patch_campaign(
    campaign_id: int,
    payload: SeasonalCampaignUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> SeasonalCampaignRead:
    campaign = get_campaign_or_404(session, campaign_id=campaign_id)
    updated = update_campaign(session, campaign=campaign, payload=payload)
    create_audit_log(
        session,
        action_type="seasonal_campaign_updated",
        entity_type="seasonal_campaign",
        entity_id=str(updated.id),
        summary=f"Updated seasonal campaign '{updated.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(exclude_unset=True),
    )
    return updated


@admin_router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete campaign")
def remove_campaign(
    campaign_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> Response:
    campaign = get_campaign_or_404(session, campaign_id=campaign_id)
    delete_campaign(session, campaign=campaign)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@admin_router.post(
    "/{campaign_id}/items",
    response_model=SeasonalCampaignItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add campaign item",
)
def post_campaign_item(
    campaign_id: int,
    payload: SeasonalCampaignItemCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> SeasonalCampaignItemRead:
    campaign = get_campaign_or_404(session, campaign_id=campaign_id)
    item = add_campaign_item(session, campaign=campaign, payload=payload)
    create_audit_log(
        session,
        action_type="seasonal_campaign_item_added",
        entity_type="seasonal_campaign_item",
        entity_id=str(item.id),
        summary=f"Added book {item.book_id} to campaign '{campaign.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"campaign_id": campaign.id, "book_id": item.book_id},
    )
    return item


@admin_item_router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete campaign item",
)
def delete_campaign_item_route(
    item_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> Response:
    item = get_campaign_item_or_404(session, item_id=item_id)
    remove_campaign_item(session, item=item)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
