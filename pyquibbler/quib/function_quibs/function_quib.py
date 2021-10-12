from __future__ import annotations
import types
from enum import Enum
from functools import wraps, cached_property
from operator import getitem
from typing import Callable, Any, Mapping, Tuple, Optional, Set

import numpy as np

from ..override_choice import get_overrides_for_assignment
from ..assignment import AssignmentTemplate, Assignment
from ..assignment.assignment import QuibWithAssignment
from ..quib import Quib
from ..utils import is_there_a_quib_in_args, iter_quibs_in_args, call_func_with_quib_values, \
    deep_copy_without_quibs_or_artists, copy_and_convert_args_to_values
from ...env import LAZY


class CacheBehavior(Enum):
    """
    The different modes in which the caching of a FunctionQuib can operate:
     - `AUTO`: decide automatically according to the ratio between evaluation time and memory consumption.
     - `OFF`: never cache.
     - `ON`: always cache.
    """
    AUTO = 'auto'
    OFF = 'off'
    ON = 'on'


class FunctionQuib(Quib):
    """
    An abstract class for quibs that represent the result of a computation.
    """
    _DEFAULT_CACHE_BEHAVIOR = CacheBehavior.AUTO
    MAX_BYTES_PER_SECOND = 2 ** 30
    MIN_SECONDS_FOR_CACHE = 1e-3

    def __init__(self,
                 func: Callable,
                 args: Tuple[Any, ...],
                 kwargs: Mapping[str, Any],
                 cache_behavior: Optional[CacheBehavior],
                 assignment_template: Optional[AssignmentTemplate] = None):
        super().__init__(assignment_template=assignment_template)
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._cache_behavior = None

        if cache_behavior is None:
            cache_behavior = self._DEFAULT_CACHE_BEHAVIOR
        self.set_cache_behavior(cache_behavior)

    @cached_property
    def parents(self) -> Set[Quib]:
        return set(iter_quibs_in_args(self.args, self.kwargs))

    @classmethod
    def create(cls, func, func_args=(), func_kwargs=None, cache_behavior=None, **kwargs):
        """
        Public constructor for FunctionQuib.
        """
        # If we received a function that was already wrapped with a function quib, we want want to unwrap it
        while hasattr(func, '__quib_wrapper__'):
            assert func.__quib_wrapper__ is cls, "This function was wrapped previously with a different class"
            previous_func = func
            func = func.__wrapped__
            # If it was a bound method we need to recreate it
            if hasattr(previous_func, '__self__'):
                func = types.MethodType(func, previous_func.__self__)

        if func_kwargs is None:
            func_kwargs = {}
        func_kwargs = {k: deep_copy_without_quibs_or_artists(v)
                       for k, v in func_kwargs.items()}
        func_args = deep_copy_without_quibs_or_artists(func_args)
        self = cls(func=func, args=func_args, kwargs=func_kwargs,
                   cache_behavior=cache_behavior, **kwargs)
        for arg in iter_quibs_in_args(func_args, func_kwargs):
            arg.add_child(self)
        if not LAZY:
            self.get_value()
        return self

    @classmethod
    def create_wrapper(cls, func: Callable):
        """
        Given an original function, return a new function (a "wrapper") to be used instead of the original.
        The wrapper, when called, will return a FunctionQuib of type `cls` if its arguments contain a quib.
        Otherwise it will call the original function and will return its result.
        This function can be used as a decorator.
        """

        @wraps(func)
        def quib_supporting_func_wrapper(*args, **kwargs):
            if is_there_a_quib_in_args(args, kwargs):
                return cls.create(func=func, func_args=args, func_kwargs=kwargs)

            return func(*args, **kwargs)

        quib_supporting_func_wrapper.__annotations__['return'] = cls
        quib_supporting_func_wrapper.__quib_wrapper__ = cls
        return quib_supporting_func_wrapper

    @property
    def func(self):
        return self._func

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs

    def assign(self, assignment: Assignment) -> None:
        """
        Apply the given assignment to the function quib.
        Using reverse assignments, the assignment will propagate as far is possible up the dependency graph,
        and collect possible overrides.
        When more than one override can be performed, the user will be asked to choose one.
        When there is only one override option, it will be automatically performed.
        When there are no override options, AssignmentNotPossibleException is raised.
        """
        get_overrides_for_assignment(self, assignment).apply()

    def __repr__(self):
        return f"<{self.__class__.__name__} - {getattr(self.func, '__name__', repr(self.func))}>"

    def pretty_repr(self):
        func_name = getattr(self.func, '__name__', str(self.func))
        args, kwargs = copy_and_convert_args_to_values(self.args, self.kwargs)
        posarg_reprs = map(str, args)
        kwarg_reprs = (f'{key}={val}' for key, val in kwargs.items())
        return f'{func_name}({", ".join([*posarg_reprs, *kwarg_reprs])})'

    def get_cache_behavior(self):
        return self._cache_behavior

    def set_cache_behavior(self, cache_behavior: CacheBehavior):
        self._cache_behavior = cache_behavior

    def _call_func(self):
        """
        Call the function wrapped by this FunctionQuib with the
        given arguments after replacing quib with their values.
        """
        try:
            return call_func_with_quib_values(self.func, self.args, self.kwargs)
        except Exception:
            print(1)
            raise
    def get_reversals_for_assignment(self, assignment: Assignment):
        return []