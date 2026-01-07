# Advanced Markdown Tests

## String Operations

Tests for string manipulation:

```py
>>> text = "hello world"
>>> text.capitalize()
'Hello world'
```

Another string operation:

```py
>>> "test".replace("e", "a")
'tast'
```

## List Operations

Working with lists:

```py
>>> numbers = [1, 2, 3]
>>> sum(numbers)
6
```

List comprehension:

```py
>>> [x * 2 for x in [1, 2, 3]]
[2, 4, 6]
```

## Dictionary Operations

Basic dict operations:

```py
>>> d = {"a": 1, "b": 2}
>>> d["a"]
1
```

Dict get method:

```py
>>> d = {"x": 10, "y": 20}
>>> d.get("z", "not found")
'not found'
```

## Function Definitions

Define and call a function:

```py
>>> def add(a, b):
...     return a + b
>>> add(2, 3)
5
```

Recursive function:

```py
>>> def factorial(n):
...     return 1 if n <= 1 else n * factorial(n - 1)
>>> factorial(5)
120
```

## Exception Handling

```py
>>> 1 / 0
Traceback (most recent call last):
  ...
ZeroDivisionError: division by zero
```

## Type Conversions

```py
>>> int("42")
42
```

```py
>>> float("3.14")
3.14
```

```py
>>> str(123)
'123'
```
