from pydantic import BaseModel


class DeviceDataCreate(BaseModel):
    device_id: str
    x: float
    y: float
    z: float