from collections import defaultdict, Counter
from datetime import datetime

import pandas as pd
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt


import numpy as np
import math
from sklearn.cluster import DBSCAN

def dt(timestamp: str) -> datetime:
    return datetime.strptime(timestamp, '%m/%d/%Y %H:%M:%S')


def build_dataset(version: str) -> pd.DataFrame:
    DATA_PATH = f'../data/r{version}/{{type}}.csv'
    ANSWERS_PATH = f'../data/answers/r{version}-{{attacker}}.csv'
    DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'

    logon_df = pd.read_csv(DATA_PATH.format(type='logon'))

    sessions = defaultdict(list)

    for _, row in logon_df.iterrows():
        user = row['user']
        ts = dt(row['date'])
        action = row['activity']

        if action == 'Logon':
            if sessions[user] and len(sessions[user][-1]) == 1:
                sessions[user][-1] = (sessions[user][-1][0], ts)
            sessions[user].append((ts,))
        else:
            if sessions[user] and len(sessions[user][-1]) == 2:
                sessions[user].append((None, ts))
            else:
                sessions[user][-1] = (sessions[user][-1][0], ts)

    actions_df = pd.concat(
        [
            logon_df,
            pd.read_csv(DATA_PATH.format(type='file')),
            pd.read_csv(DATA_PATH.format(type='device')),
        ],
        axis=0,
        ignore_index=True,
    )

    actions_df['timestamp'] = actions_df.apply(
        lambda x: dt(x['date']).strftime('%Y-%m-%dT%H:%M:%S'),
        axis=1,
    )

    def get_session_id(user: str, timestamp: datetime) -> str:
        for idx, (from_, to_) in enumerate(sessions[user]):
            if from_ is not None and (from_ <= timestamp <= to_):
                return f'{user}_{idx}'
            if from_ is None and to_ > timestamp:
                return f'{user}_{idx}'

    actions_df['session_id'] = actions_df.apply(
        lambda x: get_session_id(x['user'], dt(x['date'])),
        axis=1,
    )

    actions_df['filename'] = actions_df['filename'].fillna('')

    actions_df['file_activity'] = actions_df.apply(lambda x: int(bool(x['filename'])), axis=1)
    actions_df['device_activity'] = actions_df.apply(lambda x: int(x['activity'] in {'Connect', 'Disconnect'}), axis=1)

    sessions_df = actions_df.groupby(['user', 'session_id']).agg({'timestamp': ['min', 'max'], 'file_activity': ['max'], 'device_activity': ['max']}).reset_index()
    sessions_df.columns = ['user', 'session_id', 'session_start', 'session_end', 'file_activity', 'device_activity']

    def timestamp_to_minutes(timestamp: datetime) -> int:
        return (timestamp.hour * 60 + timestamp.minute) / (60 * 24)

    sessions_df['session_start_rlt'] = sessions_df.apply(
        lambda x: timestamp_to_minutes(datetime.strptime(x['session_start'], DATE_FORMAT)),
        axis=1,
    )
    sessions_df['session_end_rlt'] = sessions_df.apply(
        lambda x: timestamp_to_minutes(datetime.strptime(x['session_end'], DATE_FORMAT)),
        axis=1,
    )

    user_to_sessions = {
        user: sessions_df[sessions_df['user'] == user]
        for user in set(sessions_df['user'])
    }

    # используем DBSCAN
    malicios_sessions = set()
    for user, user_sessions_df in user_to_sessions.items():
        df = user_sessions_df.drop(
            ['user', 'session_id', 'session_start', 'session_end'],
            axis=1,
        )
        db = DBSCAN(eps=0.1, min_samples=5).fit(df)

        for session_id, pred in zip(user_sessions_df['session_id'], db.labels_):
            if pred == -1:
                malicios_sessions.add(session_id)

    filtered_sessions_df = sessions_df[sessions_df.apply(lambda x: x['session_id'] in malicios_sessions, axis=1)]
    target_ids = set()

    with open(ANSWERS_PATH.format(attacker=1)) as f1:
        for row in f1.readlines():
            if row.strip():
                target_ids.add(row.split(',')[1])

    insider_session_ids = set()

    for _, row in actions_df.iterrows():
        if str(row['id']) in target_ids:
            insider_session_ids.add(row['session_id'])

    filtered_actions_df = actions_df[actions_df.apply(lambda x: x['session_id'] in malicios_sessions, axis=1)]
    filtered_actions_df['target'] = filtered_actions_df.apply(lambda x: x['id'] in target_ids, axis=1)

    return filtered_actions_df










