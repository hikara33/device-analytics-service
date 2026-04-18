from datetime import datetime

from pydantic import BaseModel, Field


class SampleIn(BaseModel):
    x: float
    y: float
    z: float
    recorded_at: datetime | None = None


class SampleOut(BaseModel):
    id: int
    device_id: str
    x: float
    y: float
    z: float
    magnitude: float
    created_at: datetime

    model_config = {"from_attributes": True}


class StatsBlock(BaseModel):
    count: int
    min: float
    max: float
    sum: float
    median: float


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=255)


class UserOut(BaseModel):
    id: int
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserDeviceLink(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=255)


class UserDeviceOut(BaseModel):
    id: int
    user_id: int
    device_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AsyncTaskAccepted(BaseModel):
    task_id: str
    status_path: str


class TaskStatusOut(BaseModel):
    task_id: str
    state: str
    result: StatsBlock | dict | None = None
    error: str | None = None
