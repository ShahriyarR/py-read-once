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

# How about Python Dataclasses?

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

