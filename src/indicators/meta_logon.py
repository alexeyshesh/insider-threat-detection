from src.indicators.base import BaseIndicator
from src.indicators.worktime_logon import LogonWorkdayIndicator
from src.indicators.max_resource_usage import ResourceUsageMaxIndicator
from src.models import BaseEvent, LogonEvent, DeviceUsageEvent, FileCopyEvent


from src.indicators.base import BaseIndicator
from src.indicators.worktime_logon import LogonWorkdayIndicator
from src.indicators.max_resource_usage import ResourceUsageMaxIndicator
from src.models import BaseEvent, LogonEvent, DeviceUsageEvent, FileCopyEvent


class MetaLogonIndicator(BaseIndicator):

    def __init__(
        self,
        train_days: int = 90,
        workday_delta: int = 120,
        usage_interval: int = 120,
    ):
        self.logon_indicator = LogonWorkdayIndicator(
            delta=workday_delta,
            train_days=train_days,
        )
        self.device_usage_indicator = ResourceUsageMaxIndicator(
            event_class=DeviceUsageEvent,
            limit=usage_interval,
            train_days=train_days,
        )
        self.file_copy_indicator = ResourceUsageMaxIndicator(
            event_class=FileCopyEvent,
            limit=usage_interval,
            train_days=train_days,
        )
        self.last_logon_indicator_dict: dict[str, bool] = {}

    def process(self, event: BaseEvent) -> bool:

        val = False

        if isinstance(event, LogonEvent):
            val = self.logon_indicator.process(event)
            self.last_logon_indicator_dict[event.user_id] = val
            return False

        if isinstance(event, DeviceUsageEvent):
            val = self.device_usage_indicator.process(event)

        if isinstance(event, FileCopyEvent):
            val = self.file_copy_indicator.process(event)

        return self.last_logon_indicator_dict.get(event.user_id, False) and val

