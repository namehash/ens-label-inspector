"""
How it works:
- @field is used to mark a field as public or private (name starts with _).

A field is created as a cached_property, so it is only computed once.
If the field is public, it is given a '_is_public_field' attribute.
The materialize() function goes over all public fields and builds a 'materialized' dictionary (computes all fields).
If it finds a list, it recursively materializes all elements in the list.
A private field is never materialized, but it can be used as a helper function for other fields.

How to:
- Create a simple field:
    Mark a member function with @field.
    The function needs to be a pure (no side effects).

- Create a field that depends on other fields:
    Just use the other fields in the function body.
    They will be computed as needed.

- Create a private field:
    Name the field _my_field (first underscore makes the field private).

- Create a field which is a list of objects:
    Make the field return a list of objects inheriting from AnalysisBase (nested lists are OK).
    In your code you can use these lists as they are (your own types).
    In the response they will be materialized as lists of dictionaries.

- Refer to a field higher in the hierarchy from a child (e.g. list element):
    The convention is to pass the parent AnalysisBase object as an argument to the child.
    You should also set the root attribute of the child to point to the analysis root object.
    @analysis_object
    class MyChild(AnalysisBase):
        def __init__(self, my_value, parent):
            # a value characteristic of the child
            self.my_value = my_value
            # the parent AnalysisBase object
            self.parent = parent
            # the top-level AnalysisBase object
            self.root = parent.root

        @field
        def my_field(self):
            # use self.parent.some_field to refer to a field of the parent

    @analysis_object
    class MyParent(AnalysisBase):
        @field
        def children(self):
            return [MyChild(v, self) for v in self.my_values]

- Use a function that returns multiple values:
    Given a function f() -> (v1, v2, ...), create a field with the following signature:
    @field
    # should probably be private (unless you want to also include it in the response)
    def _my_field(self) -> Tuple[v1, v2, ...]:
        return f(self)
    # Then, map the tuple elements to their own fields:
    @field
    def my_field_1(self) -> v1:
        return self._my_field[0]
    ...
"""


from typing import Generic, Optional, List, Dict, TypeVar, Callable


T = TypeVar('T')
R = TypeVar('R')


def agg_all(items: List[T]) -> Optional[T]:
    '''
    Returns the first item if all items are equal, otherwise None.
    '''
    if len(items) == 0:
        return None
    it0 = items[0]
    return it0 if all(items[i] == it0 for i in range(1, len(items))) else None


def agg_any(items: List[T]) -> List[T]:
    '''
    Returns a list of unique items.
    '''
    return list(set(items))


def agg_only(items: List[T]) -> Optional[T]:
    '''
    Returns the first item if there is only one item, otherwise None.
    '''
    return items[0] if len(items) == 1 else None


class field(Generic[R]):
    def __init__(self, func: Callable[..., R]):
        self.func = func
        self._is_public_field = func.__name__[0] != '_'

    def __get__(self, obj, cls) -> R:
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


def analysis_object(cls):
    cls._FIELDS = [name
                   for name in dir(cls)
                   if name[0] != '_'
                   if hasattr(getattr(cls, name), '_is_public_field')]
    return cls


class AnalysisBase:
    def materialize(self) -> Dict:
        def process(field):
            if isinstance(field, AnalysisBase):
                # Recursively materialize the field.
                return field.materialize()
            elif isinstance(field, List):
                # Look for materializable objects in the list.
                return [process(fi) for fi in field]
            else:
                # The field is a simple value.
                return field

        # Create a dictionary field_name: field_value.
        return {field: process(getattr(self, field)) for field in self._FIELDS}
