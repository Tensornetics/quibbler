from sys import getsizeof
from time import perf_counter
from typing import Callable, Any, Mapping, Tuple, Optional, List, TYPE_CHECKING

from .cache import ShallowCache
from .function_quib import FunctionQuib, CacheBehavior
from ..assignment import AssignmentTemplate


if TYPE_CHECKING:
    from ..assignment.assignment import PathComponent, Assignment, PathComponent
    from ..quib import Quib


class DefaultFunctionQuib(FunctionQuib):
    """
    The default implementation for a function quib, when no specific function quib type can be used.
    This implementation treats the quib as a whole unit, so when a dependency of a DefaultFunctionQuib
    is changed, the whole cache is thrown away.
    """

    @property
    def is_cache_valid(self):
        """
        User interface to check cache validity.
        """
        return self._is_cache_valid

    def __init__(self,
                 func: Callable,
                 args: Tuple[Any, ...],
                 kwargs: Mapping[str, Any],
                 cache_behavior: Optional[CacheBehavior],
                 assignment_template: Optional[AssignmentTemplate] = None,
                 is_cache_valid: bool = False,
                 cached_result: Any = None):
        super().__init__(func, args, kwargs, cache_behavior, assignment_template=assignment_template)
        self._is_cache_valid = is_cache_valid
        self._cached_result = cached_result
        self._cache = ShallowCache()

    def _invalidate_self(self, path: List['PathComponent']):
        self._cache.set_invalid_at_path_component(path[0])

    def _should_cache(self, result: Any, elapsed_seconds: float):
        """
        Decide if the result of the calculation is worth caching according to its size and the calculation time.
        Note that there is no accurate way (and no efficient way to even approximate) the complete size of composite
        types in python, so we only measure the outer size of the object.
        """
        if self._cache_behavior is CacheBehavior.ON:
            return True
        if self._cache_behavior is CacheBehavior.OFF:
            return False
        assert self._cache_behavior is CacheBehavior.AUTO, \
            f'self._cache_behavior has unexpected value: "{self._cache_behavior}"'
        return elapsed_seconds > self.MIN_SECONDS_FOR_CACHE \
               and getsizeof(result) / elapsed_seconds < self.MAX_BYTES_PER_SECOND

    def _get_inner_value_valid_at_path(self, path: Optional[List['PathComponent']]):
        """
        If the cached result is still valid, return it.
        Otherwise, calculate the value, store it in the cache and return it.
        """
        if self._is_cache_valid:
            return self._cached_result

        start_time = perf_counter()
        # Because we have a shallow cache, we want the result valid at the first component
        result = self._call_func(path[0])
        elapsed_seconds = perf_counter() - start_time
        if self._should_cache(result, elapsed_seconds):
            self._cache.set_valid_value_at_path_component(path[0], result)
            self._cached_result = result
            self._is_cache_valid = True
        return result
