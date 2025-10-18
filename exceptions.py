class UnsuccessfulHTTPStatusCodeError(Exception):
    """Статус-код ответа сервера не равен 200."""


class RequestExceptError(Exception):
    """Ошибка запроса."""


class EmptyDataError(Exception):
    """Пустой словарь или список."""


class UnknownStatusError(Exception):
    """Неизвестный статус проверки работы."""


class TelegramMsgError(Exception):
    """Ошибка отправки сообщения в Telegram."""
