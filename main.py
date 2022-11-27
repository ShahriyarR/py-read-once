import pickle
import json
import inspect
from typing import Iterable, List, Any
from custom_exceptions import UnsupportedOperationException

def _init_subclass(cls, *args, **kwargs) -> None:
    raise TypeError('Subclassing final classes is restricted')


def final(cls):
    """Marks class as `final`, so it won't have any subclasses."""
    setattr(  # noqa: B010
        cls, '__init_subclass__', classmethod(_init_subclass),
    )
    return cls



class ReadOnce:
    """
    Read-once object implementation; inspired by Secure by Design book
    """

    __secrets: List[str] = []

    def add_secret(self, *args):
        self.__secrets.append(*args)

    def get_secret(self):
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
        if __name == "_ReadOnce__secrets" and function_name not in ("add_secret", "get_secret"):
            return []

        return super().__getattribute__(__name)

    def __setattr__(self, __name: str, __value: str) -> Any:
        if __name == "_ReadOnce__secrets":
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

@final
class Password(ReadOnce):
    def __init__(self, password: str) -> None:
        super().__init__()
        self.add_secret(password)


if __name__ == "__main__":
    obj = Password("Awesome")
    print(obj.secrets)
    print(obj._ReadOnce__secrets)
    print(obj.__dict__)
    print(dir(obj))
    print(obj.get_secret())
    # print(obj.get_secret())
    json.dumps(obj)
    # pickle.dumps(obj)
    # obj._ReadOnce__secrets = "asdsada"







