from datetime import date, datetime

from pydantic import BaseModel

from src.enums import LogonEventType
from src.models import BaseEvent, LogonEvent

from src.indicators.base import BaseIndicator


class UserLogonRecord(BaseModel):
    avg_first_login: float | None = None
    avg_last_logout: float | None = None

    last_logout: datetime | None = None
    last_login: datetime | None = None

    login_count: int = 0
    logout_count: int = 0

    def add_event(self, type: LogonEventType, timestamp: datetime):
        if type == LogonEventType.login:
            self.add_login(timestamp)
        elif type == LogonEventType.logout:
            self.add_logout(timestamp)
        else:
            raise TypeError(f'Unknown event type {type}')

    def add_login(self, timestamp: datetime):
        mins = timestamp.hour * 60 + timestamp.minute

        if self.login_count == 0:
            self.avg_first_login = mins
            self.login_count = 1
            self.last_login = timestamp
            return

        assert self.avg_first_login is not None and self.last_login is not None

        if self.last_login.date() == timestamp.date():
            return

        self.avg_first_login = (
            (self.avg_first_login * self.login_count + mins)
            / (self.login_count + 1)
        )
        self.last_login = timestamp
        self.login_count += 1

    def add_logout(self, timestamp: datetime):
        if self.logout_count == 0:
            if self.last_logout is None or timestamp.date() == self.last_logout.date():
                self.last_logout = timestamp
            else:
                self.avg_last_logout = self.last_logout.hour * 60 + self.last_logout.minute
                self.last_logout = timestamp
                self.logout_count = 1
            return

        assert self.last_logout is not None and self.avg_last_logout is not None

        if timestamp.date() == self.last_logout.date():
            self.last_logout = timestamp
            return

        mins = self.last_logout.hour * 60 + self.last_logout.minute
        self.avg_last_logout = (
            (self.avg_last_logout * self.logout_count + mins)
            / (self.logout_count + 1)
        )
        self.last_logout = timestamp
        self.logout_count += 1


class LogonWorkdayIndicator(BaseIndicator):
    """
    Горит, если человек зашел во время, сильно отличающееся от оббычного времени входа

    Хранит для каждого человека отображение user_id -> (avg_login, avg_logoff)

    В первом поле храним первое время входа за день
    Во втором последнее. Индикатор горит, если первое время входа сильно меньше обычного первого,
    или если произошел вход/выход во время, сильно отличающееся от обычного
    """

    def __init__(self, delta: int = 15, train_days: int = 30):
        self.delta = delta
        self.train_days = train_days
        self.user_to_avg_logon_map: dict[str, UserLogonRecord] = {}
        self.first_day: date | None = None

    def process(self, event: BaseEvent) -> bool:
        if not isinstance(event, LogonEvent):
            return False

        if self.first_day is None:
            self.first_day = event.timestamp.date()

        if event.user_id not in self.user_to_avg_logon_map:
            self.user_to_avg_logon_map[event.user_id] = UserLogonRecord()

        record = self.user_to_avg_logon_map[event.user_id]

        if (
            (event.timestamp.date() - self.first_day).days < self.train_days
            or record.avg_first_login is None
            or record.avg_last_logout is None
        ):
            self.user_to_avg_logon_map[event.user_id].add_event(event.type, event.timestamp)
            return False

        mins = event.timestamp.hour * 60 + event.timestamp.minute
        if (
            event.type == LogonEventType.login and mins < record.avg_first_login - self.delta
            or event.type == LogonEventType.logout and mins > record.avg_last_logout + self.delta
        ):
            return True

        self.user_to_avg_logon_map[event.user_id].add_event(event.type, event.timestamp)
        return False
