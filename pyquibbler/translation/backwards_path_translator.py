from abc import abstractmethod

from typing import Dict, Optional, Tuple, Type

from pyquibbler.translation.source_func_call import SourceFuncCall
from pyquibbler.translation.types import Source
from pyquibbler.path.path_component import Path
from pyquibbler.path.utils import working_component


class BackwardsPathTranslator:
    """
    A backwards path translator knows how to translate a path in a FuncCall's result back into paths of the FuncCall's
    sources.
    Normally, you will create a backwardspathtranslator for a specific set of functions and then add it as the
    translator in the `function_overriding.third_party_overriding` package.
    """

    # Override this in your translator if you have the ability to translate without needing shape + type. If you can
    # only work without shape and type in specific situations,
    # raise `FailedToTranslateException` if you fail in order to attempt WITH shape + type
    SHOULD_ATTEMPT_WITHOUT_SHAPE_AND_TYPE = False

    def __init__(self, func_call: SourceFuncCall, shape: Optional[Tuple[int, ...]], type_: Optional[Type], path):
        self._func_call = func_call
        self._shape = shape
        self._path = path
        self._type = type_

    @property
    def _working_component(self):
        return working_component(self._path)

    @abstractmethod
    def translate_in_order(self) -> Dict[Source, Path]:
        """
        Translate the path back to a mapping between sources and their respective paths which have an equivalence to
        self._path
        """
        pass

    def translate_without_order(self) -> Dict[Source, Path]:
        """
        Just like translate_in_order, but without any necessity to have the path in a specific order- the default
        behavior is just to translate in order, but if you have the ability to translate out of order WITHOUT needing
        shape or type, then override this method.
        """
        return self.translate_in_order()