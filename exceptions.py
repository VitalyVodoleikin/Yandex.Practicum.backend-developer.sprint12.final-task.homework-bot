class UnsuccessfulHTTPStatusCodeError(Exception):
    """Статус-код ответа сервера не равен 200."""
    pass


class RequestExceptError(Exception):
    """Ошибка запроса."""
    pass


class EmptyDataError(Exception):
    """Пустой словарь или список."""
    pass


class UnknownStatusError(Exception):
    """Неизвестный статус проверки работы."""
    pass


class TelegramMsgError(Exception):
    """Ошибка отправки сообщения в Telegram."""
    pass
