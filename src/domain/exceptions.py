class NotFoundException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class ConflictException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class InvalidInputException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class UnauthorizedException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class InfrastructureException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)
