import json
import pickle

import pytest

from readonce import UnsupportedOperationException


def test_finalized_class_can_not_be_subclassed(get_password_class):
    with pytest.raises(TypeError):

        class TryPassword(get_password_class):
            ...


def test_password_read_only_once(get_password_obj):
    password = get_password_obj.get_secret()

    assert password == "awesome_pass"

    with pytest.raises(UnsupportedOperationException):
        # Can not read password twice, because it is already consumed
        get_password_obj.get_secret()


def test_if_can_pickle_the_secret_class(get_password_obj):
    with pytest.raises(UnsupportedOperationException):
        pickle.dumps(get_password_obj)


def test_direct_secrets_access_is_empty_list(get_password_obj):
    assert get_password_obj.secrets == []


def test_direct_access_to_is_consumed_field(get_password_obj):
    assert get_password_obj.is_consumed is None
    assert get_password_obj._ReadOnce__is_consumed is None

    with pytest.raises(UnsupportedOperationException):
        get_password_obj._ReadOnce__is_consumed = True

    with pytest.raises(UnsupportedOperationException):
        get_password_obj._ReadOnce__update_is_consumed()


def test_direct__reset_is_consumed_call(get_password_obj):
    with pytest.raises(UnsupportedOperationException):
        get_password_obj._ReadOnce__reset_is_consumed()


def test_direct_reset_secrets_call(get_password_obj):
    with pytest.raises(UnsupportedOperationException):
        get_password_obj._ReadOnce__reset_secrets()


def test_sensitive_class_dict_is_empty(get_password_obj):
    assert get_password_obj.__dict__ == {}


def test_sensitive_class_dir_output_is_empty(get_password_obj):
    assert not dir(get_password_obj)
    assert get_password_obj.__dir__() == []


def test_sensitive_class_super_class_secrets_is_empty(get_password_obj):
    assert get_password_obj._ReadOnce__secrets == []
    assert get_password_obj.secrets == []


def test_len_of_secrets(get_password_class):
    obj = get_password_class("new_password")
    assert len(obj) == 1
    pass_ = obj.get_secret()
    assert len(obj) == 0
    assert pass_ == "new_password"
    with pytest.raises(UnsupportedOperationException):
        # Can not read password twice, because it is already consumed
        obj.get_secret()


def test_if_several_secrets_can_be_added(get_password_obj):
    get_password_obj.add_secret("new_secret")
    get_password_obj.add_secret("new_secret2")
    assert len(get_password_obj) == 1

    assert get_password_obj.get_secret() == "new_secret2"


def test_if_sensitive_object_can_be_used_after_consuming(get_password_obj):
    get_password_obj.get_secret()
    # It should fail to add new secret after consuming old one. Why?
    # Imagine you can read password then add back to secret then read it again???
    with pytest.raises(UnsupportedOperationException):
        get_password_obj.add_secret("new_secret")


def test_if_class_str_and_repr_exposes_secrets(get_password_obj):
    assert get_password_obj.__str__() == "ReadOnce[secrets=*****]"
    assert get_password_obj.__repr__() == "ReadOnce[secrets=*****]"


def test_if_sensitive_object_is_serializable(
    get_password_obj, get_custom_password_encoder
):
    # With custom encoder
    with pytest.raises(UnsupportedOperationException):
        json.dumps(get_password_obj, cls=get_custom_password_encoder)

    # Without custom encoder
    with pytest.raises(TypeError):
        json.dumps(get_password_obj)


def test_if_dataclass_field_can_be_used(get_db_password_class):
    # This should fail with: "AttributeError: 'DBPassword' object has no attribute 'password'"
    with pytest.raises(AttributeError) as err:
        db = get_db_password_class("db-password")


def test_use_sensitive_class_as_descriptor(get_db_credentials_with_desc_obj):
    db_port = get_db_credentials_with_desc_obj.port
    # Integers are converted to strings
    assert db_port.get_secret() == "3306"
    db_uri = get_db_credentials_with_desc_obj.uri
    assert db_uri.get_secret() == "mysql://"

    assert (
        get_db_credentials_with_desc_obj.__str__()
        == "DBCredentialsWithDescriptors(password=ReadOnce[secrets=*****], uri=ReadOnce[secrets=*****], port=ReadOnce[secrets=*****], host=ReadOnce[secrets=*****])"
    )
    # Again can not be read twice
    with pytest.raises(UnsupportedOperationException):
        db_uri.get_secret()


