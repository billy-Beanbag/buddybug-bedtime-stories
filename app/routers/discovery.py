from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlmodel import Session

from app.database import get_session
from app.middleware.request_context import get_request_id_from_request
from app.models import BookCollection, User
from app.schemas.discovery_schema import (
    BookCollectionCreate,
    BookCollectionItemCreate,
    BookCollectionItemRead,
    BookCollectionRead,
    BookCollectionUpdate,
    BookDiscoveryMetadataRead,
    BookDiscoveryMetadataUpdate,
    CollectionDetailResponse,
    DiscoverySearchRequest,
    DiscoverySearchResponse,
)
from app.services.analytics_service import track_event_safe
from app.services.audit_service import create_audit_log
from app.services.discovery_service import (
    add_collection_item,
    create_collection,
    delete_collection,
    delete_collection_item,
    get_book_discovery_metadata,
    get_collection_detail,
    get_collection_item_or_404,
    get_collection_or_404,
    list_collections,
    list_featured_books,
    rebuild_all_discovery_metadata,
    rebuild_book_discovery_metadata,
    search_books,
    update_book_discovery_metadata,
    update_collection,
    update_collection_item,
)
from app.utils.dependencies import get_current_editor_user, get_optional_current_user

router = APIRouter(prefix="/discovery", tags=["discovery"])
admin_router = APIRouter(prefix="/admin/discovery", tags=["admin-discovery"])


