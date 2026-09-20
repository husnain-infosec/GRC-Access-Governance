from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

def log_audit_event(
    db: Session,
    action: str,
    ip_address: str,
    status: str,
    user_id=None,
    department_id=None,
    target_user_id=None,
    resource_id=None,
    metadata: dict | None = None,
):
    entry = AuditLog(
        user_id=user_id,
        department_id=department_id,
        action=action,
        target_user_id=target_user_id,
        resource_id=resource_id,
        ip_address=ip_address,
        status=status,
        metadata_json=metadata,
    )
    db.add(entry)