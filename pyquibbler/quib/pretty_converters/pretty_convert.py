import operator
from typing import Callable, List, Union
from typing import Tuple, Any, Mapping

import numpy as np

from pyquibbler.quib.pretty_converters.convert_math_equations import MATH_FUNCS_TO_CONVERTERS, \
    MathExpression
from pyquibbler.env import REPR_RETURNS_SHORT_NAME


def _convert_sub_item(sub_item: Any) -> str:
    if isinstance(sub_item, slice):
        return _convert_slice(sub_item)
    if isinstance(sub_item, type(Ellipsis)):
        return '...'
    return repr(sub_item)

def _convert_slice(slice_: slice):
    pretty = ':'
    if slice_.start is not None:
        pretty = f"{slice_.start}{pretty}"
    if slice_.stop is not None:
        pretty = f"{pretty}{slice_.stop}"
    if slice_.step is not None:
        pretty = f"{pretty}:{slice_.step}"
    return pretty


def getitem_converter(func, args: List[str]):
    assert len(args) == 2
    obj, item = args
    if isinstance(item, tuple):
        item = ", ".join(_convert_sub_item(sub_item) for sub_item in item)
    else:
        item = _convert_sub_item(item)
    return f"{obj}[{item}]"


def call_converter(func, pretty_arg_names: List[str]):
    func_being_called, *args = pretty_arg_names
    return f"{func_being_called}({', '.join(repr(arg) for arg in args)})"


def get_pretty_args_and_kwargs(args: Tuple[Any, ...], kwargs: Mapping[str, Any]):
    pretty_args = [repr(arg) for arg in args]
    pretty_kwargs = [f'{key}={repr(val)}' for key, val in kwargs.items()]

    return pretty_args, pretty_kwargs


def get_pretty_value_of_func_with_args_and_kwargs(func: Callable,
                                                  args: Tuple[Any, ...],
                                                  kwargs: Mapping[str, Any]) -> Union[MathExpression, str]:
    """
    Get the pretty value of a function, using a special converter if possible (eg for math notation) and defaulting
    to a standard func(xxx) if not
    """

    with REPR_RETURNS_SHORT_NAME.temporary_set(True):
        # For now, no ability to special convert if kwargs exist
        if not kwargs and func in CONVERTERS:
            pretty_value = CONVERTERS[func](func, args)
        else:
            func_name = getattr(func, '__name__', str(func))
            pretty_args, pretty_kwargs = get_pretty_args_and_kwargs(args, kwargs)
            pretty_value = f'{func_name}({", ".join(map(str, [*pretty_args, *pretty_kwargs]))})'

        return pretty_value


CONVERTERS = {
    **MATH_FUNCS_TO_CONVERTERS,
    operator.getitem: getitem_converter,
    np.vectorize.__call__: call_converter
}
