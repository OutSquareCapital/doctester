# Edge Cases and Special Tests

## Empty Code Block

Nothing here, just text.

## Code Block with Non-Python Language

We shouldn't parse this:

```javascript
console.log("hello");
```

## Python Block

This should be parsed:

```py
>>> 1 + 1
2
```

## Mixed Content

Some explanation before code:

```py
>>> x = []
>>> x.append(5)
>>> x
[5]
```

More text and explanation.

```py
>>> len([1, 2, 3, 4, 5])
5
```

## Multiline Strings

```py
>>> text = """
... This is a
... multiline string
... """
>>> "multiline" in text
True
```

## Complex Expressions

```py
>>> [x**2 for x in range(5) if x % 2 == 0]
[0, 4, 16]
```

## Import Statements

```py
>>> import math
>>> math.pi
3.141592653589793
```

## Custom Classes

```py
>>> class Point:
...     def __init__(self, x, y):
...         self.x = x
...         self.y = y
...     def __repr__(self):
...         return f"Point({self.x}, {self.y})"
>>> p = Point(3, 4)
>>> p
Point(3, 4)
```
