"""Clean test file for doctester."""

def add(x: int, y: int) -> int:
    """Add two numbers.

    Example:
    ```python
    >>> 2 + 3
    5
    >>> 10 + (-5)
    5

    ```
    """

def multiply_no_doctest(x: int, y: int) -> int:
    """Multiply two numbers.

    ```python
    assert 3 * 4 == 12
    assert 0 * 100 == 0
    ```
    """

"""Stub file with no doctests to test empty file handling."""

def no_docstring() -> None: ...
def empty_docstring() -> None:
    """"""  # ruff: ignore[empty-docstring]

def no_examples() -> None:
    """Function without examples.

    Args:
        None
    """

class EdgeCases:
    """Class with complex signature.

    ```python
    >>> # Testing complex class instantiation patterns
    >>> class Example:
    ...     pass
    >>> obj = Example()
    >>> type(obj).__name__
    'Example'

    ```

    ```python
    >>> # Testing complex class instantiation patterns
    >>> class Example:
    ...     pass
    >>> obj = Example()
    >>> type(obj).__name__
    'Example'

    ```
    """

    def generic_method[T](self, value: T) -> T:
        """Method with generic type parameter.

        ```python
        >>> def identity[T](x: T) -> T:
        ...     return x
        >>> identity(42)
        42
        >>> identity("hello")
        'hello'
        >>> identity([1, 2, 3])
        [1, 2, 3]

        ```
        """

def function_with_default(x: int = 10, y: str = "default") -> str:
    """Function with default parameters.

    ```python
    >>> def greet(name: str = "World", prefix: str = "Hello") -> str:
    ...     return f"{prefix}, {name}!"
    >>> greet()
    'Hello, World!'
    >>> greet("Alice")
    'Hello, Alice!'
    >>> greet("Bob", "Hi")
    'Hi, Bob!'
    >>> greet(prefix="Hey", name="Charlie")
    'Hey, Charlie!'

    ```
    """

def function_with_complex_return() -> dict[str, list[int | None]]:
    r"""Function with complex return type annotation.

    ```python
    >>> # Complex nested types with union
    >>> result: dict[str, list[int | None]] = {
    ...     "values": [1, 2, None, 3],
    ...     "empty": [],
    ...     "mixed": [None, 42, None]
    ... }
    >>> result["values"]
    [1, 2, None, 3]
    >>> len(result)
    3
    >>> None in result["mixed"]
    True

    ```
    """

def intersection() -> None:
    """Exracted from pyochain.

    Check complex docstring.

    Args:
        other (AbstractSet[Any]): The set to intersect with.

    Returns:
        AbstractSet[T]: A new `Set` containing shared elements only.

    Example:
        ```python
        from pyochain import Set, Dict, Vec

        from_set = Set((1, 2))
        assert from_set.intersection({2, 3}) == Set((2,))
        assert from_set.intersection({3, 4}) == Set(())
        dct = Dict.from_ref({"a": 1, "b": 2, "c": 3})
        from_keys = dct.keys().intersection({"b", "c", "d"}).iter().sort()
        assert from_keys == Vec(("b", "c"))
        from_items = (
            dct.items().intersection({("b", 2), ("c", 3), ("d", 4)}).iter().sort()
        )
        assert from_items == Vec((("b", 2), ("c", 3)))
        ```
    """

def unfenced_doctest() -> None:
    """Function with un-fenced doctest.

    >>> 5 - 3
    2
    """

