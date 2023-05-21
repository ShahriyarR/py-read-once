# What is Read-Once object?

This concept is defined and explained in [Secure by Design](https://www.manning.com/books/secure-by-design) book.

It is also exposed in this link [LiveBook](https://livebook.manning.com/concept/security/read-once-object).

The overall characteristics of Read-Once objects, grabbed from [Book Review: Secure by Design](https://adriancitu.com/tag/read-once-object-pattern/)

```
Read-once objects

A read-once object is an object designed to be read once (or a limited number of times). This object usually represents a value or concept in your domain that’s considered to be sensitive (for example, passport numbers, credit card numbers, or passwords). The main purpose of the read-once object is to facilitate detection of unintentional use of the data it encapsulates.

Here’s a list of the key aspects of a read-once object:

    Its main purpose is to facilitate detection of unintentional use.
    It represents a sensitive value or concept.
    It’s often a domain primitive.
    Its value can be read once, and once only.
    It prevents serialization of sensitive data.
    It prevents sub-classing and extension.
```

# About the Usage

Imagine that you need to pass a password it to some kind of service, which is going to Login your user.
The Login service will only require this password only once, so why not to restrict it to be read, used only Once?

# Important information

The ReadOnce object is not a cryptography library. 
It is not responsible for encrypting/decrypting or dictating any type of cryptography methods to store and retrieve your secrets.

The main idea behind the ReadOnce objects is hardening the access and allow only one time access to the stored secrets in the object.

Question: Are the secrets stored in plain text?
Answer: No, we use symmetric encryption from cryptography named [Fernet](https://cryptography.io/en/latest/fernet/).
And we store passed secret data internally as so called fernet token(ciphertext+hash value).
When you try to retrieve the secret back, it is decrypted with the same key and send back as a plain text.

Question: Then we have an encryption+hashing of plaintext?
Answer: Yes, but ReadOnce class expects already encrypted(+ peppered, salted, hashed etc.) string to be passed as a secret, 
because when you retrieve the secret it will return what it was originally passed. 
If you passed the secret as "12345" you will get back "12345".
If you passed the secret something like "HmDVbz6N3MlXqZ4q3TvLakMQ9fQjI45yhuoRHyZWiM4=" you will get back the same string.

Question: Then why you store the secret as a token(ciphertext+hash value)?
Answer: It is an extra layer of hardening, if somehow, somebody could get the ReadOnce object and tries to steal the secret, lovely attacker should also have the key.
Okay the key also stored in ReadOnce object, but it is a non-trivial to get the key back. 
If the attacker tries to add new secret over old one, the encryption key also updated.


### Install using pip:

`pip install readonce`

Then just inherit from the `ReadOnce`:

```py
from readonce import ReadOnce


class Password(ReadOnce):
    def __init__(self, password: str) -> None:
        super().__init__()
        self.add_secret(password)

```

Here the password string is added as a secret. 
From our definition it can be read only once and only using `get_secret()`, no direct access to the secret.

* You can not expose the object properties as well:

```py
>>> obj = Password(password="awesome_password")
>>> dir(obj)
[]
>>> obj.__dict__
{}
```

* Trying to read the password twice:

```py
>>> obj.get_secret()
'awesome_password'
>>> obj.get_secret()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/shako/REPOS/py-read-once/.venv/lib/python3.10/site-packages/readonce.py", line 47, in get_secret
    raise UnsupportedOperationException("Sensitive data was already consumed")
readonce.UnsupportedOperationException: ('Not allowed on sensitive value', 'Sensitive data was already consumed')
```

* If someone tries to add its own secret to already instantiated object and then get back already defined secret data(original secret),
it will get only new secret.

```py
>>> obj = Password(password="awesome_password")
>>> obj.add_secret("new_fake_date")
>>> obj.get_secret()
'new_fake_date'
>>> obj.get_secret()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/shako/REPOS/py-read-once/.venv/lib/python3.10/site-packages/readonce.py", line 47, in get_secret
    raise UnsupportedOperationException("Sensitive data was already consumed")
readonce.UnsupportedOperationException: ('Not allowed on sensitive value', 'Sensitive data was already consumed')
```

* You cannot create a subclass from sensitive class, it is a way of expose parent class data, but no success:

```py
>>> class FakePassword(Password):
...     ...
... 
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/shako/REPOS/py-read-once/.venv/lib/python3.10/site-packages/readonce.py", line 21, in __new__
    raise TypeError("Subclassing final classes is restricted")
TypeError: Subclassing final classes is restricted
```

* If somebody tries to access secrets directly:

```py
>>> obj.secrets
[]
>>> obj._ReadOnce__secrets
[]
```

* You can not pickle it:

```py
>>> import pickle
>>> pickle.dumps(obj)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/shako/REPOS/py-read-once/.venv/lib/python3.10/site-packages/readonce.py", line 87, in __getstate__
    raise UnsupportedOperationException()
readonce.UnsupportedOperationException: Not allowed on sensitive value
```

* You can not JSON serialize it:

With default encoder:

```py
>>> import json

>>> json.dumps(obj)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/usr/lib/python3.10/json/__init__.py", line 231, in dumps
    return _default_encoder.encode(obj)
  File "/usr/lib/python3.10/json/encoder.py", line 199, in encode
    chunks = self.iterencode(o, _one_shot=True)
  File "/usr/lib/python3.10/json/encoder.py", line 257, in iterencode
    return _iterencode(o, 0)
  File "/usr/lib/python3.10/json/encoder.py", line 179, in default
    raise TypeError(f'Object of type {o.__class__.__name__} '
TypeError: Object of type Password is not JSON serializable
```

With custom encoder:

```py
class CustomPasswordEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return {"password": obj.get_secret()}
        except AttributeError:
            return super().default(obj)
```

```py
>>> json.dumps(obj, cls=CustomPasswordEncoder)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/usr/lib/python3.10/json/__init__.py", line 238, in dumps
    **kw).encode(obj)
  File "/usr/lib/python3.10/json/encoder.py", line 199, in encode
    chunks = self.iterencode(o, _one_shot=True)
  File "/usr/lib/python3.10/json/encoder.py", line 257, in iterencode
    return _iterencode(o, 0)
  File "<stdin>", line 4, in default
  File "/home/shako/REPOS/py-read-once/.venv/lib/python3.10/site-packages/readonce.py", line 48, in get_secret
    raise UnsupportedOperationException("Sensitive data can not be serialized")
readonce.UnsupportedOperationException: ('Not allowed on sensitive value', 'Sensitive data can not be serialized')
```

* At some points the class itself can be silently dumped to logs, but not here:

```py
>>> obj = Password(password="awesome_password")
>>> print(obj)
ReadOnce[secrets=*****]
>>> obj
ReadOnce[secrets=*****]
```

# How about Python [Dataclasses](https://docs.python.org/3.10/library/dataclasses.html)?

Regarding dataclasses, it is prohibited to directly define field then add it to secret:

```py
from readonce import ReadOnce
from dataclasses import dataclass

@dataclass
class DBPassword(ReadOnce):
    password: str
    def __post_init__(self):
        # This is going to fail with "AttributeError: 'DBPassword' object has no attribute 'password'"
        self.add_secret(self.password)
```

The result will be:

```py
DBPassword(password="awesome")
...
AttributeError: 'DBPassword' object has no attribute 'password'
```

The better way either to use fields as a "descriptor" way. 
Imagine you have an idea to share your database credentials in whole chunk. 
We can create separate sensitive data holders or secrets for each information:

```py
from readonce import ReadOnce

class Password(ReadOnce):
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
```

Then we can combine them in one dataclass:

```py
@dataclass
class DBCredentialsWithDescriptors:
    password: Password = Password("db-password")
    uri: DBUri = DBUri("mysql://")
    port: DBPort = DBPort(3306)
    host: DBHost = DBHost("localhost")
```

In this way, further we can get our secrets back, again using `get_secret()` and only once:

```py
>>> credentials = DBCredentialsWithDescriptors()
>>> credentials.password.get_secret()
'db-password'

>>> credentials.password.get_secret()
...
readonce.UnsupportedOperationException: ('Not allowed on sensitive value', 'Sensitive data was already consumed')
```

Printing or dumping credentials object will not give any valuable information as well:

```py
>>> print(credentials)
DBCredentialsWithDescriptors(password=ReadOnce[secrets=*****], uri=ReadOnce[secrets=*****], port=ReadOnce[secrets=*****], host=ReadOnce[secrets=*****])
```

Okay, this not a full "descriptors" in terms of Python(no `__get__` and `__set__`), but I did not open this door intentionally.


* Another way of using dataclasses is just declaring the fields:

```py
@dataclass
class DBCredentials:
    password: Password
    uri: DBUri
    port: DBPort
    host: DBHost
```

Then initialize the fields in the future. This approach is similar to DTOs(data transfer objects).

* Is it possible to JSON serialize `DBCredentials`? Impossible if you decided to dump sensitive fields:
Trying with custom encoder:
```py
import json

class CustomDBCredentialsEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            # Intentionally omit other fields
            return {"uri": obj.uri.get_secret()}
        except AttributeError:
            return super().default(obj)
```

```py
>>> credentials = DBCredentialsWithDescriptors()

>>> json.dumps(credentials, cls=CustomDBCredentialsEncoder)
...
readonce.UnsupportedOperationException: ('Not allowed on sensitive value', 'Sensitive data can not be serialized')
```

Same applies to pickling:

```py
>>> import pickle
>>> pickle.dumps(credentials)
...
readonce.UnsupportedOperationException: Not allowed on sensitive value
```

# Relation with [Pydantic](https://pydantic-docs.helpmanual.io/)

As we know the Pydantic models is a de-facto standard for data validation based on type annotations, we can easily use ReadOnce objects with Pydantic.
In this section I am going to share some tests.

The simplest way to declare Pydantic models with ReadOnce objects is to allow arbitrary types:

```py
from pydantic import BaseModel

class DBCredentialsModel(BaseModel):
    comment: str
    password: Password
    uri: DBUri
    port: DBPort
    host: DBHost

    class Config:
        arbitrary_types_allowed = True
```

Creating credentials:

```py
>>> credentials = DBCredentialsModel(comment="The Hacked Database", password=Password("db-password"), uri=DBUri("mysql://"), port=DBPort(3306), host=DBHost("localhost"))
>>> credentials
DBCredentialsModel(comment='The Hacked Database', password=ReadOnce[secrets=*****], uri=ReadOnce[secrets=*****], port=ReadOnce[secrets=*****], host=ReadOnce[secrets=*****])
```

Again the sensitive data is not exposed:

```py
credentials.dict()
{'comment': 'The Hacked Database', 'password': ReadOnce[secrets=*****], 'uri': ReadOnce[secrets=*****], 'port': ReadOnce[secrets=*****], 'host': ReadOnce[secrets=*****]}
```

It can not be serialized in a default way:

```py
>>> credentials.json()
...
TypeError: Object of type 'Password' is not JSON serializable
```

Unfortunately, the nature of the ReadOnce object prevents using powerful validation mechanics in the model class.
In its core, the sensitive object can not be used twice if it was already consumed:
* You can call arbitrary time `add_secret()` if no `get_secret()` was called before it.
* Whenever you called `get_secret()` the sensitive object is considered as exhausted.

Imagine we want to validate the password length and try to add custom validator inside the Pydantic model:

```py
from pydantic import BaseModel, validator

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
```

As you can expect, we need first get the secret data then validate it, if validation is okay we need to put that secret back to the sensitive object, which is not possible.

Therefore, it is better to push the validation logic towards `Password` sensitive class instead. We will explore the validation in-depth in the future.

If we test this `InvalidDBCredentialsModel` it should fail with:
`readonce.UnsupportedOperationException: ('Not allowed on sensitive value', 'Sensitive object exhausted; you can not use it twice')`

> If you have any further Pydantic ideas please open an issue, we can explore and figure out the best usage

# Applying best practices from Design by Contract

In order to further ensure data(secret) integrity and security, 
we can use `DbC` ideas as it gives us cleaner way of defining reusable constraints.

I like [icontract](https://github.com/Parquery/icontract) package which is quite handy tool.
I have tried to explain this YouTube tutorial as well [Design-by-Contract programming with Python](https://www.youtube.com/watch?v=yi-GInnc768).

Let's redefine our sensitive class as:

```py
import icontract
from readonce import ReadOnce

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
```

The current password validation is quite naive, it just checks the length of the string: this is our `pre-condition` and
it is marked as `@icontract.require`.

But what is `@icontract.ensure` then? 
This is our so called, `post-condition`: after adding secret the length of the secrets storage must be equal to one.

We can add more sophisticated password validation using regex, it is up to your business needs.
The question should be asked here: *"What is a password for our application?"*

```py
import re

def validate_password(password: str) -> bool:
    reg = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{6,20}$"
    pattern = re.compile(reg)
    return bool(re.search(pattern, password))
```

After writing down password requirements you can convert them to `pre-conditions` as part of your DbC approach.

# Is it possible to monkeypatch the secret logic management?

As far, as I have tested it, 
it is really non-trivial and over-hardened to monkeypatch the secret storage and also the secret management methods.

For eg, following test clearly shows the consequences:

```py
def test_monkeypatch_change_secrets_storage(get_password_obj, monkeypatch):
    # Directly trying to monkeypatch will raise double UnsupportedOperationException;
    # As monkeypatch in its default undo() section tries to again edit "_ReadOnce__secrets" which raises same exception
    # That's why we use context() below

    # with pytest.raises(UnsupportedOperationException):
    #     monkeypatch.setattr(get_password_obj, "_ReadOnce__secrets", ["12345"], raising=False)

    with pytest.raises(UnsupportedOperationException):
        with monkeypatch.context() as m:
            m.setattr(get_password_obj, "_ReadOnce__secrets", ["12345"], raising=True)
```


# How to install for development?

### Create and activate the virtualenv:

* `python3.10 -m venv .venv`

* `source .venv/bin/activate`

We use flit for the package management:

### Install flit:

* `pip install flit==3.7.1`

### Installing project for development

`make install-dev` or `flit install --env --deps=develop --symlink` 

### Installing for general showcase

`make install` or `flit install --env --deps=develop` 

### Run all tests in verbose

`make test` or `pytest -svv`

