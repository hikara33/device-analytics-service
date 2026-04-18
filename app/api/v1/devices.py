from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.models.models import DeviceSample
from app.schemas.schemas import AsyncTaskAccepted, SampleIn, SampleOut, StatsBlock
from app.services.stats import stats_for_device
from app.tasks.stats_tasks import analyze_device_task

router = APIRouter()


@router.post(
    "/{device_id}/samples",
    response_model=SampleOut,
    status_code=status.HTTP_201_CREATED,
)
def ingest_sample(
    device_id: str,
    body: SampleIn,
    db: Session = Depends(get_db),
) -> SampleOut:
    ts = body.recorded_at if body.recorded_at is not None else datetime.utcnow()
    row = DeviceSample(
        device_id=device_id,
        x=body.x,
        y=body.y,
        z=body.z,
        created_at=ts,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{device_id}/stats", response_model=StatsBlock)
def get_device_stats(
    device_id: str,
    db: Session = Depends(get_db),
    from_ts: datetime | None = Query(default=None, alias="from"),
    to_ts: datetime | None = Query(default=None, alias="to"),
) -> StatsBlock:
    st = stats_for_device(db, device_id, from_ts, to_ts)
    if st is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Нет выборок за указанный период")
    return StatsBlock(
        count=st.count,
        min=st.min_value,
        max=st.max_value,
        sum=st.sum_value,
        median=st.median_value,
    )


@router.post(
    "/{device_id}/stats/async",
    response_model=AsyncTaskAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def enqueue_device_stats(
    device_id: str,
    from_ts: datetime | None = Query(default=None, alias="from"),
    to_ts: datetime | None = Query(default=None, alias="to"),
) -> AsyncTaskAccepted:
    task = analyze_device_task.delay(
        device_id,
        from_ts.isoformat() if from_ts else None,
        to_ts.isoformat() if to_ts else None,
    )
    prefix = get_settings().api_v1_prefix
    return AsyncTaskAccepted(
        task_id=task.id,
        status_path=f"{prefix}/tasks/{task.id}",
    )
