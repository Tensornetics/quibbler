from typing import Any

from pyquibbler import Quib, q


def identity_function_for_obj2quib(v):
    return v


# For the functional_representation:
identity_function_for_obj2quib.__name__ = 'obj2quib'


def obj2quib(obj: Any) -> Quib:
    """
    Create a quib from an object containing quibs.

    Convert an object containing quibs to a quib whose value represents the object.

    Parameters
    ----------
    obj : any object
        The object to convert to quib. Can contain nested lists, tuples, dicts and quibs.

    See also
    --------
    quiby, q, iquib

    Examples
    --------
    >>> a = iquib(3)
    >>> my_list = obj2quib([1, 2, a, 4])
    >>> a.assign(7)
    >>> my_list.get_value()
    [1, 2, 7, 4]

    Note
    ----
    If the argument obj is a quib, the function returns this quib.
    """

    # TODO: need to implement translation and inversion for list, tuple and dict.
    if isinstance(obj, (list, tuple)):
        return q(identity_function_for_obj2quib, type(obj)([obj2quib(sub_obj) for sub_obj in obj]))

    if isinstance(obj, dict):
        return q(identity_function_for_obj2quib, {obj2quib(sub_key): obj2quib(sub_obj) for sub_key, sub_obj in obj.items()})

    return obj
