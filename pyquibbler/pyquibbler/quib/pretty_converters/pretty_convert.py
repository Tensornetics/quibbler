import operator
from typing import Callable
from typing import Tuple, Any, Mapping

import numpy as np

from pyquibbler.quib.pretty_converters.convert_math_equations import OPERATOR_FUNCS_TO_MATH_CONVERTERS, \
    MathExpression, StringMathExpression, MathPrecedence
from pyquibbler.env import REPR_RETURNS_SHORT_NAME


def _convert_sub_item(sub_item: Any) -> str:
    if isinstance(sub_item, slice):
        return _convert_slice(sub_item)
    if isinstance(sub_item, type(Ellipsis)):
        return '...'
    return repr(sub_item)


def _convert_slice(slice_: slice) -> str:
    pretty = ':'
    if slice_.start is not None:
        pretty = f"{slice_.start}{pretty}"
    if slice_.stop is not None:
        pretty = f"{pretty}{slice_.stop}"
    if slice_.step is not None:
        pretty = f"{pretty}:{slice_.step}"
    return pretty


def getitem_converter(func: Callable, args: Tuple[Any, ...]) -> MathExpression:

    assert len(args) == 2
    obj, item = args
    if isinstance(item, tuple):
        item_repr = ", ".join(_convert_sub_item(sub_item) for sub_item in item)
        if len(item) == 1:
            item_repr = f"({item_repr},)"
    else:
        item_repr = _convert_sub_item(item)
    return StringMathExpression(f"{obj}[{item_repr}]", MathPrecedence.SUBSCRIPTION)


def vectorize_call_converter(func: Callable, args: Tuple[Any, ...]) -> MathExpression:
    func_being_called, *args = args
    return StringMathExpression(f"{func_being_called}({', '.join(repr(arg) for arg in args)})",
                                MathPrecedence.FUNCTION_CALL)


def function_call_converter(func: Callable,
                            args: Tuple[Any, ...],
                            kwargs: Mapping[str, Any]) -> MathExpression:
    func_name = getattr(func, '__name__', str(func))
    pretty_args, pretty_kwargs = get_pretty_args_and_kwargs(args, kwargs)
    return StringMathExpression(f'{func_name}({", ".join(map(str, [*pretty_args, *pretty_kwargs]))})',
                                MathPrecedence.FUNCTION_CALL)


def str_format_call_converter(func: Callable,
                              args: Tuple[Any, ...],
                              kwargs: Mapping[str, Any]) -> MathExpression:
    func_name = getattr(func, '__name__', str(func))
    str_ = getattr(func, '__reduce__')()[1][0]
    pretty_args, pretty_kwargs = get_pretty_args_and_kwargs(args, kwargs)
    return StringMathExpression(f'"{str_}".{func_name}({", ".join(map(str, [*pretty_args, *pretty_kwargs]))})',
                                MathPrecedence.FUNCTION_CALL)


def get_pretty_args_and_kwargs(args: Tuple[Any, ...], kwargs: Mapping[str, Any]):
    pretty_args = [repr(arg) for arg in args]
    pretty_kwargs = [f'{key}={repr(val)}' for key, val in kwargs.items()]

    return pretty_args, pretty_kwargs


def is_str_format(func: Callable) -> bool:
    return getattr(func, '__qualname__', None) == 'str.format'


def get_pretty_value_of_func_with_args_and_kwargs(func: Callable,
                                                  args: Tuple[Any, ...],
                                                  kwargs: Mapping[str, Any]) -> MathExpression:
    """
    Get the pretty value of a function, using a special converter if possible (eg for math notation) and defaulting
    to a standard func(xxx) if not
    """

    with REPR_RETURNS_SHORT_NAME.temporary_set(True):
        # For now, no ability to special convert if kwargs exist
        if not kwargs and func in CONVERTERS:
            pretty_value = CONVERTERS[func](func, args)
        elif is_str_format(func):
            pretty_value = str_format_call_converter(func, args, kwargs)
        else:
            pretty_value = function_call_converter(func, args, kwargs)

        return pretty_value


CONVERTERS = {
    **OPERATOR_FUNCS_TO_MATH_CONVERTERS,
    operator.getitem: getitem_converter,
    np.vectorize.__call__: vectorize_call_converter
}