def test_use_sensitive_data_class(
    get_db_credentials_class,
    get_password_class,
    get_db_host_class,
    get_db_uri_class,
    get_db_port,
    get_custom_db_credentials_encoder,
):
    credentials = get_db_credentials_class(
        password=get_password_class("db-password"),
        uri=get_db_uri_class("mysql://"),
        host=get_db_host_class("localhost"),
        port=get_db_port(3306),
    )
    # Credentials are not exposed if somebody tries to log
    assert (
        credentials.__str__()
        == "DBCredentials(password=ReadOnce[secrets=*****], uri=ReadOnce[secrets=*****], port=ReadOnce[secrets=*****], "
        "host=ReadOnce[secrets=*****])"
    )

    assert credentials.password.get_secret() == "db-password"

    with pytest.raises(TypeError):
        json.dumps(credentials)

    # With custom encoder
    with pytest.raises(UnsupportedOperationException):
        json.dumps(credentials, cls=get_custom_db_credentials_encoder)

    with pytest.raises(TypeError):
        json.dumps(credentials.uri)

    # Can not be pickled
    with pytest.raises(UnsupportedOperationException):
        pickle.dumps(credentials)

    # Again can not be read twice
    with pytest.raises(UnsupportedOperationException):
        credentials.password.get_secret()


def test_use_sensitive_data_pydantic_model(
    get_db_credentials_model,
    get_password_class,
    get_db_host_class,
    get_db_uri_class,
    get_db_port,
):
    credentials = get_db_credentials_model(
        comment="The Hacked Database",
        password=get_password_class("db-password"),
        uri=get_db_uri_class("mysql://"),
        host=get_db_host_class("localhost"),
        port=get_db_port(3306),
    )
    assert credentials.password.get_secret() == "db-password"


def test_use_invalid_sensitive_data_pydantic_model(
    get_invalid_db_credentials_model,
    get_password_class,
    get_db_host_class,
    get_db_uri_class,
    get_db_port,
):
    with pytest.raises(UnsupportedOperationException):
        get_invalid_db_credentials_model(
            comment="The Hacked Database",
            password=get_password_class("db-password"),  # valid length password
            uri=get_db_uri_class("mysql://"),
            host=get_db_host_class("localhost"),
            port=get_db_port(3306),
        )


def test_monkeypatch_get_secret(get_password_obj, monkeypatch):
    def mock_return():
        return "12345"

    get_password_obj.add_secret("new_secret")
    monkeypatch.setattr(get_password_obj, "get_secret", mock_return)
    # the original secret was not affected
    assert get_password_obj.get_secret() != mock_return()


def test_monkeypatch_add_secret(get_password_obj, monkeypatch):
    def mock_return():
        return "12345"

    # basically has no effect on add_secret
    monkeypatch.setattr(get_password_obj, "add_secret", mock_return)
    get_password_obj.add_secret("fake")
    monkeypatch.setattr(get_password_obj, "get_secret", mock_return)
    # the original secret was not affected
    assert get_password_obj.get_secret() != mock_return()


def test_monkeypatch_change_secrets_property(get_password_obj, monkeypatch):
    # It has no effect either for the secrets property
    monkeypatch.setattr(get_password_obj, "secrets", ["12345"])
    # Still original secret is there
    assert get_password_obj.get_secret() != "12345"


def test_monkeypatch_change_secrets_storage(get_password_obj, monkeypatch):
    # Directly trying to monkeypatch will raise double UnsupportedOperationException;
    # As monkeypatch in its default undo() section tries to again edit "_ReadOnce__secrets" which raises same exception
    # That's why we use context() below

    # with pytest.raises(UnsupportedOperationException):
    #     monkeypatch.setattr(get_password_obj, "_ReadOnce__secrets", ["12345"], raising=False)

    with pytest.raises(UnsupportedOperationException):
        with monkeypatch.context() as m:
            m.setattr(get_password_obj, "_ReadOnce__secrets", ["12345"], raising=True)


def test_direct_access_to_key_field(get_password_obj):
    assert get_password_obj.key is None
    assert get_password_obj._ReadOnce__key is None

    with pytest.raises(UnsupportedOperationException):
        get_password_obj._ReadOnce__key = b"new key"

    with pytest.raises(UnsupportedOperationException):
        get_password_obj._ReadOnce__update_key(b"new key")

    with pytest.raises(UnsupportedOperationException):
        get_password_obj._ReadOnce__reset_key()


def test_monkeypatch_the_key(get_password_obj, monkeypatch):
    get_password_obj.add_secret("new_secret")

    with pytest.raises(UnsupportedOperationException):
        with monkeypatch.context() as m:
            m.setattr(get_password_obj, "_ReadOnce__key", None)
