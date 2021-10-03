from operator import getitem
from typing import Dict, List

import numpy as np

from pyquibbler.quib import Quib
from pyquibbler.quib.assignment import Assignment
from .reverser import Reversal, Reverser
from pyquibbler.quib.assignment.reverse_assignment.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.utils import recursively_run_func_on_object


class TranspositionalReverser(Reverser):
    """
    In charge of reversing all functions which move elements around from it's arguments WITHOUT performing
    any mathematical operations between them.
    """

    SUPPORTED_FUNCTIONS = [
        np.rot90,
        np.concatenate,
        getitem
    ]

    def _get_quibs_to_ids(self) -> Dict[Quib, int]:
        """
        Get a mapping between quibs and their unique ids (these ids are only constant for the particular
        instance of the transpositional reverser)
        """
        return {potential_quib: i for i, potential_quib in enumerate(self._get_quibs_in_args())}

    def _get_quib_ids_mask(self) -> np.ndarray:
        """
        Runs the function with each quib's ids instead of it's values
        """
        quibs_to_ids = self._get_quibs_to_ids()

        def replace_quib_with_id(obj):
            if isinstance(obj, Quib):
                return np.full(obj.get_shape().get_value(), quibs_to_ids[obj])
            return obj

        arguments = recursively_run_func_on_object(
            func=replace_quib_with_id,
            obj=self._args
        )
        return self._func(*arguments, *self._kwargs)

    def _get_empty_function_quib_result_with_value(self) -> np.ndarray:
        """
        Since we don't have the real result (may not have been computed yet),
        we create an empty result in same shape as the real result and set the new value in it
        """
        return create_empty_array_with_values_at_indices(self._function_quib.get_shape().get_value(),
                                                         indices=self._indices, value=self._value)

    def _get_bool_mask_representing_indices_in_result(self) -> np.ndarray:
        """
        Get a boolean mask representing where the indices that were changed are in the result- this will be in
        same shape as the result
        """
        return create_empty_array_with_values_at_indices(self._function_quib.get_shape().get_value(),
                                                         indices=self._indices,
                                                         value=True, empty_value=False)

    def _get_quibs_to_index_grids(self) -> Dict[Quib, np.ndarray]:
        """
        Get a mapping between quibs and their indices grid
        """
        return {
            quib: np.indices(quib.get_shape().get_value())
            for quib in self._get_quibs_in_args()
        }

    def _get_quibs_to_masks(self):
        """
        Get a mapping between quibs and a bool mask representing all the elements that are relevant to them in the
        result (for the particular given changed indices)
        """
        quibs_to_ids = self._get_quibs_to_ids()
        quibs_mask = self._get_quib_ids_mask()

        def _build_quib_mask(quib: Quib):
            quib_mask_on_result = np.equal(quibs_mask, quibs_to_ids[quib])
            return np.logical_and(quib_mask_on_result, self._get_bool_mask_representing_indices_in_result())

        return {
            quib: _build_quib_mask(quib)
            for quib in self._get_quibs_in_args()
        }

    def _get_quibs_to_indices_at_dimension(self, dimension: int):
        """
        Get a mapping of quibs to their referenced indices at a *specific dimension*
        """
        quibs_to_index_grids = self._get_quibs_to_index_grids()
        quibs_to_masks = self._get_quibs_to_masks()

        def replace_quib_with_index_at_dimension(q):
            if isinstance(q, Quib):
                return quibs_to_index_grids[q][dimension]
            return q

        new_arguments = recursively_run_func_on_object(
            func=replace_quib_with_index_at_dimension,
            obj=self._args
        )

        indices_res = self._func(*new_arguments, **self._kwargs)

        return {
            quib: indices_res[quibs_to_masks[quib]]
            for quib in self._get_quibs_in_args()
        }

    def _get_quibs_to_indices_in_quibs(self) -> Dict[Quib, np.ndarray]:
        """
        Get a mapping of quibs to the quib's indices that were referenced in `self._indices` (ie after reversal of the
        indices relevant to the particular quib)
        """
        max_shape_length = max([len(quib.get_shape().get_value())
                                for quib in self._get_quibs_in_args()])
        quibs_to_indices_in_quibs = {}
        for i in range(max_shape_length):
            quibs_to_indices_at_dimension = self._get_quibs_to_indices_at_dimension(i)

            for quib, index in quibs_to_indices_at_dimension.items():
                quibs_to_indices_in_quibs.setdefault(quib, []).append(index)

        return quibs_to_indices_in_quibs

    def _get_quibs_to_relevant_result_values(self) -> Dict[Quib, np.ndarray]:
        """
        Get a mapping of quibs to values that were both referenced in `self._indices` and came from the
        corresponding quib
        """
        quibs_to_masks = self._get_quibs_to_masks()
        return {
            quib: self._get_empty_function_quib_result_with_value()[quibs_to_masks[quib]]
            for quib in self._get_quibs_in_args()
        }

    def _get_reversals(self) -> List[Reversal]:
        quibs_to_indices_in_quibs = self._get_quibs_to_indices_in_quibs()
        quibs_to_results = self._get_quibs_to_relevant_result_values()

        return [
            Reversal(
                quib=quib,
                assignments=[
                    Assignment(quibs_to_indices_in_quibs[quib],
                               quibs_to_results[quib])
                ]
            )
            for quib in quibs_to_indices_in_quibs
        ]
