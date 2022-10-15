from abc import abstractmethod
from typing import Optional, Type, List

from pyquibbler.utilities.multiple_instance_runner import ConditionalRunner

from .exceptions import FailedToTypeTranslateException
from .run_conditions import TypeTranslateRunCondition
from .utils import get_representative_value_of_type, CannotFindRepresentativeValueForType

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.function_definitions.func_definition import FuncDefinition


class TypeTranslator(ConditionalRunner):
    """
    Translate data argument type to result type. If possible.
    """
    RUN_CONDITIONS: Optional[List[TypeTranslateRunCondition]] = None

    def __init__(self,
                 func_definition: 'FuncDefinition',
                 data_arguments_types: Optional[List[Type]],
                 ):
        self._func_definition = func_definition
        self._data_arguments_types = data_arguments_types

    @property
    def _func(self):
        return self._func_definition.func

    @abstractmethod
    def get_type(self) -> Optional[Type]:
        """
        Return the type of the result.
        Return None if the type cannot be determined without executing the function.
        """
        pass


class ElementwiseTypeTranslator(TypeTranslator):
    """
    Translate type for functions that work elementwise
    The type depends on the type of the data arguments. For example:
    type(np.sin(1)) -> np.floar64
    type(np.sin([1])) -> np.ndarray
    """

    RUN_CONDITIONS: Optional[List[TypeTranslateRunCondition]] = TypeTranslateRunCondition.WITH_ARGUMENTS_TYPES

    def get_type(self) -> Optional[Type]:

        try:
            representative_values = (get_representative_value_of_type(type_) for type_ in self._data_arguments_types)
        except CannotFindRepresentativeValueForType:
            raise FailedToTypeTranslateException(self._func)

        try:
            return self._func(*representative_values)
        except Exception:
            raise FailedToTypeTranslateException(self._func)
