import json

import pytest

from readonce import ReadOnce


class Password(ReadOnce):
    def __init__(self, password: str) -> None:
        super().__init__()
        self.add_secret(password)


class CustomPasswordEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return {"password": obj.get_secret()}
        except AttributeError:
            return super().default(obj)


@pytest.fixture
def get_sensitive_class():
    return Password


@pytest.fixture
def get_custom_encoder():
    return CustomPasswordEncoder


@pytest.fixture(scope="function")
def get_sensitive_obj():
    return Password("awesome_pass")
