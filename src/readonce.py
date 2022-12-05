"""
Read-Once Object implementation in Python - Inspired by Secure by Design book.
"""

import inspect
from typing import Any, Iterable, List

import icontract

__version__ = "1.0.2"


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


@icontract.invariant(
    lambda self: len(self) == 0 or len(self) == 1,
    "There can be no or only single secret data stored",
)
class ReadOnce(metaclass=Final):
    """
    Read-once object implementation:
    * Sensitive data can be added only using add_secret
    * Sensitive data can be read only once
    * Sensitive class - inherited from ReadOnce can not be further subclassed
    * Sensitive data can not be pickled
    * Sensitive data can not be JSON serialized
    * All properties, fields are hidden and can not be accessed directly - even from subclass
    * The secrets can not be updated directly from outside - even from subclass
    """

    __secrets: List[str] = []
    __is_consumed: bool = False

    @icontract.ensure(lambda self: not self.__secrets and not self.__is_consumed)
    def __init__(self) -> None:
        self.__reset_secrets()
        self.__reset_is_consumed()

    @classmethod
    def __reset_secrets(cls) -> None:
        cls.__secrets = []

    @classmethod
    def __reset_is_consumed(cls):
        cls.__is_consumed = False

    @classmethod
    def __update_is_consumed(cls):
        cls.__is_consumed = True

    def add_secret(self, *args):
        if self.__is_consumed:
            raise UnsupportedOperationException(
                "Sensitive object exhausted; you can not use it twice"
            )
        self.__reset_secrets()
        self.__secrets.append(*args)

    def get_secret(self):
        frame = inspect.currentframe()
        # get two upper/back frame; one is getting back from icontract wrapper, second to get encoder default function
        function_name = frame.f_back.f_back.f_code.co_name
        if function_name == "default":
            raise UnsupportedOperationException("Sensitive data can not be serialized")
        if self.__secrets:
            self.__update_is_consumed()
            return self.__secrets.pop()
        raise UnsupportedOperationException("Sensitive data was already consumed")

    @property
    def secrets(self):
        return []

    @property
    def is_consumed(self):
        return None

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

        if __name == "_ReadOnce__is_consumed" and function_name not in (
            "add_secret",
            "get_secret",
            "__init__",
        ):
            return None

        if __name == "_ReadOnce__update_is_consumed" and function_name not in (
            "get_secret",
        ):
            raise UnsupportedOperationException()

        if __name == "_ReadOnce__reset_secrets" and function_name not in (
            "add_secret",
            "__init__",
        ):
            raise UnsupportedOperationException()

        if __name == "_ReadOnce__reset_is_consumed" and function_name not in (
            "__init__",
        ):
            raise UnsupportedOperationException()

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

        if __name == "_ReadOnce__is_consumed" and function_name not in (
            "get_secret",
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
