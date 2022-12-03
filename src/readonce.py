"""
Read Once Object implementation in Python - Inspired by Secure by Design book.
"""

import inspect
from typing import Any, Iterable, List

__version__ = "1.0"


class UnsupportedOperationException(Exception):
    def __init__(self, *args: object) -> None:
        self.message = "Not allowed on sensitive value"
        super().__init__(self.message, *args)


class Final(type):
    def __new__(cls, name, bases, classdict):
        for b in bases:
            if b is not ReadOnce:
                raise TypeError("Subclassing final classes is restricted")
        return type.__new__(cls, name, bases, dict(classdict))


class ReadOnce(metaclass=Final):
    """
    Read-once object implementation; inspired by Secure by Design book
    """

    __secrets: List[str] = []

    @classmethod
    def __init__(cls) -> None:
        cls.__secrets = []

    @classmethod
    def __reset_secrets(cls) -> None:
        cls.__secrets = []

    def add_secret(self, *args):
        self.__reset_secrets()
        self.__secrets.append(*args)

    def get_secret(self):
        frame = inspect.currentframe()
        function_name = frame.f_back.f_code.co_name
        if function_name == "default":
            raise UnsupportedOperationException("Sensitive data can not be serialized")
        if self.__secrets:
            return self.__secrets.pop()
        raise UnsupportedOperationException("Sensitive data was already consumed")

    @property
    def secrets(self):
        return []

    def __getattribute__(self, __name: str) -> Any:
        frame = inspect.currentframe()
        # get the outer frame or caller frame
        function_name = frame.f_back.f_code.co_name
        if __name == "_ReadOnce__secrets" and function_name not in (
            "add_secret",
            "get_secret",
            "__len__",
        ):
            return []

        return super().__getattribute__(__name)

    def __setattr__(self, __name: str, __value: str) -> Any:
        frame = inspect.currentframe()
        # get the outer frame or caller frame
        function_name = frame.f_back.f_code.co_name

        if __name == "_ReadOnce__secrets" and function_name not in (
            "add_secret",
            "__init__",
        ):
            raise UnsupportedOperationException()

    def __dir__(self) -> Iterable[str]:
        return []

    def __str__(self) -> str:
        return f"{__class__.__name__}[secrets=*****]"

    def __repr__(self) -> str:
        return f"{__class__.__name__}[secrets=*****]"

    def __getstate__(self):
        raise UnsupportedOperationException()

    def __setstate__(self, value):
        raise UnsupportedOperationException()

    def __len__(self):
        return len(self.__secrets)
