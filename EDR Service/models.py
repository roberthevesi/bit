from pydantic import BaseModel


class Device(BaseModel):
    id: str
    os: str


class Time(BaseModel):
    a: int
    m: int


class File(BaseModel):
    file_hash: str
    file_path: str
    time: Time


class LastAccess(BaseModel):
    hash: str
    path: str
    pid: int


class Event(BaseModel):
    device: Device
    file: File
    last_access: LastAccess


class VerdictItem(BaseModel):
    hash: str
    risk_level: int = -1


class Verdict(BaseModel):
    file: VerdictItem
    process: VerdictItem
