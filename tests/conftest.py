import pytest

from readonce import ReadOnce


class Password(ReadOnce):
    def __init__(self, password: str) -> None:
        super().__init__()
        self.add_secret(password)


@pytest.fixture
def get_senstive_class():
    return Password


@pytest.fixture(scope="function")
def get_sensitive_obj():
    return Password("awesome_pass")
