from datetime import datetime

from app.celery_app import celery_app
from app.db.database import SessionLocal
from app.services.stats import stats_for_device, stats_for_user_devices_aggregate


@celery_app.task(name="stats.analyze_device")
def analyze_device_task(
    device_id: str,
    from_ts_iso: str | None,
    to_ts_iso: str | None,
) -> dict | None:
    from_ts = datetime.fromisoformat(from_ts_iso) if from_ts_iso else None
    to_ts = datetime.fromisoformat(to_ts_iso) if to_ts_iso else None
    db = SessionLocal()
    try:
        st = stats_for_device(db, device_id, from_ts, to_ts)
        return st.as_dict() if st else None
    finally:
        db.close()


@celery_app.task(name="stats.analyze_user_aggregate")
def analyze_user_aggregate_task(
    user_id: int,
    from_ts_iso: str | None,
    to_ts_iso: str | None,
) -> dict | None:
    from_ts = datetime.fromisoformat(from_ts_iso) if from_ts_iso else None
    to_ts = datetime.fromisoformat(to_ts_iso) if to_ts_iso else None
    db = SessionLocal()
    try:
        st = stats_for_user_devices_aggregate(db, user_id, from_ts, to_ts)
        return st.as_dict() if st else None
    finally:
        db.close()
