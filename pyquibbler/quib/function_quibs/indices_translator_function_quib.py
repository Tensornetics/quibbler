import numpy as np
from abc import abstractmethod
from dataclasses import dataclass
from functools import lru_cache
from typing import Set, Optional, Dict, Callable, List, Any, Union

from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.function_quibs.utils import create_empty_array_with_values_at_indices, ArgsValues
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.function_quibs import FunctionQuib
from pyquibbler.quib.assignment import PathComponent, QuibWithAssignment
from pyquibbler.quib.utils import iter_objects_of_type_in_object_shallowly

Args = List[Any]
Kwargs = Dict[str, Any]


@dataclass
class SupportedFunction:
    data_source_indices: Union[Set[Union[int, str, slice]],
                               Callable[[Args, Kwargs, Kwargs], List[Any]]]

    def get_data_source_args(self, args_values: ArgsValues) -> List[Any]:
        if callable(self.data_source_indices):
            return self.data_source_indices(args_values)
        return [args_values[item] for item in self.data_source_indices]


class IndicesTranslatorFunctionQuib(FunctionQuib):
    SUPPORTED_FUNCTIONS: Optional[Dict[Callable, SupportedFunction]]

    def _get_source_shaped_bool_mask(self, invalidator_quib: Quib, indices: Any) -> Any:
        """
        Return a boolean mask in the shape of the given quib, in which only the given indices are set to
        True.
        """
        return create_empty_array_with_values_at_indices(
            value=True,
            empty_value=False,
            indices=indices,
            shape=invalidator_quib.get_shape().get_value()
        )

    def _get_bool_mask_representing_indices_in_result(self, indices) -> Union[np.ndarray, bool]:
        """
        Get a boolean mask representing where the indices that were changed are in the result- this will be in
        same shape as the result
        """
        return create_empty_array_with_values_at_indices(self.get_shape().get_value(),
                                                         indices=indices, value=True,
                                                         empty_value=False)

    def _get_representative_result(self, working_component, value):
        """
        Get a result representing the result of this quib (same shape) with the given component (directly indexable,
        not a `PathComponent`) set to a value
        """
        return create_empty_array_with_values_at_indices(
            self.get_shape().get_value(),
            indices=working_component,
            value=value,
        )

    @classmethod
    def create_wrapper(cls, func: Callable):
        if cls.SUPPORTED_FUNCTIONS is not None:
            try:
                assert func in cls.SUPPORTED_FUNCTIONS, \
                    f'Tried to create a wrapper for function {func} which is not supported'
            except Exception:
                print(1)
                raise
        return super().create_wrapper(func)

    @lru_cache()
    def _get_data_source_quib_parents(self) -> Set:
        if self.SUPPORTED_FUNCTIONS is not None:
            supported_function = self.SUPPORTED_FUNCTIONS[self._func]
            data_source_args = supported_function.get_data_source_args(self._get_args_values(include_defaults=False))
            return set(iter_objects_of_type_in_object_shallowly(Quib, data_source_args))
        return self.parents

    @abstractmethod
    def _forward_translate_indices_to_bool_mask(self, quib: Quib, indices: Any) -> Any:
        pass

    def _get_source_paths_of_quibs_given_path(self, filtered_path_in_result: List[PathComponent]):
        return {}

    def _get_quibs_to_relevant_result_values(self, assignment: Assignment):
        return {}

    def _forward_translate_invalidation_path(self, quib: Quib,
                                             path: List[PathComponent]) -> List[Optional[List[PathComponent]]]:
        working_component, *rest_of_path = path
        bool_mask_in_output_array = self._forward_translate_indices_to_bool_mask(quib,
                                                                                 working_component.component)

        if np.any(bool_mask_in_output_array):
            # If there exist both True's and False's in the boolean mask,
            # this function's quib result must be an ndarray- if it were a single item (say a PyObj, int, dict, list)
            # we'd expect it to be completely True (as it is ONE single object). If it is not a single item, it is by
            # definitely an ndarray
            assert issubclass(self.get_type(), np.ndarray) or np.all(bool_mask_in_output_array)
            assert issubclass(self.get_type(), np.ndarray) or isinstance(bool_mask_in_output_array, np.bool_) \
                   or (bool_mask_in_output_array.shape == () and bool_mask_in_output_array.dtype == np.bool_)

            if not np.all(bool_mask_in_output_array) and issubclass(self.get_type(), np.ndarray):
                return [[PathComponent(self.get_type(), bool_mask_in_output_array), *rest_of_path]]
            return [rest_of_path]
        return []

    def get_inversions_for_assignment(self, assignment: Assignment) -> List[QuibWithAssignment]:
        components_at_end = assignment.path[1:]
        current_components = assignment.path[0:1]
        if len(assignment.path) > 0 and assignment.path[0].references_field_in_field_array():
            components_at_end = [assignment.path[0], *components_at_end]
            current_components = []

        quibs_to_paths = self._get_source_paths_of_quibs_given_path(current_components)
        quibs_to_values = self._get_quibs_to_relevant_result_values(assignment)

        return [
            QuibWithAssignment(
                quib=quib,
                assignment=Assignment(
                    path=[*path, *components_at_end],
                    value=quibs_to_values[quib]
                )
            )
            for quib, path in quibs_to_paths.items()
            if quib in quibs_to_values
        ]
