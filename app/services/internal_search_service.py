from __future__ import annotations

import json
from collections.abc import Callable

from sqlalchemy import func, or_
from sqlmodel import Session, select

from app.models import (
    Book,
    ChildProfile,
    EditorialProject,
    FeatureFlag,
    IncidentRecord,
    MaintenanceJob,
    SeasonalCampaign,
    StoryDraft,
    SupportTicket,
    User,
)
from app.schemas.internal_search_schema import (
    InternalSearchGroup,
    InternalSearchResult,
    QuickActionItem,
)

SEARCH_GROUP_LABELS = {
    "user": "Users",
    "child_profile": "Child Profiles",
    "book": "Books",
    "story_draft": "Story Drafts",
    "editorial_project": "Editorial Projects",
    "support_ticket": "Support Tickets",
    "incident": "Incidents",
    "campaign": "Campaigns",
    "feature_flag": "Feature Flags",
    "maintenance_job": "Maintenance Jobs",
}
MIN_QUERY_LENGTH = 2
MAX_LIMIT_PER_GROUP = 10


def _normalize_query(query: str | None) -> str:
    return (query or "").strip()


def _normalized_limit(limit_per_group: int) -> int:
    return max(1, min(MAX_LIMIT_PER_GROUP, limit_per_group))


def _contains(column, query: str):
    return func.lower(func.coalesce(column, "")).like(f"%{query.lower()}%")


def _maybe_id_match(model, query: str):
    if not query.isdigit():
        return None
    return model.id == int(query)


def _serialize_metadata(value: dict[str, object] | None) -> str | None:
    if not value:
        return None
    return json.dumps(value, sort_keys=True, default=str)


def _truncate(value: str | None, limit: int = 140) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if len(stripped) <= limit:
        return stripped
    return f"{stripped[: limit - 3].rstrip()}..."


def _role_badge(user: User) -> str:
    if user.is_admin:
        return "admin"
    if user.is_editor:
        return "editor"
    if user.is_educator:
        return "educator"
    return user.subscription_tier


def search_users(session: Session, *, query: str, limit: int) -> list[InternalSearchResult]:
    conditions = [_contains(User.email, query), _contains(User.display_name, query)]
    id_match = _maybe_id_match(User, query)
    if id_match is not None:
        conditions.append(id_match)
    users = list(
        session.exec(
            select(User).where(or_(*conditions)).order_by(User.created_at.desc(), User.id.desc()).limit(limit)
        ).all()
    )
    return [
        InternalSearchResult(
            entity_type="user",
            entity_id=str(user.id),
            title=user.display_name or user.email,
            subtitle=user.email if user.display_name else None,
            description=f"Subscription: {user.subscription_tier} • Language: {user.language}",
            route=f"/admin/search?q={user.id}",
            badge=_role_badge(user),
            metadata_json=_serialize_metadata(
                {
                    "email": user.email,
                    "is_active": user.is_active,
                    "subscription_tier": user.subscription_tier,
                }
            ),
        )
        for user in users
    ]


def search_child_profiles(session: Session, *, query: str, limit: int) -> list[InternalSearchResult]:
    conditions = [_contains(ChildProfile.display_name, query)]
    id_match = _maybe_id_match(ChildProfile, query)
    if id_match is not None:
        conditions.append(id_match)
    child_profiles = list(
        session.exec(
            select(ChildProfile)
            .where(or_(*conditions))
            .order_by(ChildProfile.created_at.desc(), ChildProfile.id.desc())
            .limit(limit)
        ).all()
    )
    return [
        InternalSearchResult(
            entity_type="child_profile",
            entity_id=str(child_profile.id),
            title=child_profile.display_name,
            subtitle=f"Age band {child_profile.age_band} • User #{child_profile.user_id}",
            description=f"Language: {child_profile.language}",
            route=f"/admin/search?q={child_profile.id}",
            badge="active" if child_profile.is_active else "inactive",
            metadata_json=_serialize_metadata(
                {
                    "user_id": child_profile.user_id,
                    "language": child_profile.language,
                }
            ),
        )
        for child_profile in child_profiles
    ]


