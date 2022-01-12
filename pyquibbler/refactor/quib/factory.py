import functools
import pathlib
import weakref
from typing import Optional, Tuple, Type, Callable

from pyquibbler.refactor.env import GET_VARIABLE_NAMES, SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS
from pyquibbler.refactor.logger import logger
from pyquibbler.refactor.function_definitions.func_call import FuncCall
from pyquibbler.refactor.project import Project
from pyquibbler.refactor.quib.function_running import FunctionRunner
from pyquibbler.refactor.function_definitions import get_definition_for_function, CannotFindDefinitionForFunctionException
from pyquibbler.refactor.quib.graphics import UpdateType
from pyquibbler.refactor.quib.quib_guard import add_new_quib_to_guard_if_exists
from pyquibbler.refactor.quib.utils.iterators import iter_quibs_in_args
from pyquibbler.refactor.quib.quib import Quib
from pyquibbler.refactor.quib.utils import deep_copy_without_quibs_or_graphics
from pyquibbler.refactor.quib.variable_metadata import get_var_name_being_set_outside_of_pyquibbler, \
    get_file_name_and_line_number_of_quib


def get_original_func(func: Callable):
    """
    Get the original func- if this function is already overrided, get the original func it's function_definitions.

    So for example, if the OVERLOADED np.array is given as `func`, then the ORIGINAL np.array will be returned
    If the ORIGINAL np.array is given as `func`, then `func` will be returned
    """
    while hasattr(func, '__quibbler_wrapped__'):
        func = func.__quibbler_wrapped__
    return func


def get_deep_copied_args_and_kwargs(args, kwargs):
    if kwargs is None:
        kwargs = {}
    kwargs = {k: deep_copy_without_quibs_or_graphics(v) for k, v in kwargs.items()}
    args = deep_copy_without_quibs_or_graphics(args)
    return args, kwargs


def get_quib_name() -> Optional[str]:
    should_get_variable_names = GET_VARIABLE_NAMES and not Quib._IS_WITHIN_GET_VALUE_CONTEXT

    try:
        return get_var_name_being_set_outside_of_pyquibbler() if should_get_variable_names else None
    except Exception as e:
        logger.warning(f"Failed to get name, exception {e}")

    return None


def get_file_name_and_line_no() -> Tuple[Optional[str], Optional[str]]:
    should_get_file_name_and_line = SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS and not Quib._IS_WITHIN_GET_VALUE_CONTEXT

    try:
        return get_file_name_and_line_number_of_quib() if should_get_file_name_and_line else None, None
    except Exception as e:
        logger.warning(f"Failed to get file name + lineno, exception {e}")

    return None, None


def create_quib(func, args=(), kwargs=None, cache_behavior=None, evaluate_now=False,
                allow_overriding=False, call_func_with_quibs: bool = False, update_type: UpdateType = None,
                can_save_as_txt: bool = False, default_save_directory: pathlib.Path = None,
                **init_kwargs):
    """
    Public constructor for creating a quib.
    # TODO: serious docs
    """

    kwargs = kwargs or {}

    # TODO: how are we handling this situation overall
    call_func_with_quibs = kwargs.pop('call_func_with_quibs', call_func_with_quibs)

    args, kwargs = get_deep_copied_args_and_kwargs(args, kwargs)
    file_name, line_no = get_file_name_and_line_no()
    func = get_original_func(func)

    definition = get_definition_for_function(func)

    runner = definition.function_runner_cls.from_(
        func_call=FuncCall.from_function_call(
            func=func,
            args=args,
            kwargs=kwargs,
            include_defaults=True
        ),
        call_func_with_quibs=call_func_with_quibs,
        graphics_collections=None,
        default_cache_behavior=cache_behavior or FunctionRunner.DEFAULT_CACHE_BEHAVIOR,
    )

    quib = Quib(function_runner=runner,
                assignment_template=None,
                allow_overriding=allow_overriding,
                name=get_quib_name(),
                file_name=file_name,
                line_no=line_no,
                update_type=None,
                can_save_as_txt=can_save_as_txt,
                default_save_directory=default_save_directory or Project.get_or_create().function_quib_directory,
                **init_kwargs)

    add_new_quib_to_guard_if_exists(quib)

    if update_type:
        quib.set_redraw_update_type(update_type or UpdateType.DRAG)

    for arg in iter_quibs_in_args(args, kwargs):
        arg.add_child(quib)

    if evaluate_now:
        quib.get_value()

    return quib
