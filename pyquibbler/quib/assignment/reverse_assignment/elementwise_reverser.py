from typing import Any, List, Dict, Callable

import numpy as np

from pyquibbler.quib import Quib
from pyquibbler.quib.assignment.reverse_assignment.reverser import Reversal, Reverser
from .utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.utils import call_func_with_quib_values


def create_inverse_function_from_indexes_to_funcs(quib_argument_indexes_to_inverse_functions: Dict[int, Callable]):
    """
    Create an inverse function that will call actual inverse functions based on the index of the quib in the arguments
    """
    def _inverse(empty_result_with_values_at_indices: np.ndarray, args, kwargs, quib_to_change: Quib):
        quib_index = next(i for i, v in enumerate(args) if v is quib_to_change)
        inverse_func = quib_argument_indexes_to_inverse_functions[quib_index]
        new_args = list(args)
        new_args[quib_index] = empty_result_with_values_at_indices
        return call_func_with_quib_values(inverse_func, new_args, kwargs)
    return _inverse


class ElementWiseReverser(Reverser):
    """
    In charge of reversing all element-wise mathematical operation functions
    """

    # We use indexes instead of arg names because you cannot get signature from ufuncs (numpy functions)
    FUNCTIONS_TO_INVERSE_FUNCTIONS = {
        np.add: create_inverse_function_from_indexes_to_funcs(
            {
                i: np.subtract for i in range(2)
            }
        ),
        np.multiply: create_inverse_function_from_indexes_to_funcs(
            {
                i: np.divide for i in range(2)
            }
        ),
        np.subtract: create_inverse_function_from_indexes_to_funcs(
            {
                0: np.add,
                1: np.subtract
            }
        ),
        np.divide: create_inverse_function_from_indexes_to_funcs({
            0: np.multiply,
            1: np.divide
        })
    }

    SUPPORTED_FUNCTIONS = list(FUNCTIONS_TO_INVERSE_FUNCTIONS.keys())

    def _get_indexes_to_change(self, argument_quib: Quib, changed_index: Any):
        """
        Even though the operation is element wise, this does not necessarily mean that the final results shape is
        the same as the arguments' shape, as their may have been broadcasting. Given this, we take our argument quib
        and broadcast it's index grid to the shape of the result, so we can see the corresponding quib indices for the
        result indices
        """
        index_grid = np.indices(argument_quib.get_shape().get_value())
        broadcasted_grid = np.broadcast_to(index_grid, (index_grid.shape[0], *self._function_quib.get_shape().get_value()))
        return [
            dimension[changed_index]
            for dimension in broadcasted_grid
        ]

    def _get_reversals(self) -> List[Reversal]:
        quib_to_change = self._get_quibs_in_args()[0]
        empty_result_with_value = create_empty_array_with_values_at_indices(self._function_quib.get_shape().get_value(),
                                                                            self._indices, self._value)
        inverse_function = self.FUNCTIONS_TO_INVERSE_FUNCTIONS[self._func]
        new_quib_argument_value = inverse_function(empty_result_with_value, self._args, self._kwargs,
                                                   quib_to_change)
        changed_indices = self._get_indexes_to_change(quib_to_change, self._indices)
        return [Reversal(
            quib=quib_to_change,
            assignments=[
                Assignment(changed_indices, new_quib_argument_value[self._indices])
            ]
        )]