def search_books(session: Session, *, query: str, limit: int) -> list[InternalSearchResult]:
    conditions = [_contains(Book.title, query)]
    id_match = _maybe_id_match(Book, query)
    if id_match is not None:
        conditions.append(id_match)
    books = list(
        session.exec(select(Book).where(or_(*conditions)).order_by(Book.created_at.desc(), Book.id.desc()).limit(limit)).all()
    )
    return [
        InternalSearchResult(
            entity_type="book",
            entity_id=str(book.id),
            title=book.title,
            subtitle=f"{book.language} • Age band {book.age_band}",
            description=f"Story draft #{book.story_draft_id}",
            route="/admin/books",
            badge=book.publication_status,
            metadata_json=_serialize_metadata(
                {
                    "published": book.published,
                    "story_draft_id": book.story_draft_id,
                }
            ),
        )
        for book in books
    ]


def search_story_drafts(session: Session, *, query: str, limit: int) -> list[InternalSearchResult]:
    conditions = [_contains(StoryDraft.title, query)]
    id_match = _maybe_id_match(StoryDraft, query)
    if id_match is not None:
        conditions.append(id_match)
    drafts = list(
        session.exec(
            select(StoryDraft).where(or_(*conditions)).order_by(StoryDraft.created_at.desc(), StoryDraft.id.desc()).limit(limit)
        ).all()
    )
    return [
        InternalSearchResult(
            entity_type="story_draft",
            entity_id=str(draft.id),
            title=draft.title,
            subtitle=f"{draft.language} • Age band {draft.age_band}",
            description=f"Project #{draft.project_id}" if draft.project_id is not None else "Standalone draft",
            route=f"/admin/drafts/{draft.id}",
            badge=draft.review_status,
            metadata_json=_serialize_metadata(
                {
                    "project_id": draft.project_id,
                    "story_idea_id": draft.story_idea_id,
                }
            ),
        )
        for draft in drafts
    ]


def search_editorial_projects(session: Session, *, query: str, limit: int) -> list[InternalSearchResult]:
    conditions = [_contains(EditorialProject.title, query), _contains(EditorialProject.slug, query)]
    id_match = _maybe_id_match(EditorialProject, query)
    if id_match is not None:
        conditions.append(id_match)
    projects = list(
        session.exec(
            select(EditorialProject)
            .where(or_(*conditions))
            .order_by(EditorialProject.created_at.desc(), EditorialProject.id.desc())
            .limit(limit)
        ).all()
    )
    return [
        InternalSearchResult(
            entity_type="editorial_project",
            entity_id=str(project.id),
            title=project.title,
            subtitle=project.slug,
            description=f"{project.language} • {project.source_type}",
            route=f"/admin/editorial/{project.id}",
            badge=project.status,
            metadata_json=_serialize_metadata(
                {
                    "assigned_editor_user_id": project.assigned_editor_user_id,
                    "content_lane_key": project.content_lane_key,
                }
            ),
        )
        for project in projects
    ]


def search_support_tickets(session: Session, *, query: str, limit: int) -> list[InternalSearchResult]:
    conditions = [_contains(SupportTicket.subject, query), _contains(SupportTicket.email, query)]
    id_match = _maybe_id_match(SupportTicket, query)
    if id_match is not None:
        conditions.append(id_match)
    tickets = list(
        session.exec(
            select(SupportTicket)
            .where(or_(*conditions))
            .order_by(SupportTicket.created_at.desc(), SupportTicket.id.desc())
            .limit(limit)
        ).all()
    )
    return [
        InternalSearchResult(
            entity_type="support_ticket",
            entity_id=str(ticket.id),
            title=ticket.subject,
            subtitle=f"{ticket.category} • {ticket.priority}",
            description=_truncate(ticket.message),
            route=f"/admin/support/{ticket.id}",
            badge=ticket.status,
            metadata_json=_serialize_metadata(
                {
                    "user_id": ticket.user_id,
                    "child_profile_id": ticket.child_profile_id,
                    "email": ticket.email,
                }
            ),
        )
        for ticket in tickets
    ]


