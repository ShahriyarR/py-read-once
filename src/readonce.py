"""
Read-Once Object implementation in Python - Inspired by Secure by Design book.
"""

import inspect
from typing import Any, Iterable, List, Optional

import icontract
from cryptography.fernet import Fernet

__version__ = "1.1.3"


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
    @icontract.ensure(
        lambda self: not self.secrets_ and not self.is_consumed_ and not self.key_
    )
    def __init__(self) -> None:
        self.secrets_: List[bytes] = []
        self.is_consumed_: bool = False
        self.key_: Optional[bytes] = None

    @property
    def secrets(self):
        return []

    @property
    def is_consumed(self):
        return None

    @property
    def key(self):
        return None

    def add_secret(self, secret: Any):
        def __get_token():
            key_ = Fernet.generate_key()
            fernet = Fernet(key_)
            return key_, fernet.encrypt(bytes(secret_, encoding="utf-8"))

        if self.is_consumed_:
            raise UnsupportedOperationException(
                "Sensitive object exhausted; you can not use it twice"
            )
        secret_ = str(secret)
        self.reset_secrets()
        self.reset_key()
        key, token = __get_token()
        self.update_key(key)
        if not self.key_:
            raise UnsupportedOperationException(
                "Missing encryption key; impossible to store the secret"
            )
        self.secrets_.append(token)

    def get_secret(self):
        frame = inspect.currentframe()
        # get two upper/back frame; one is getting back from icontract wrapper, second to get encoder default function
        function_name = frame.f_back.f_back.f_code.co_name
        if function_name == "default":
            raise UnsupportedOperationException("Sensitive data can not be serialized")
        if self.secrets_:
            self.update_is_consumed()
            if not self.is_consumed_:
                raise UnsupportedOperationException("Failed to set consumed flag")
            if not self.key_:
                raise UnsupportedOperationException(
                    "Missing encryption key; impossible decrypt the secret"
                )
            fernet = Fernet(self.key_)
            token = self.secrets_.pop()
            secret = fernet.decrypt(token)
            self.reset_key()
            return secret.decode(encoding="utf-8")
        raise UnsupportedOperationException("Sensitive data was already consumed")

    def __getattribute__(self, attr):
        frame = inspect.currentframe()
        # get the outer frame or caller frame
        function_name = frame.f_back.f_code.co_name

        if attr == "secrets_" and function_name not in (
            "add_secret",
            "get_secret",
            "reset_secrets",
            "__len__",
        ):
            return []

        if attr == "reset_secrets" and function_name not in (
            "add_secret",
            "__init__",
        ):
            raise UnsupportedOperationException()

        if attr == "is_consumed_" and function_name not in (
            "add_secret",
            "get_secret",
            "reset_is_consumed",
            "update_is_consumed",
            "__init__",
        ):
            return None

        if attr == "reset_is_consumed" and function_name not in ("__init__",):
            raise UnsupportedOperationException()

        if attr == "update_is_consumed" and function_name not in ("get_secret",):
            raise UnsupportedOperationException()

        if attr == "key_" and function_name not in (
            "add_secret",
            "get_secret",
            "update_key",
            "reset_key",
            "__init__",
        ):
            return None

        if attr == "reset_key" and function_name not in (
            "add_secret",
            "get_secret",
            "__init__",
        ):
            raise UnsupportedOperationException()

        if attr == "update_key" and function_name not in ("add_secret",):
            raise UnsupportedOperationException()

        return super().__getattribute__(attr)

    def __setattr__(self, attr: str, value: str) -> Any:
        frame = inspect.currentframe()
        # get the outer frame or caller frame
        function_name = frame.f_back.f_code.co_name
        if attr == "secrets_" and function_name not in (
            "add_secret",
            "reset_secrets",
            "__init__",
        ):
            raise UnsupportedOperationException()

        if attr == "is_consumed_" and function_name not in (
            "get_secret",
            "update_is_consumed",
            "__init__",
        ):
            raise UnsupportedOperationException()

        if attr == "key_" and function_name not in (
            "get_secret",
            "add_secret",
            "reset_key",
            "update_key",
            "__init__",
        ):
            raise UnsupportedOperationException()

        if attr == "get_secret":
            raise UnsupportedOperationException()

        if attr == "add_secret":
            raise UnsupportedOperationException()

        super().__setattr__(attr, value)

    def reset_secrets(self) -> None:
        self.secrets_ = []

    def reset_is_consumed(self):
        self.is_consumed_ = False

    def update_is_consumed(self):
        self.is_consumed_ = True

    def reset_key(self):
        self.key_ = None

    def update_key(self, key: bytes):
        self.key_ = key

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
        return 0

    def __dict__(self):
        return {}
