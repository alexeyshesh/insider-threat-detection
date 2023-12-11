from datetime import datetime, timedelta

from pydantic import BaseModel

from src.models import BaseEvent


class ResourceUsageRecord(BaseModel):

    last_events: list[datetime] = []
    max_val: int = 0

    @property
    def cur_val(self) -> int:
        return len(self.last_events)

    def add_event(
        self,
        timestamp: datetime,
        limit: int,
        is_train: bool,
    ):
        self.last_events.append(timestamp)
        self.last_events = [
            x for x in self.last_events
            if x > timestamp - timedelta(minutes=limit)
        ]

        if is_train and len(self.last_events) > self.max_val:
            self.max_val = len(self.last_events)


class ResourceUsageMaxIndicator:
    """
    Индикатор будет показывать статистические выбросы по данным использования
    внешних устройств
    """

    def __init__(self, event_class: type, limit: int = 60, train_days: int = 30):
        self.limit = limit
        self.train_days = train_days
        self.event_class = event_class

        self.usage: dict[str, ResourceUsageRecord] = {}
        self.first_day = None

    def process(self, event: BaseEvent) -> bool:

        if self.first_day is None:
            self.first_day = event.timestamp.date()

        if not isinstance(event, self.event_class):
            return False

        if event.user_id not in self.usage:
            self.usage[event.user_id] = ResourceUsageRecord()


        is_train = (event.timestamp.date() - self.first_day).days < self.train_days

        self.usage[event.user_id].add_event(
            timestamp=event.timestamp,
            limit=self.limit,
            is_train=is_train,
        )

        return (
            not is_train
            and self.usage[event.user_id].cur_val > self.usage[event.user_id].max_val
        )
