class MemosCLIError(Exception):
    exit_code = 1


class ConfigError(MemosCLIError):
    exit_code = 4


class NetworkError(MemosCLIError):
    exit_code = 2


class APIError(MemosCLIError):
    exit_code = 1

    def __init__(self, status: int, message: str, payload=None):
        super().__init__(message)
        self.status = status
        self.payload = payload


class ArgumentError(MemosCLIError):
    exit_code = 3

