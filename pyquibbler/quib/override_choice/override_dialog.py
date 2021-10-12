from __future__ import annotations
import matplotlib.pyplot as plt
from dataclasses import dataclass
from functools import partial
from matplotlib.axes import Axes
from matplotlib.backend_bases import Event
from matplotlib.widgets import RadioButtons, Button
from typing import List, Callable, Optional, TYPE_CHECKING
from enum import Enum

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.utils import Flag

if TYPE_CHECKING:
    from pyquibbler.quib import Quib


@dataclass
class AssignmentCancelledByUserException(PyQuibblerException):
    pass


class SelectedIndexExposingRadioButtons(RadioButtons):
    """
    Radio buttons that expose the selected index
    """

    def __init__(self, ax: Axes, labels: List[str], active=0):
        super().__init__(ax, labels, active=active)
        self.selected_index = active

    def set_active(self, index: int):
        self.selected_index = index
        super().set_active(index)


class OverrideChoiceType(Enum):
    OVERRIDE = 0
    DIVERGE = 1


@dataclass()
class OverrideChoice:
    """
    Result of a choice between possible overrides.
    """
    choice_type: OverrideChoiceType
    chosen_index: Optional[int] = None

    def __post_init__(self):
        if self.choice_type is OverrideChoiceType.OVERRIDE:
            assert self.chosen_index is not None


def create_button(ax: Axes, label: str, callback: Callable[[Event], None]) -> Button:
    button = Button(ax, label)
    button.on_clicked(callback)
    return button


def show_fig(fig):
    """
    Show the given figure and wait until it is closed.
    """
    closed = Flag(False)
    fig.canvas.mpl_connect('close_event', lambda _event: closed.set(True))
    fig.show()
    while not closed:
        plt.pause(0.1)


def choose_override_dialog(options: List[Quib], can_diverge: bool) -> OverrideChoice:
    """
    Open a popup dialog to offer the user a choice between override options.
    If can_diverge is true, offer the user to diverge the override instead of choosing an override option.
    """
    # Used to keep references to the widgets so they won't be garbage collected
    widgets = []
    fig = plt.figure()
    grid = fig.add_gridspec(6, 6)

    radio_ax = fig.add_subplot(grid[:-1, :])
    radio = SelectedIndexExposingRadioButtons(radio_ax, [f'Override {quib.pretty_repr()}' for quib in options])
    widgets.append(radio)  # This is not strictly needed but left here to prevent a bug

    choice_type = None

    def button_callback(button_choice: OverrideChoiceType, _event):
        nonlocal choice_type
        choice_type = button_choice
        plt.close(fig)

    button_specs = [('Cancel', None),
                    ('Override', OverrideChoiceType.OVERRIDE)]
    if can_diverge:
        button_specs.append(('Diverge', OverrideChoiceType.DIVERGE))

    for i, (label, button_choice) in enumerate(button_specs):
        ax = fig.add_subplot(grid[-1, -i - 1])
        button = create_button(ax, label, partial(button_callback, button_choice))
        widgets.append(button)

    show_fig(fig)
    if choice_type is None:
        raise AssignmentCancelledByUserException()
    return OverrideChoice(choice_type, radio.selected_index)
