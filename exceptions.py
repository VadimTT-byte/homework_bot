from venv import create


class ResponseNotEqualOK(Exception):
    """Ответ сервера не равен 200"""
    pass


class MessageNotSendError(Exception):
    """Не удалось отправить сообщение"""
    pass


class RequestError(Exception):
    """Ошибка при запросе к API"""
    pass


class UnregisteredStatus(Exception):
    """Незарегистрированный статус дом.работы"""
    pass