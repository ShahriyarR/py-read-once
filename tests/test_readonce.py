import pickle

import pytest

from readonce import UnsupportedOperationException


def test_finalized_class_can_not_be_subclassed(get_senstive_class):

    with pytest.raises(TypeError):

        class TryPassword(get_senstive_class):
            ...


def test_password_read_only_once(get_sensitive_obj):

    password = get_sensitive_obj.get_secret()

    assert password == "awesome_pass"

    with pytest.raises(UnsupportedOperationException):
        # Can not read password twice, because it is already consumed
        password = get_sensitive_obj.get_secret()


def test_if_can_pickle_the_secret_class(get_sensitive_obj):

    with pytest.raises(UnsupportedOperationException):
        pickle.dumps(get_sensitive_obj)


def test_direct_secrets_access_is_empty_list(get_sensitive_obj):
    assert get_sensitive_obj.secrets == []


def test_sensitive_class_dict_is_empty(get_sensitive_obj):
    assert get_sensitive_obj.__dict__ == {}


def test_sensitive_class_dir_output_is_empty(get_sensitive_obj):
    assert dir(get_sensitive_obj) == []
    assert get_sensitive_obj.__dir__() == []


def test_sensitive_class_super_class_secrets_is_empty(get_sensitive_obj):
    assert get_sensitive_obj._ReadOnce__secrets == []
    assert get_sensitive_obj.secrets == []


def test_len_of_secrets(get_senstive_class):
    obj = get_senstive_class("new_password")
    assert len(obj) == 1
    pass_ = obj.get_secret()
    assert len(obj) == 0
    assert pass_ == "new_password"
    with pytest.raises(UnsupportedOperationException):
        # Can not read password twice, because it is already consumed
        password = obj.get_secret()


def test_if_several_secrets_can_be_added(get_sensitive_obj):
    get_sensitive_obj.add_secret("new_secret")
    get_sensitive_obj.add_secret("new_secret2")
    assert len(get_sensitive_obj) == 1

    assert get_sensitive_obj.get_secret() == "new_secret2"


def test_if_class_str_and_repr_exposes_secrets(get_sensitive_obj):
    assert get_sensitive_obj.__str__() == "ReadOnce[secrets=*****]"
    assert get_sensitive_obj.__repr__() == "ReadOnce[secrets=*****]"
