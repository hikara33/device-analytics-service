from dataclasses import dataclass
from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import Select, func, select, text
from sqlalchemy.orm import Session

from app.models.models import DeviceSample, UserDevice


@dataclass(frozen=True)
class MagnitudeStats:
    count: int
    min_value: float
    max_value: float
    sum_value: float
    median_value: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "min": self.min_value,
            "max": self.max_value,
            "sum": self.sum_value,
            "median": self.median_value,
        }


def _device_sample_filters(
    device_id: str,
    from_ts: datetime | None,
    to_ts: datetime | None,
) -> list[Any]:
    conds: list[Any] = [DeviceSample.device_id == device_id]
    if from_ts is not None:
        conds.append(DeviceSample.created_at >= from_ts)
    if to_ts is not None:
        conds.append(DeviceSample.created_at <= to_ts)
    return conds


def stats_for_device(
    db: Session,
    device_id: str,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
) -> MagnitudeStats | None:
    conds = _device_sample_filters(device_id, from_ts, to_ts)
    count_q = select(func.count()).select_from(DeviceSample).where(*conds)
    count = db.execute(count_q).scalar_one()
    if count == 0:
        return None

    agg = db.execute(
        select(
            func.min(DeviceSample.magnitude),
            func.max(DeviceSample.magnitude),
            func.sum(DeviceSample.magnitude),
        ).where(*conds)
    ).one()

    median_row = db.execute(
        text(
            """
            SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY magnitude)
            FROM device_samples
            WHERE device_id = :device_id
            AND (:from_ts IS NULL OR created_at >= :from_ts)
            AND (:to_ts IS NULL OR created_at <= :to_ts)
            """
        ),
        {
            "device_id": device_id,
            "from_ts": from_ts,
            "to_ts": to_ts,
        },
    ).one()

    return MagnitudeStats(
        count=int(count),
        min_value=float(agg[0]),
        max_value=float(agg[1]),
        sum_value=float(agg[2]),
        median_value=float(median_row[0]),
    )


def stats_for_user_devices_aggregate(
    db: Session,
    user_id: int,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
) -> MagnitudeStats | None:
    subq: Select[Any] = (
        select(DeviceSample.magnitude)
        .join(
            UserDevice,
            (UserDevice.device_id == DeviceSample.device_id) & (UserDevice.user_id == user_id),
        )
        .where(UserDevice.user_id == user_id)
    )
    if from_ts is not None:
        subq = subq.where(DeviceSample.created_at >= from_ts)
    if to_ts is not None:
        subq = subq.where(DeviceSample.created_at <= to_ts)

    subq = subq.subquery()
    count_q = select(func.count()).select_from(subq)
    count = db.execute(count_q).scalar_one()
    if count == 0:
        return None

    agg = db.execute(
        select(
            func.min(subq.c.magnitude),
            func.max(subq.c.magnitude),
            func.sum(subq.c.magnitude),
        )
    ).one()

    median_sql = text(
        """
        SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY d.magnitude)
        FROM device_samples d
        INNER JOIN user_devices ud ON ud.device_id = d.device_id AND ud.user_id = :user_id
        WHERE (:from_ts IS NULL OR d.created_at >= :from_ts)
        AND (:to_ts IS NULL OR d.created_at <= :to_ts)
        """
    )
    median_row = db.execute(
        median_sql,
        {"user_id": user_id, "from_ts": from_ts, "to_ts": to_ts},
    ).one()

    return MagnitudeStats(
        count=int(count),
        min_value=float(agg[0]),
        max_value=float(agg[1]),
        sum_value=float(agg[2]),
        median_value=float(median_row[0]),
    )


def stats_per_device_for_user(
    db: Session,
    user_id: int,
    from_ts: datetime | None = None,
    to_ts: datetime | None = None,
) -> list[dict[str, Any]]:
    devices = db.execute(
        select(UserDevice.device_id).where(UserDevice.user_id == user_id).order_by(UserDevice.device_id)
    ).scalars().all()

    out: list[dict[str, Any]] = []
    for dev in devices:
        st = stats_for_device(db, dev, from_ts, to_ts)
        if st is not None:
            out.append({"device_id": dev, "stats": st.as_dict()})
        else:
            out.append({"device_id": dev, "stats": None})
    return out