# Extracted from pyochain, check complex docstring with nested code blocks and examples.
class DictMd:
    """A `Dict` is a key-value store similar to Python's built-in `dict`, but with additional methods inspired by Rust's `HashMap`.

    Accept the same input types as the built-in `dict`, including `Mapping`, `Iterable` of key-value pairs, and objects implementing `__getitem__()` and `keys()`.

    Implement the `MutableMapping` interface, so all standard dictionary operations are supported.

    Args:
        data (DictConvertible[K, V]): Initial data for the Dict that can converted to a dictionary.

    See Also:
        - [`Dict::from_ref`][from_ref]: Create a `Dict` from an existing dictionary, no-copy.
        - [`Dict::from_kwargs`][from_kwargs]: Create a `Dict` from keyword arguments.
        - [`Dict::from_object`][from_object]: Create a `Dict` from an object's `__dict__` attribute, no-copy.

    Example:
        The most straightforward way to create a `Dict` is from a standard Python `dict`.

        This will copy the data, just like the built-in `dict` constructor.
        ```python
        from pyochain import Dict

        py_dict = {1: "a", 2: "b"}
        pyochain_dict = Dict(py_dict)
        assert pyochain_dict == Dict({1: "a", 2: "b"})
        ```
        Another common case is when you have an iterable of key-value pairs, such as the one returned by `dict::items`, or an `Iterator` of tuples.
        ```python
        from pyochain import Dict, Iter, Seq

        names = Seq(("alice", "bob", "charlie", "dave"))
        ages = (30, 25, 35, 40)
        records = names.iter().zip(ages).collect(Dict)
        assert records == Dict({"alice": 30, "bob": 25, "charlie": 35, "dave": 40})
        assert records.items().iter().collect(Seq) == (
            ("alice", 30),
            ("bob", 25),
            ("charlie", 35),
            ("dave", 40),
        )
        ```
        Any object that implements the `Mapping` protocol can also be directly converted to a `Dict`:
        ```python
        from collections.abc import Mapping, Iterator, Iterable
        from dataclasses import dataclass

        @dataclass
        class CustomMapping(Mapping[int, str]):
            data: dict[int, str]

            def __getitem__(self, key: int) -> str:
                return self.data[key]

            def __iter__(self) -> Iterator[int]:
                return iter(self.data)

            def __len__(self) -> int:
                return len(self.data)

        custom_mapping = CustomMapping({1: "a", 2: "b"})
        assert Dict(custom_mapping) == Dict({1: "a", 2: "b"})
        ```
        But it can also be as minimal as an object that implements `__getitem__` and `keys`:
        ```python
        from pyochain import Dict

        class MinimalDictLike:
            def __init__(self, data: dict[int, str]) -> None:
                self._data = data

            def keys(self) -> Iterable[int]:
                return iter(self._data)

            def __getitem__(self, key: int) -> str:
                return self._data[key]

        minimal_dict_like = MinimalDictLike({1: "a", 2: "b"})
        assert Dict(minimal_dict_like) == Dict({1: "a", 2: "b"})
        ```
    """  # ruff: ignore[line-too-long]

class Dict:
    """A `Dict` is a key-value store similar to Python's built-in `dict`, but with additional methods inspired by Rust's `HashMap`.

    Accept the same input types as the built-in `dict`, including `Mapping`, `Iterable` of key-value pairs, and objects implementing `__getitem__()` and `keys()`.

    Implement the `MutableMapping` interface, so all standard dictionary operations are supported.

    Args:
        data (DictConvertible[K, V]): Initial data for the Dict that can converted to a dictionary.

    See Also:
        - [`Dict::from_ref`][from_ref]: Create a `Dict` from an existing dictionary, no-copy.
        - [`Dict::from_kwargs`][from_kwargs]: Create a `Dict` from keyword arguments.
        - [`Dict::from_object`][from_object]: Create a `Dict` from an object's `__dict__` attribute, no-copy.

    Example:
        The most straightforward way to create a `Dict` is from a standard Python `dict`.

        This will copy the data, just like the built-in `dict` constructor.
        ```python
        >>> from pyochain import Dict
        >>> py_dict = {1: "a", 2: "b"}
        >>> pyochain_dict = Dict(py_dict)
        >>> pyochain_dict
        Dict(1: 'a', 2: 'b')

        ```
        Another common case is when you have an iterable of key-value pairs, such as the one returned by `dict::items`, or an `Iterator` of tuples.
        ```python
        >>> from pyochain import Dict, Iter, Seq
        >>>
        >>> names = ("alice", "bob", "charlie", "dave")
        >>> ages = (30, 25, 35, 40)
        >>> records = Iter(names).zip(ages).collect(Dict)
        >>> records
        Dict('alice': 30, 'bob': 25, 'charlie': 35, 'dave': 40)
        >>> records.items().iter().collect(Seq)
        Seq(('alice', 30), ('bob', 25), ('charlie', 35), ('dave', 40))

        ```
        Any object that implements the `Mapping` protocol can also be directly converted to a `Dict`:
        ```python
        >>> from collections.abc import Mapping, Iterable, Iterator
        >>> from dataclasses import dataclass
        >>> @dataclass
        ... class CustomMapping(Mapping[int, str]):
        ...     data: dict[int, str]
        ...
        ...     def __getitem__(self, key: int) -> str:
        ...         return self.data[key]
        ...
        ...     def __iter__(self) -> Iterator[int]:
        ...         return iter(self.data)
        ...
        ...     def __len__(self) -> int:
        ...         return len(self.data)
        >>> custom_mapping = CustomMapping({1: "a", 2: "b"})
        >>> Dict(custom_mapping)
        Dict(1: 'a', 2: 'b')

        ```
        But it can also be as minimal as an object that implements `__getitem__` and `keys`:
        ```python
        >>> from pyochain import Dict
        >>>
        >>> class MinimalDictLike:
        ...     def __init__(self, data: dict[int, str]) -> None:
        ...         self._data = data
        ...
        ...     def keys(self) -> Iterable[int]:
        ...         return iter(self._data)
        ...
        ...     def __getitem__(self, key: int) -> str:
        ...         return self._data[key]
        >>>
        >>> minimal_dict_like = MinimalDictLike({1: "a", 2: "b"})
        >>> Dict(minimal_dict_like)
        Dict(1: 'a', 2: 'b')

        ```
    """  # ruff: ignore[line-too-long]
