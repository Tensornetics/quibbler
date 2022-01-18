from typing import Callable, Dict
from unittest.mock import Mock
from pytest import fixture, mark, raises

from pyquibbler.assignment import override_dialog, AssignmentCancelledByUserException


@fixture
def button_callbacks():
    return {}


def override_module_func(monkeypatch, module, overridden_name, replacement):
    assert hasattr(module, overridden_name), \
        f'We assume that the {module.__name__} module imports or defines {overridden_name}, ' \
        f'as we are trying to replace this function with a mock.'

    original = getattr(module, overridden_name)
    monkeypatch.setattr(module, overridden_name, replacement)
    return original


@fixture(autouse=True)
def override_create_button(monkeypatch, button_callbacks):
    def create_button_wrapper(ax, label, callback):
        button_callbacks[label] = callback
        return original(ax, label, callback)

    original = override_module_func(monkeypatch, override_dialog, 'create_button', create_button_wrapper)


def override_show_fig_with_button_press(monkeypatch, button_label: str, callbacks: Dict[str, Callable[[], None]]):
    mock = lambda fig, _choice_type: callbacks[button_label]()
    override_module_func(monkeypatch, override_dialog, 'show_fig', mock)


@fixture
def override_options():
    return [Mock(), Mock()]


@mark.parametrize('can_diverge', [True, False])
def test_override_dialog_cancel_button(monkeypatch, override_options, can_diverge, button_callbacks):
    override_show_fig_with_button_press(monkeypatch, 'Cancel', button_callbacks)
    with raises(AssignmentCancelledByUserException):
        override_dialog.choose_override_dialog(override_options, can_diverge)


@mark.parametrize('can_diverge', [True, False])
def test_override_dialog_override_button(monkeypatch, override_options, can_diverge, button_callbacks):
    override_show_fig_with_button_press(monkeypatch, 'Override', button_callbacks)
    result = override_dialog.choose_override_dialog(override_options, can_diverge)

    assert result.choice_type is override_dialog.OverrideChoiceType.OVERRIDE
    assert result.chosen_index == 0


def test_override_dialog_diverge_button(monkeypatch, override_options, button_callbacks):
    override_show_fig_with_button_press(monkeypatch, 'Diverge', button_callbacks)
    result = override_dialog.choose_override_dialog(override_options, True)

    assert result.choice_type is override_dialog.OverrideChoiceType.DIVERGE
