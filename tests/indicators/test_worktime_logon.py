from datetime import datetime

from src.indicators.worktime_logon import (
    LogonEvent,
    LogonEventType,
    LogonWorkdayIndicator,
)


def test_logon_workday_indicator():
    delta = 15
    user_id = 'xyz'

    train_data = [
        (datetime(2023, 1, 1, 8, 0, 0), LogonEventType.login),
        (datetime(2023, 1, 1, 18, 0, 0), LogonEventType.logout),
        (datetime(2023, 1, 2, 7, 55, 0), LogonEventType.login),
        (datetime(2023, 1, 2, 10, 55, 0), LogonEventType.login),  # не первый вход
        (datetime(2023, 1, 2, 18, 5, 0), LogonEventType.logout),
        (datetime(2023, 1, 3, 8, 5, 0), LogonEventType.login),
        (datetime(2023, 1, 3, 15, 55, 0), LogonEventType.logout),  # не последний выход
        (datetime(2023, 1, 3, 17, 55, 0), LogonEventType.logout),
        (datetime(2023, 1, 4, 8, 0, 0), LogonEventType.login),
        (datetime(2023, 1, 4, 18, 0, 0), LogonEventType.logout),
    ]
    test_data = [
        ((datetime(2023, 2, 1, 7, 46, 0), LogonEventType.login), False),
        ((datetime(2023, 2, 1, 18, 13, 0), LogonEventType.logout), False),

        ((datetime(2023, 2, 2, 8, 45, 0), LogonEventType.login), False),
        ((datetime(2023, 2, 2, 15, 45, 0), LogonEventType.logout), False),

        ((datetime(2023, 2, 3, 6, 50, 0), LogonEventType.login), True),
        ((datetime(2023, 2, 3, 22, 45, 0), LogonEventType.logout), True),
    ]

    i = LogonWorkdayIndicator(delta=delta, train_days=15)

    for idx, (timestamp, event_type) in enumerate(train_data):
        i.process(
            LogonEvent(
                event_id=str(idx),
                user_id=user_id,
                timestamp=timestamp,
                type=event_type,
            ),
        )
        print(i.user_to_avg_logon_map)

    assert i.user_to_avg_logon_map[user_id].avg_first_login == 8 * 60  # 8:00
    assert i.user_to_avg_logon_map[user_id].avg_last_logout == 18 * 60  # 18:00

    for idx, ((timestamp, event_type), expected_val) in enumerate(
        test_data,
        start=len(train_data)
    ):
        val = i.process(
            LogonEvent(
                event_id=str(idx),
                user_id=user_id,
                timestamp=timestamp,
                type=event_type,
            ),
        )

        assert val == expected_val, f'Expected {expected_val} for event {idx}'