def search_incidents(session: Session, *, query: str, limit: int) -> list[InternalSearchResult]:
    conditions = [_contains(IncidentRecord.title, query), _contains(IncidentRecord.affected_area, query)]
    id_match = _maybe_id_match(IncidentRecord, query)
    if id_match is not None:
        conditions.append(id_match)
    incidents = list(
        session.exec(
            select(IncidentRecord)
            .where(or_(*conditions))
            .order_by(IncidentRecord.created_at.desc(), IncidentRecord.id.desc())
            .limit(limit)
        ).all()
    )
    return [
        InternalSearchResult(
            entity_type="incident",
            entity_id=str(incident.id),
            title=incident.title,
            subtitle=f"{incident.affected_area} • {incident.severity}",
            description=_truncate(incident.summary),
            route=f"/admin/incidents/{incident.id}",
            badge=incident.status,
            metadata_json=_serialize_metadata({"feature_flag_key": incident.feature_flag_key}),
        )
        for incident in incidents
    ]


def search_campaigns(session: Session, *, query: str, limit: int) -> list[InternalSearchResult]:
    conditions = [_contains(SeasonalCampaign.title, query), _contains(SeasonalCampaign.key, query)]
    id_match = _maybe_id_match(SeasonalCampaign, query)
    if id_match is not None:
        conditions.append(id_match)
    campaigns = list(
        session.exec(
            select(SeasonalCampaign)
            .where(or_(*conditions))
            .order_by(SeasonalCampaign.created_at.desc(), SeasonalCampaign.id.desc())
            .limit(limit)
        ).all()
    )
    return [
        InternalSearchResult(
            entity_type="campaign",
            entity_id=campaign.key,
            title=campaign.title,
            subtitle=campaign.key,
            description=_truncate(campaign.description),
            route=f"/campaigns/{campaign.key}",
            badge="active" if campaign.is_active else "inactive",
            metadata_json=_serialize_metadata(
                {
                    "language": campaign.language,
                    "age_band": campaign.age_band,
                }
            ),
        )
        for campaign in campaigns
    ]


def search_feature_flags(session: Session, *, query: str, limit: int) -> list[InternalSearchResult]:
    conditions = [_contains(FeatureFlag.key, query), _contains(FeatureFlag.name, query)]
    id_match = _maybe_id_match(FeatureFlag, query)
    if id_match is not None:
        conditions.append(id_match)
    flags = list(
        session.exec(
            select(FeatureFlag)
            .where(or_(*conditions))
            .order_by(FeatureFlag.updated_at.desc(), FeatureFlag.id.desc())
            .limit(limit)
        ).all()
    )
    return [
        InternalSearchResult(
            entity_type="feature_flag",
            entity_id=flag.key,
            title=flag.name,
            subtitle=flag.key,
            description=_truncate(flag.description),
            route="/admin/feature-flags",
            badge="enabled" if flag.enabled else "disabled",
            metadata_json=_serialize_metadata({"rollout_percentage": flag.rollout_percentage}),
        )
        for flag in flags
    ]


def search_maintenance_jobs(session: Session, *, query: str, limit: int) -> list[InternalSearchResult]:
    conditions = [_contains(MaintenanceJob.key, query), _contains(MaintenanceJob.title, query)]
    id_match = _maybe_id_match(MaintenanceJob, query)
    if id_match is not None:
        conditions.append(id_match)
    jobs = list(
        session.exec(
            select(MaintenanceJob)
            .where(or_(*conditions))
            .order_by(MaintenanceJob.created_at.desc(), MaintenanceJob.id.desc())
            .limit(limit)
        ).all()
    )
    return [
        InternalSearchResult(
            entity_type="maintenance_job",
            entity_id=str(job.id),
            title=job.title,
            subtitle=job.key,
            description=job.target_scope or job.job_type,
            route="/admin/maintenance",
            badge=job.status,
            metadata_json=_serialize_metadata({"job_type": job.job_type}),
        )
        for job in jobs
    ]


