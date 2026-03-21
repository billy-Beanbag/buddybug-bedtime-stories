from sqlmodel import Session, select

from app.models import HousekeepingPolicy

DEFAULT_HOUSEKEEPING_POLICIES = [
    {
        "key": "old_notification_events",
        "name": "Old notification events",
        "target_table": "notification_events",
        "action_type": "report_only",
        "retention_days": 90,
        "enabled": True,
        "dry_run_only": True,
        "notes": "Dry-run only visibility into old delivered and read notifications.",
    },
    {
        "key": "old_reengagement_suggestions",
        "name": "Old reengagement suggestions",
        "target_table": "reengagement_suggestions",
        "action_type": "soft_cleanup",
        "retention_days": 60,
        "enabled": True,
        "dry_run_only": True,
        "notes": "Dismissed suggestions are safe cleanup candidates after review.",
    },
    {
        "key": "old_completed_maintenance_jobs",
        "name": "Old completed maintenance jobs",
        "target_table": "maintenance_jobs",
        "action_type": "report_only",
        "retention_days": 120,
        "enabled": True,
        "dry_run_only": True,
        "notes": "Maintenance job history stays report-only in the first version.",
    },
    {
        "key": "old_succeeded_workflow_jobs",
        "name": "Old succeeded workflow jobs",
        "target_table": "workflow_jobs",
        "action_type": "report_only",
        "retention_days": 120,
        "enabled": True,
        "dry_run_only": True,
        "notes": "Workflow job retention starts with reporting only.",
    },
]


def seed_housekeeping_policies(session: Session) -> None:
    existing_keys = {key for key in session.exec(select(HousekeepingPolicy.key)).all()}
    created_any = False
    for payload in DEFAULT_HOUSEKEEPING_POLICIES:
        if payload["key"] in existing_keys:
            continue
        session.add(HousekeepingPolicy(**payload))
        created_any = True
    if created_any:
        session.commit()
