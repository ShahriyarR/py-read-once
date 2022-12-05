import json
import re
from dataclasses import dataclass

import icontract
import pytest
from pydantic import BaseModel, validator

from readonce import ReadOnce


def validate_password(password: str) -> bool:
    reg = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"
    pattern = re.compile(reg)
    return bool(re.search(pattern, password))


def validate_password_length(password: str) -> bool:
    return len(password) > 7


class Password(ReadOnce):
    @icontract.ensure(lambda self: len(self) == 1, "Secret is missing")
    @icontract.require(
        lambda password: validate_password_length(password),
        "Password length should be more than 7",
    )
    def __init__(self, password: str) -> None:
        super().__init__()
        self.add_secret(password)


class DBUri(ReadOnce):
    def __init__(self, uri: str) -> None:
        super().__init__()
        self.add_secret(uri)


class DBPort(ReadOnce):
    def __init__(self, port: int) -> None:
        super().__init__()
        self.add_secret(port)


class DBHost(ReadOnce):
    def __init__(self, host: str) -> None:
        super().__init__()
        self.add_secret(host)


class CustomPasswordEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return {"password": obj.get_secret()}
        except AttributeError:
            return super().default(obj)


class CustomDBCredentialsEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            # Intentionally omit other fields
            return {"uri": obj.uri.get_secret()}
        except AttributeError:
            return super().default(obj)


@dataclass
class DBPassword(ReadOnce):
    password: str

    def __post_init__(self):
        # This is going to fail with "AttributeError: 'DBPassword' object has no attribute 'password'"
        self.add_secret(self.password)


@dataclass
class DBCredentialsWithDescriptors:
    password: Password = Password("db-password")
    uri: DBUri = DBUri("mysql://")
    port: DBPort = DBPort(3306)
    host: DBHost = DBHost("localhost")


@dataclass
class DBCredentials:
    password: Password
    uri: DBUri
    port: DBPort
    host: DBHost


class InvalidDBCredentialsModel(BaseModel):
    comment: str
    password: Password
    uri: DBUri
    port: DBPort
    host: DBHost

    @validator("password")
    def password_length_check(cls, v):
        passwd = v.get_secret()
        if len(passwd) > 7:
            v.add_secret(passwd)
            return v
        raise ValueError("Password length should be more than 7")

    class Config:
        arbitrary_types_allowed = True


class DBCredentialsModel(BaseModel):
    comment: str
    password: Password
    uri: DBUri
    port: DBPort
    host: DBHost

    class Config:
        arbitrary_types_allowed = True


@pytest.fixture
def get_password_class():
    return Password


@pytest.fixture
def get_custom_password_encoder():
    return CustomPasswordEncoder


@pytest.fixture
def get_custom_db_credentials_encoder():
    return CustomDBCredentialsEncoder


@pytest.fixture
def get_db_password_class():
    return DBPassword


@pytest.fixture
def get_db_credentials_with_desc_obj():
    return DBCredentialsWithDescriptors()


@pytest.fixture
def get_db_credentials_class():
    return DBCredentials


@pytest.fixture
def get_password_obj():
    return Password("awesome_pass")


@pytest.fixture
def get_db_uri_class():
    return DBUri


@pytest.fixture
def get_db_host_class():
    return DBHost


@pytest.fixture
def get_db_port():
    return DBPort


@pytest.fixture
def get_db_credentials_model():
    return DBCredentialsModel


@pytest.fixture
def get_invalid_db_credentials_model():
    return InvalidDBCredentialsModel
