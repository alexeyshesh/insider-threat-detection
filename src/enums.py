from enum import Enum


class LogonEventType(str, Enum):
    login = 'logon'
    logout = 'logoff'