def search_internal_entities(session: Session, *, query: str, limit_per_group: int = 5) -> list[InternalSearchGroup]:
    normalized_query = _normalize_query(query)
    if len(normalized_query) < MIN_QUERY_LENGTH:
        return []

    limit = _normalized_limit(limit_per_group)
    searchers: list[tuple[str, Callable[[Session], list[InternalSearchResult]]]] = [
        ("user", lambda active_session: search_users(active_session, query=normalized_query, limit=limit)),
        ("child_profile", lambda active_session: search_child_profiles(active_session, query=normalized_query, limit=limit)),
        ("book", lambda active_session: search_books(active_session, query=normalized_query, limit=limit)),
        ("story_draft", lambda active_session: search_story_drafts(active_session, query=normalized_query, limit=limit)),
        (
            "editorial_project",
            lambda active_session: search_editorial_projects(active_session, query=normalized_query, limit=limit),
        ),
        ("support_ticket", lambda active_session: search_support_tickets(active_session, query=normalized_query, limit=limit)),
        ("incident", lambda active_session: search_incidents(active_session, query=normalized_query, limit=limit)),
        ("campaign", lambda active_session: search_campaigns(active_session, query=normalized_query, limit=limit)),
        ("feature_flag", lambda active_session: search_feature_flags(active_session, query=normalized_query, limit=limit)),
        (
            "maintenance_job",
            lambda active_session: search_maintenance_jobs(active_session, query=normalized_query, limit=limit),
        ),
    ]

    groups: list[InternalSearchGroup] = []
    for entity_type, searcher in searchers:
        items = searcher(session)
        if not items:
            continue
        groups.append(
            InternalSearchGroup(
                entity_type=entity_type,
                label=SEARCH_GROUP_LABELS[entity_type],
                items=items,
            )
        )
    return groups


def _base_quick_actions() -> list[QuickActionItem]:
    return [
        QuickActionItem(
            key="open_search_console",
            label="Open internal search console",
            route="/admin/search",
            action_type="route",
            description="Open the full internal search page.",
            permission_hint="editor_or_admin",
        ),
        QuickActionItem(
            key="open_support_queue",
            label="Open support queue",
            route="/admin/support",
            action_type="route",
            description="Jump to active support ticket triage.",
            permission_hint="editor_or_admin",
        ),
        QuickActionItem(
            key="open_incident_console",
            label="Open incident console",
            route="/admin/incidents",
            action_type="route",
            description="Jump to current production incidents.",
            permission_hint="admin",
        ),
        QuickActionItem(
            key="open_feature_flags",
            label="Open feature flags",
            route="/admin/feature-flags",
            action_type="route",
            description="Review release controls and rollout targets.",
            permission_hint="admin",
        ),
        QuickActionItem(
            key="open_maintenance_jobs",
            label="Open maintenance jobs",
            route="/admin/maintenance",
            action_type="route",
            description="Review bounded backfills and rebuild jobs.",
            permission_hint="admin",
        ),
    ]


def _filter_actions(actions: list[QuickActionItem], query: str | None) -> list[QuickActionItem]:
    normalized_query = _normalize_query(query).lower()
    if len(normalized_query) < MIN_QUERY_LENGTH:
        return []
    return [
        action
        for action in actions
        if normalized_query in action.label.lower() or normalized_query in (action.description or "").lower()
    ]


