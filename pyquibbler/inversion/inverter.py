from __future__ import annotations
from abc import ABC, abstractmethod

from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.path.data_accessing import deep_assign_data_in_path


class Inverter(ABC):

    def __init__(self, func_call: FuncCall, assignment, previous_result):
        self._func_call = func_call
        self._assignment = assignment
        self._previous_result = previous_result

    @classmethod
    def from_(cls, func_call, assignment, previous_result):
        return cls(func_call, assignment, previous_result)

    @abstractmethod
    def get_inversals(self):
        pass

    def _get_result_with_assignment_set(self):
        return deep_assign_data_in_path(self._previous_result,
                                        self._assignment.path,
                                        self._assignment.value,
                                        should_copy_objects_referenced=True)