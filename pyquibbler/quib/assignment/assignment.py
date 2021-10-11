from __future__ import annotations
import numpy as np

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING, List, Union, Tuple

if TYPE_CHECKING:
    from ..quib import Quib

AssignmentPath = Union[str, Tuple, type(Ellipsis)]


PathComponent = Union[str, Tuple, type(Ellipsis)]


@dataclass
class Assignment:
    """
    A change performed on a quib.
    """
    value: Any
    path: List[AssignmentPath] = field(default_factory=list)

    def __eq__(self, other):
        if not isinstance(other, Assignment):
            return NotImplemented
        # array_equal works for all objects, and our value and paths might contain ndarrays
        return np.array_equal((self.value, self.paths), (other.value, other.paths))


@dataclass(frozen=True)
class QuibWithAssignment:
    """
    A quib together with it's assignment
    """
    quib: Quib
    assignment: Assignment

    def apply(self) -> None:
        self.quib.assign(self.assignment)

    def override(self):
        self.quib.override(self.assignment, allow_overriding_from_now_on=False)