def get_quick_actions_for_context(
    *,
    entity_type: str | None,
    entity_id: str | None,
    query: str | None = None,
) -> list[QuickActionItem]:
    if entity_type is None or entity_id is None:
        return _filter_actions(_base_quick_actions(), query)

    if entity_type == "user":
        return [
            QuickActionItem(
                key="open_user_search",
                label="Open user in search console",
                route=f"/admin/search?q={entity_id}",
                action_type="route",
                entity_type=entity_type,
                entity_id=entity_id,
                description="Show this user in the standalone internal search console.",
                permission_hint="editor_or_admin",
            ),
            QuickActionItem(
                key="open_user_account_health",
                label="Open account health",
                route="/admin/account-health",
                action_type="route",
                entity_type=entity_type,
                entity_id=entity_id,
                description="Open the account health workspace for follow-up actions.",
                permission_hint="admin",
            ),
            QuickActionItem(
                key="copy_user_id",
                label="Copy user ID",
                route=None,
                action_type="copy",
                entity_type=entity_type,
                entity_id=entity_id,
                description=f"Copy user ID {entity_id}.",
                permission_hint="editor_or_admin",
            ),
        ]
    if entity_type == "child_profile":
        return [
            QuickActionItem(
                key="open_child_search",
                label="Open child profile in search console",
                route=f"/admin/search?q={entity_id}",
                action_type="route",
                entity_type=entity_type,
                entity_id=entity_id,
                description="Show this child profile in the standalone internal search console.",
                permission_hint="editor_or_admin",
            ),
            QuickActionItem(
                key="open_account_health_from_child",
                label="Open account health",
                route="/admin/account-health",
                action_type="route",
                entity_type=entity_type,
                entity_id=entity_id,
                description="Open the surrounding account-health workspace.",
                permission_hint="admin",
            ),
            QuickActionItem(
                key="copy_child_profile_id",
                label="Copy child profile ID",
                route=None,
                action_type="copy",
                entity_type=entity_type,
                entity_id=entity_id,
                description=f"Copy child profile ID {entity_id}.",
                permission_hint="editor_or_admin",
            ),
        ]
    if entity_type == "book":
        return [
            QuickActionItem(
                key="open_book_queue",
                label="Open books queue",
                route="/admin/books",
                action_type="route",
                entity_type=entity_type,
                entity_id=entity_id,
                description="Open the internal books queue.",
                permission_hint="editor_or_admin",
            ),
            QuickActionItem(
                key="open_reader_preview",
                label="Open reader preview",
                route=f"/reader/{entity_id}",
                action_type="route",
                entity_type=entity_type,
                entity_id=entity_id,
                description="Open the live reader view for this book.",
                permission_hint="editor_or_admin",
            ),
            QuickActionItem(
                key="copy_book_id",
                label="Copy book ID",
                route=None,
                action_type="copy",
                entity_type=entity_type,
                entity_id=entity_id,
                description=f"Copy book ID {entity_id}.",
                permission_hint="editor_or_admin",
            ),
        ]
    if entity_type == "story_draft":
        return [
            QuickActionItem(
                key="open_story_draft",
                label="Open story draft",
                route=f"/admin/drafts/{entity_id}",
                action_type="route",
                entity_type=entity_type,
                entity_id=entity_id,
                description="Open the draft detail page.",
                permission_hint="editor_or_admin",
            ),
            QuickActionItem(
                key="open_drafts_queue",
                label="Open drafts queue",
                route="/admin/drafts",
                action_type="route",
                entity_type=entity_type,
                entity_id=entity_id,
                description="Return to the draft review queue.",
                permission_hint="editor_or_admin",
            ),
            QuickActionItem(
                key="copy_story_draft_id",
                label="Copy draft ID",
                route=None,
                action_type="copy",
                entity_type=entity_type,
                entity_id=entity_id,
                description=f"Copy story draft ID {entity_id}.",
                permission_hint="editor_or_admin",
            ),
        ]
    if entity_type == "editorial_project":
        return [
            QuickActionItem(
                key="open_editorial_project",
                label="Open editorial project",
                route=f"/admin/editorial/{entity_id}",
                action_type="route",
                entity_type=entity_type,
                entity_id=entity_id,
                description="Open the editorial project detail page.",
                permission_hint="editor_or_admin",
            ),
            QuickActionItem(
                key="open_editorial_projects",
                label="Open editorial projects",
                route="/admin/editorial",
                action_type="route",
                entity_type=entity_type,
                entity_id=entity_id,
                description="Return to the editorial project list.",
                permission_hint="editor_or_admin",
            ),
            QuickActionItem(
                key="copy_editorial_project_id",
                label="Copy project ID",
                route=None,
                action_type="copy",
                entity_type=entity_type,
                entity_id=entity_id,
                description=f"Copy editorial project ID {entity_id}.",
                permission_hint="editor_or_admin",
            ),
        ]
    if entity_type == "support_ticket":
        return [
            QuickActionItem(
                key="open_support_ticket",
                label="Open support ticket",
                route=f"/admin/support/{entity_id}",
                action_type="route",
                entity_type=entity_type,
                entity_id=entity_id,
                description="Open ticket detail and notes.",
                permission_hint="editor_or_admin",
            ),
            QuickActionItem(
                key="open_support_queue",
                label="Open support queue",
                route="/admin/support",
                action_type="route",
                entity_type=entity_type,
                entity_id=entity_id,
                description="Return to the support queue.",
                permission_hint="editor_or_admin",
            ),
            QuickActionItem(
                key="copy_support_ticket_id",
                label="Copy support ticket ID",
                route=None,
                action_type="copy",
                entity_type=entity_type,
                entity_id=entity_id,
                description=f"Copy support ticket ID {entity_id}.",
                permission_hint="editor_or_admin",
            ),
        ]
    if entity_type == "incident":
        return [
            QuickActionItem(
                key="open_incident",
                label="Open incident",
                route=f"/admin/incidents/{entity_id}",
                action_type="route",
                entity_type=entity_type,
                entity_id=entity_id,
                description="Open the incident detail page.",
                permission_hint="admin",
            ),
            QuickActionItem(
                key="open_incident_console",
                label="Open incident console",
                route="/admin/incidents",
                action_type="route",
                entity_type=entity_type,
                entity_id=entity_id,
                description="Return to the incident console.",
                permission_hint="admin",
            ),
            QuickActionItem(
                key="copy_incident_id",
                label="Copy incident ID",
                route=None,
                action_type="copy",
                entity_type=entity_type,
                entity_id=entity_id,
                description=f"Copy incident ID {entity_id}.",
                permission_hint="admin",
            ),
        ]
    if entity_type == "campaign":
        return [
            QuickActionItem(
                key="open_campaign",
                label="Open campaign page",
                route=f"/campaigns/{entity_id}",
                action_type="route",
                entity_type=entity_type,
                entity_id=entity_id,
                description="Open the campaign destination page.",
                permission_hint="editor_or_admin",
            ),
            QuickActionItem(
                key="open_discover",
                label="Open discover page",
                route="/discover",
                action_type="route",
                entity_type=entity_type,
                entity_id=entity_id,
                description="Open discovery surfaces where campaigns appear.",
                permission_hint="editor_or_admin",
            ),
            QuickActionItem(
                key="copy_campaign_key",
                label="Copy campaign key",
                route=None,
                action_type="copy",
                entity_type=entity_type,
                entity_id=entity_id,
                description=f"Copy campaign key {entity_id}.",
                permission_hint="editor_or_admin",
            ),
        ]
    if entity_type == "feature_flag":
        return [
            QuickActionItem(
                key="open_feature_flags",
                label="Open feature flags",
                route="/admin/feature-flags",
                action_type="route",
                entity_type=entity_type,
                entity_id=entity_id,
                description="Open the feature flags admin surface.",
                permission_hint="admin",
            ),
            QuickActionItem(
                key="copy_feature_flag_key",
                label="Copy feature flag key",
                route=None,
                action_type="copy",
                entity_type=entity_type,
                entity_id=entity_id,
                description=f"Copy feature flag key {entity_id}.",
                permission_hint="admin",
            ),
        ]
    if entity_type == "maintenance_job":
        return [
            QuickActionItem(
                key="open_maintenance_jobs",
                label="Open maintenance jobs",
                route="/admin/maintenance",
                action_type="route",
                entity_type=entity_type,
                entity_id=entity_id,
                description="Open the maintenance jobs workspace.",
                permission_hint="admin",
            ),
            QuickActionItem(
                key="copy_maintenance_job_id",
                label="Copy maintenance job ID",
                route=None,
                action_type="copy",
                entity_type=entity_type,
                entity_id=entity_id,
                description=f"Copy maintenance job ID {entity_id}.",
                permission_hint="admin",
            ),
        ]

    return []
