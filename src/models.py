from datetime import datetime

from pydantic import BaseModel

from src.enums import LogonEventType


class BaseEvent(BaseModel):

    event_id: str
    user_id: str
    timestamp: datetime

    @property
    def weekday(self) -> int:
        return self.timestamp.weekday()

    @property
    def is_work_time(self) -> bool:
        return 8 < self.timestamp.hour < 18


class LogonEvent(BaseEvent):
    type: LogonEventType


class DeviceUsageEvent(BaseEvent):
    pass


class FileCopyEvent(BaseEvent):
    pass
