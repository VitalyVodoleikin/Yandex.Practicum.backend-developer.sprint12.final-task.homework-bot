class CheckTokensError(Exception):
    """Ошибка при указании токенов."""


class RequestExceptError(Exception):
    """Ошибка запроса."""


class UnknownStatusError(Exception):
    """Неизвестный статус проверки работы."""


class UnsuccessfulHTTPStatusCodeError(Exception):
    """Статус-код ответа сервера не равен 200."""
