import logging

from src.domain.interfaces import LogProvider


class LogProviderInfrastructure(LogProvider):
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("app-logger")

    def info_log(self, message: str, context: str | None = None):
        full_message = f"{message} | Context: {context}" if context else message
        self.logger.info(full_message)

    def error_log(self, message: str, context: str | None = None):
        full_message = f"{message} | Context: {context}" if context else message
        self.logger.error(full_message)
