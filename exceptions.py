from venv import create


class ResponseNotEqualOK(Exception):
    """Ответ сервера не равен 200"""
    pass
