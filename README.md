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

* At some points the class itself can be silently dumped to logs, but not here:

```py
>>> obj = Password(password="awesome_password")
>>> print(obj)
ReadOnce[secrets=*****]
>>> obj
ReadOnce[secrets=*****]
```


# TODO

* Prevent JSON serialization
