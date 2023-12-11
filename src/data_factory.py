from datetime import datetime

from src.cert import CERTDataType, load_dataframe
from src.models import BaseEvent, LogonEvent, DeviceUsageEvent, FileCopyEvent


def row_to_event(dt: CERTDataType, row: dict) -> BaseEvent:
    if dt == CERTDataType.logon:
        return LogonEvent(
            event_id=row['id'],
            user_id=row['user'],
            timestamp=datetime.strptime(row['date'], '%m/%d/%Y %H:%M:%S'),
            type=row['activity'].lower(),
        )
    elif dt == CERTDataType.device:
        return DeviceUsageEvent(
            event_id=row['id'],
            user_id=row['user'],
            timestamp=datetime.strptime(row['date'], '%m/%d/%Y %H:%M:%S'),
        )
    elif dt == CERTDataType.file:
        return FileCopyEvent(
            event_id=row['id'],
            user_id=row['user'],
            timestamp=datetime.strptime(row['date'], '%m/%d/%Y %H:%M:%S'),
        )

    raise NotImplementedError


def get_data_stream(datatypes: list[CERTDataType]):
    # TODO: читать чанками, чтобы не перегружать память
    dfs = [(dt, load_dataframe(dt)) for dt in datatypes]

    streams = [
        [row_to_event(dt, row) for _, row in df.iterrows()]
        for (dt, df) in dfs
    ]

    merged = sorted(sum(streams, []), key=lambda x: x.timestamp)

    return list(merged)

