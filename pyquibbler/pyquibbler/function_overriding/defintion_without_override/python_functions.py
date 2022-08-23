# flake8: noqa

from __future__ import annotations
from typing import List, TYPE_CHECKING

from pyquibbler.inversion import TranspositionalInverter
from pyquibbler.translation.translators import BackwardsTranspositionalTranslator, ForwardsTranspositionalTranslator
from pyquibbler.translation.translators.shape_only.shape_only_translators import \
    BackwardsShapeOnlyPathTranslator, ForwardsShapeOnlyPathTranslator
from pyquibbler.inversion.inverters.casting_inverter import \
    StrCastingInverter, NumericCastingInverter, BoolCastingInverter
from pyquibbler.utilities.user_utils import identity_function_for_obj2quib

if TYPE_CHECKING:
    from pyquibbler.function_definitions.func_definition import FuncDefinition


def create_defintions_for_python_functions() -> List[FuncDefinition]:
    from pyquibbler.function_definitions.func_definition import create_func_definition
    return [
        create_func_definition(
            func=len,
            raw_data_source_arguments=[0],
            backwards_path_translators=[BackwardsShapeOnlyPathTranslator],
            forwards_path_translators=[ForwardsShapeOnlyPathTranslator]),

        *(create_func_definition(
            func=func,
            raw_data_source_arguments=[0],
            inverters=[inverter])
            for func, inverter in [

            (str,   StrCastingInverter),
            (int,   NumericCastingInverter),
            (float, NumericCastingInverter),
            (bool,  BoolCastingInverter),
        ]),

        *(create_func_definition(
            func=func,
            raw_data_source_arguments=[0],
            inverters=[TranspositionalInverter],
            backwards_path_translators=[BackwardsTranspositionalTranslator],
            forwards_path_translators=[ForwardsTranspositionalTranslator],
         )
             for func in [list, tuple, identity_function_for_obj2quib]),

        # TODO: need definition for dict (to have fully functional obj2quib inversion and translation)
    ]