@router.get("/search", response_model=DiscoverySearchResponse, summary="Search published books")
def search_discovery_books(
    q: str | None = Query(default=None),
    age_band: str | None = Query(default=None),
    language: str | None = Query(default=None),
    content_lane_key: str | None = Query(default=None),
    tone_tag: str | None = Query(default=None),
    character_tag: str | None = Query(default=None),
    bedtime_safe: bool | None = Query(default=None),
    featured_only: bool = Query(default=False),
    child_profile_id: int | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> DiscoverySearchResponse:
    response = search_books(
        session,
        request=DiscoverySearchRequest(
            q=q,
            age_band=age_band,
            language=language,
            content_lane_key=content_lane_key,
            tone_tag=tone_tag,
            character_tag=character_tag,
            bedtime_safe=bedtime_safe,
            featured_only=featured_only,
            limit=limit,
            offset=offset,
        ),
        current_user=current_user,
        child_profile_id=child_profile_id,
        published_only=True,
    )
    track_event_safe(
        session,
        event_name="discovery_search",
        user=current_user,
        child_profile_id=child_profile_id,
        metadata={"q": q, "age_band": age_band, "language": language, "result_count": response.total},
    )
    return response


@router.get("/featured", response_model=DiscoverySearchResponse, summary="List featured discovery books")
def get_featured_discovery_books(
    age_band: str | None = Query(default=None),
    language: str | None = Query(default=None),
    content_lane_key: str | None = Query(default=None),
    child_profile_id: int | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> DiscoverySearchResponse:
    response = list_featured_books(
        session,
        age_band=age_band,
        language=language,
        content_lane_key=content_lane_key,
        limit=limit,
        current_user=current_user,
        child_profile_id=child_profile_id,
    )
    track_event_safe(
        session,
        event_name="featured_collection_viewed",
        user=current_user,
        child_profile_id=child_profile_id,
        metadata={"age_band": age_band, "language": language, "result_count": response.total},
    )
    return response


@router.get("/collections", response_model=list[BookCollectionRead], summary="List public curated collections")
def get_public_discovery_collections(
    age_band: str | None = Query(default=None),
    language: str | None = Query(default=None),
    content_lane_key: str | None = Query(default=None),
    featured_only: bool = Query(default=False),
    session: Session = Depends(get_session),
) -> list[BookCollectionRead]:
    return list_collections(
        session,
        age_band=age_band,
        language=language,
        content_lane_key=content_lane_key,
        featured_only=featured_only,
        public_only=True,
    )


@router.get("/collections/{collection_key}", response_model=CollectionDetailResponse, summary="Get one curated collection")
def get_public_collection_detail(
    collection_key: str,
    child_profile_id: int | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User | None = Depends(get_optional_current_user),
) -> CollectionDetailResponse:
    detail = get_collection_detail(
        session,
        collection_key=collection_key,
        current_user=current_user,
        child_profile_id=child_profile_id,
        public_only=True,
    )
    track_event_safe(
        session,
        event_name="discovery_collection_opened",
        user=current_user,
        child_profile_id=child_profile_id,
        metadata={"collection_key": collection_key, "item_count": len(detail.items)},
    )
    return detail


@admin_router.post("/books/{book_id}/rebuild", response_model=BookDiscoveryMetadataRead, summary="Rebuild discovery metadata for one book")
def rebuild_one_book_metadata(
    book_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> BookDiscoveryMetadataRead:
    metadata = rebuild_book_discovery_metadata(session, book_id=book_id)
    create_audit_log(
        session,
        action_type="book_discovery_metadata_rebuilt",
        entity_type="book_discovery_metadata",
        entity_id=str(metadata.id),
        summary=f"Rebuilt discovery metadata for book {book_id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"book_id": book_id},
    )
    return metadata


@admin_router.post("/rebuild-all", response_model=list[BookDiscoveryMetadataRead], summary="Rebuild discovery metadata for all books")
def rebuild_all_metadata(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> list[BookDiscoveryMetadataRead]:
    items = rebuild_all_discovery_metadata(session)
    create_audit_log(
        session,
        action_type="book_discovery_metadata_rebuilt_all",
        entity_type="book_discovery_metadata",
        entity_id="all",
        summary="Rebuilt discovery metadata for all books",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"count": len(items)},
    )
    return items


@admin_router.get("/books/{book_id}/metadata", response_model=BookDiscoveryMetadataRead, summary="Get one book discovery metadata row")
def get_book_metadata(
    book_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> BookDiscoveryMetadataRead:
    metadata = get_book_discovery_metadata(session, book_id=book_id)
    if metadata is None:
        metadata = rebuild_book_discovery_metadata(session, book_id=book_id)
    return metadata


@admin_router.patch("/books/{book_id}/metadata", response_model=BookDiscoveryMetadataRead, summary="Update one book discovery metadata row")
def patch_book_metadata(
    book_id: int,
    payload: BookDiscoveryMetadataUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> BookDiscoveryMetadataRead:
    metadata = get_book_discovery_metadata(session, book_id=book_id)
    if metadata is None:
        metadata = rebuild_book_discovery_metadata(session, book_id=book_id)
    return update_book_discovery_metadata(session, metadata=metadata, payload=payload)


@admin_router.get("/collections", response_model=list[BookCollectionRead], summary="List collections for admin/editor discovery tools")
def get_admin_collections(
    age_band: str | None = Query(default=None),
    language: str | None = Query(default=None),
    content_lane_key: str | None = Query(default=None),
    featured_only: bool = Query(default=False),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> list[BookCollectionRead]:
    return list_collections(
        session,
        age_band=age_band,
        language=language,
        content_lane_key=content_lane_key,
        featured_only=featured_only,
        public_only=False,
    )


@admin_router.post("/collections", response_model=BookCollectionRead, status_code=status.HTTP_201_CREATED, summary="Create collection")
def post_collection(
    payload: BookCollectionCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> BookCollectionRead:
    collection = create_collection(session, payload=payload, created_by_user_id=current_user.id)
    create_audit_log(
        session,
        action_type="discovery_collection_created",
        entity_type="book_collection",
        entity_id=str(collection.id),
        summary=f"Created discovery collection '{collection.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"key": collection.key},
    )
    return collection


@admin_router.patch("/collections/{collection_id}", response_model=BookCollectionRead, summary="Update collection")
def patch_collection(
    collection_id: int,
    payload: BookCollectionUpdate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> BookCollectionRead:
    collection = session.get(BookCollection, collection_id)
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    updated = update_collection(session, collection=collection, payload=payload)
    create_audit_log(
        session,
        action_type="discovery_collection_updated",
        entity_type="book_collection",
        entity_id=str(updated.id),
        summary=f"Updated discovery collection '{updated.title}'",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata=payload.model_dump(exclude_unset=True),
    )
    return updated


@admin_router.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete collection")
def remove_collection(
    collection_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> Response:
    collection = session.get(BookCollection, collection_id)
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    delete_collection(session, collection=collection)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@admin_router.post("/collections/{collection_id}/items", response_model=BookCollectionItemRead, status_code=status.HTTP_201_CREATED, summary="Add collection item")
def post_collection_item(
    collection_id: int,
    payload: BookCollectionItemCreate,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_editor_user),
) -> BookCollectionItemRead:
    collection = session.get(BookCollection, collection_id)
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    item = add_collection_item(session, collection=collection, payload=payload)
    create_audit_log(
        session,
        action_type="discovery_collection_item_added",
        entity_type="book_collection_item",
        entity_id=str(item.id),
        summary=f"Added book {item.book_id} to discovery collection {collection.id}",
        actor_user=current_user,
        request_id=get_request_id_from_request(request),
        metadata={"collection_id": collection.id, "book_id": item.book_id},
    )
    return item


@admin_router.patch("/collection-items/{item_id}", response_model=BookCollectionItemRead, summary="Update collection item")
def patch_collection_item(
    item_id: int,
    position: int | None = Query(default=None),
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> BookCollectionItemRead:
    item = get_collection_item_or_404(session, item_id=item_id)
    return update_collection_item(session, item=item, position=position)


@admin_router.delete("/collection-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete collection item")
def remove_collection_item(
    item_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(get_current_editor_user),
) -> Response:
    item = get_collection_item_or_404(session, item_id=item_id)
    delete_collection_item(session, item=item)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
