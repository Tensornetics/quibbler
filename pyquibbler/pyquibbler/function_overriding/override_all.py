from typing import List

from pyquibbler.function_definitions.definitions import add_definition_for_function
from pyquibbler.function_overriding.function_override import FuncOverride
from pyquibbler.function_overriding.non_quib_overrides import switch_widgets_to_quib_supporting_widgets, \
    override_clear_axes
from pyquibbler.function_overriding.defintion_without_override.python_functions import \
    create_defintions_for_python_functions
from pyquibbler.function_overriding.quib_overrides.operators.overrides import create_operator_overrides
from pyquibbler.function_overriding.quib_overrides.quib_methods import create_quib_method_overrides
from pyquibbler.function_overriding.third_party_overriding.numpy.overrides import create_numpy_overrides
from pyquibbler.function_overriding.third_party_overriding.graphics.overrides import create_graphics_overrides
from pyquibbler.project.jupyer_project.jupyter_project import create_jupyter_project_if_in_jupyter_lab
from pyquibbler.utils import ensure_only_run_once_globally


@ensure_only_run_once_globally
def override_all():
    """
    Override all relavent functions, both operators and third party, to support Quibs
    """
    create_jupyter_project_if_in_jupyter_lab()

    function_definitions = create_defintions_for_python_functions()
    for func_definition in function_definitions:
        add_definition_for_function(
            func=func_definition.func,
            func_definition=func_definition,
            module_or_cls=None,
        )

    function_overrides: List[FuncOverride] = [*create_operator_overrides(),
                                              *create_graphics_overrides(),
                                              *create_numpy_overrides(),
                                              *create_quib_method_overrides()]
    switch_widgets_to_quib_supporting_widgets()
    override_clear_axes()
    for func_override in function_overrides:
        maybe_create_quib = func_override.override()
        add_definition_for_function(
            func=func_override.original_func,
            func_definition=func_override.func_definition,
            module_or_cls=func_override.module_or_cls,
            func_name=func_override.func_name,
            quib_creating_func=maybe_create_quib)