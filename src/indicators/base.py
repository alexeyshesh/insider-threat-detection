from src.models import BaseEvent


class BaseIndicator:
    """
    Индикатор обрабатывает событие и говорит, является ли
    оно подорзительным
    """

    def process(self, event: BaseEvent) -> bool:
        raise NotImplemented
