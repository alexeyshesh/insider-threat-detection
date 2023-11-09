from collections import defaultdict
from datetime import date, datetime
from enum import Enum

import networkx as nx
import pandas as pd


class CERTDatasetVersion(str, Enum):
    cert_3_2 = '3.2'


def _get_dataset_path(version: CERTDatasetVersion) -> str:
    return f'../data/r{version.value}/email.csv'


def get_cert_dataset_graph(
    version: CERTDatasetVersion = CERTDatasetVersion.cert_3_2,
    date_from: date | datetime = None,
    date_to: date | datetime = None,
) -> nx.Graph:
    path = open(_get_dataset_path(version))
    df = pd.read_csv(path)

    def date_filter(row):
        result = True
        if date_from is not None:
            result = result and datetime.strptime(row['date'], '%m/%d/%Y %H:%M:%S') > date_from
        if date_to is not None:
            result = result and datetime.strptime(row['date'], '%m/%d/%Y %H:%M:%S') < date_to
        return result

    if date_from or date_to:
        df = df[df.apply(date_filter, axis=1)]

    connections = defaultdict(int)

    for idx in df.index:
        email_from = df['from'][idx]
        email_to = df['to'][idx].split(';')
        for receiver in email_to:
            connections[(email_from, receiver)] += 1

    graph = nx.Graph()
    for (u, v), w in connections.items():
        graph.add_edge(u, v, weight=w)
    return graph

