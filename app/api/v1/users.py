from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.models.models import User, UserDevice
from app.schemas.schemas import AsyncTaskAccepted, StatsBlock, UserCreate, UserDeviceLink, UserDeviceOut, UserOut
from app.services.stats import stats_for_user_devices_aggregate, stats_per_device_for_user
from app.tasks.stats_tasks import analyze_user_aggregate_task

router = APIRouter()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    user = User(username=body.username.strip())
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким именем уже существует",
        ) from None
    db.refresh(user)
    return user


@router.post("/{user_id}/devices", response_model=UserDeviceOut, status_code=status.HTTP_201_CREATED)
def link_device_to_user(
    user_id: int,
    body: UserDeviceLink,
    db: Session = Depends(get_db),
) -> UserDeviceOut:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    row = UserDevice(user_id=user_id, device_id=body.device_id.strip())
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Устройство уже привязано к этому пользователю",
        ) from None
    db.refresh(row)
    return row


@router.get("/{user_id}/stats", response_model=StatsBlock)
def get_user_aggregate_stats(
    user_id: int,
    db: Session = Depends(get_db),
    from_ts: datetime | None = Query(default=None, alias="from"),
    to_ts: datetime | None = Query(default=None, alias="to"),
) -> StatsBlock:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    st = stats_for_user_devices_aggregate(db, user_id, from_ts, to_ts)
    if st is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Нет выборок по устройствам пользователя")
    return StatsBlock(
        count=st.count,
        min=st.min_value,
        max=st.max_value,
        sum=st.sum_value,
        median=st.median_value,
    )


@router.get("/{user_id}/stats/per-device")
def get_user_stats_per_device(
    user_id: int,
    db: Session = Depends(get_db),
    from_ts: datetime | None = Query(default=None, alias="from"),
    to_ts: datetime | None = Query(default=None, alias="to"),
) -> list[dict]:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return stats_per_device_for_user(db, user_id, from_ts, to_ts)


@router.post(
    "/{user_id}/stats/async",
    response_model=AsyncTaskAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def enqueue_user_aggregate_stats(
    user_id: int,
    from_ts: datetime | None = Query(default=None, alias="from"),
    to_ts: datetime | None = Query(default=None, alias="to"),
) -> AsyncTaskAccepted:
    task = analyze_user_aggregate_task.delay(
        user_id,
        from_ts.isoformat() if from_ts else None,
        to_ts.isoformat() if to_ts else None,
    )
    prefix = get_settings().api_v1_prefix
    return AsyncTaskAccepted(
        task_id=task.id,
        status_path=f"{prefix}/tasks/{task.id}",
    )
