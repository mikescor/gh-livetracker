"""
Provides logger implementations.
"""
import wrapt


class Default:
    """
    Default console logger implementation.
    """

    def info(self, msg: str) -> None:
        print(f"[INFO] {msg}")

    def warn(self, msg: str) -> None:
        print(f"[WARN] {msg}")

    def error(self, msg: str) -> None:
        print(f"[ERROR] {msg}")

    def debug(self, msg: str) -> None:
        print(f"[DEBUG] {msg}")


LOGGER = wrapt.ObjectProxy(Default())


class Logger:
    """
    Logging adatapter. Adds prefix to all log messages.
    """

    def __init__(self, prefix: str):
        self.prefix = prefix

    def info(self, msg: str) -> None:
        LOGGER.info(f"{self.prefix} {msg}")

    def error(self, msg: str) -> None:
        LOGGER.error(f"{self.prefix} {msg}")

    def warn(self, msg: str) -> None:
        LOGGER.warn(f"{self.prefix} {msg}")

    def debug(self, msg: str) -> None:
        LOGGER.debug(f"{self.prefix} {msg}")


def get_logger(module: str = "") -> Logger:
    """
    Creates new logger with the prefix provided.

    Parameters:
    -----------
    * module: module name, used to profix all the log messages.

    Returns:
    --------

    New logger.
    """
    return Logger(f"module={module}")
