from __future__ import annotations
from collections import defaultdict
from functools import partial
from matplotlib.backend_bases import PickEvent, MouseEvent, MouseButton

from typing import Any, List, Tuple, Union, Mapping
from pyquibbler.utilities.general_utils import Args

from pyquibbler.assignment import get_axes_x_y_tolerance, create_assignment, OverrideGroup, \
    get_override_group_for_quib_changes, AssignmentToQuib, Assignment
from pyquibbler.assignment.utils import convert_scalar_value
from pyquibbler.path import PathComponent, Paths, deep_get
from .graphics_inverse_assigner import graphics_inverse_assigner

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib

from numpy import unravel_index


def _is_arg_str(arg):
    from pyquibbler.quib.quib import Quib
    if isinstance(arg, Quib):
        arg = arg.get_value()
    return isinstance(arg, str)


def get_xdata_arg_indices_and_ydata_arg_indices(args: Args) -> Tuple[List[int], List[int]]:
    """
    Gets a list of indices of arguments referencing `xdata`s, and a list of indices of arguments referencing `ydata`

    There are a few options for how arguments can be built for plot

    A. (ydata)
    B. (ydata, fmt)
    C. (xdata, ydata, [fmt], xdata, ydata...)

    Where C above is essentially a combination of cases where fmt is optional
    """

    x_data_arg_indexes = []
    y_data_arg_indexes = []

    # We have `self` (Axes) as arg 0

    if len(args) == 2:
        return [], [1]

    if len(args) == 3:
        if _is_arg_str(args[2]):
            return [], [1]

    i = 1
    while i < len(args):
        step = 2
        potential_fmt_index = i + 2
        if potential_fmt_index < len(args) and _is_arg_str(args[potential_fmt_index]):
            step += 1
        x_data_arg_indexes.append(i)
        y_data_arg_indexes.append(i + 1)

        i += step

    return x_data_arg_indexes, y_data_arg_indexes


def get_quibs_to_paths_affected_by_event(args: List[Any], arg_indices: List[int],
                                         artist_index: int, data_indices: Any) -> Mapping[Quib, Paths]:
    from pyquibbler.quib.quib import Quib
    quibs_to_paths = defaultdict(list)
    for arg_index in arg_indices:
        arg = args[arg_index]
        if isinstance(arg, Quib):
            # Support indexing of lists when more than one marker is dragged
            shape = arg.get_shape()
            for data_index in data_indices:
                if artist_index is not None:
                    # for plot:
                    if len(shape) == 0:
                        path = []
                    elif len(shape) == 1:
                        path = [PathComponent(data_index)]
                    else:
                        assert len(shape) == 2, 'Matplotlib is not supposed to support plotting 3d data'
                        path = [PathComponent(data_index),
                                # Plot args should be array-like, so quib[0].get_type() should be representative
                                PathComponent(artist_index)]
                else:
                    # for scatter:
                    path = [PathComponent(unravel_index(data_index, shape))]
                quibs_to_paths[arg].append(path)
        elif isinstance(arg, list):
            for data_index in data_indices:
                quib = arg[data_index]
                if isinstance(quib, Quib):
                    quibs_to_paths[quib].append([])

    return quibs_to_paths


def get_overrides_for_event(args: List[Any], arg_indices: List[int], artist_index: int, data_indices: Any,
                            value: Any, tolerance: Any):
    """
    Assign data for an axes (x or y) to all relevant quib args
    """
    # mouse_event.xdata and mouse_event.ydata can be None if the mouse is outside the figure
    if value is None:
        return []

    quibs_to_paths = get_quibs_to_paths_affected_by_event(args, arg_indices, artist_index, data_indices)

    overrides = []
    for quib, paths in quibs_to_paths.items():
        for path in paths:
            current_value = deep_get(quib.handler.get_value_valid_at_path(path), path)
            # we cast value and the tolerance by current value. so datetime or int work as expected:
            assignment = create_assignment(value, path, tolerance,
                                           convert_func=partial(convert_scalar_value, current_value))
            overrides.append(AssignmentToQuib(quib, assignment))
    return overrides


def get_override_removals_for_event(args: List[Any], arg_indices: List[int], artist_index: int, data_indices: Any):
    """
    Assign data for an axes (x or y) to all relevant quib args
    """
    quibs_to_paths = get_quibs_to_paths_affected_by_event(args, arg_indices, artist_index, data_indices)
    return [AssignmentToQuib(quib, Assignment.create_default(path))
            for quib, paths in quibs_to_paths.items() for path in paths]


def get_override_group_by_indices(x_arg_indices: List[int], y_arg_indices: List[int], artist_index: Union[None, int],
                                  pick_event: PickEvent, mouse_event: MouseEvent, args: List[Any]) -> OverrideGroup:
    indices = pick_event.ind
    if pick_event.mouseevent.button is MouseButton.RIGHT:
        arg_indices = x_arg_indices + y_arg_indices
        changes = get_override_removals_for_event(args, arg_indices, artist_index, indices)
    else:
        tolerance_x, tolerance_y = get_axes_x_y_tolerance(pick_event.artist.axes)
        changes = [*get_overrides_for_event(args, x_arg_indices, artist_index, indices,
                                            mouse_event.xdata, tolerance_x),
                   *get_overrides_for_event(args, y_arg_indices, artist_index, indices,
                                            mouse_event.ydata, tolerance_y)]
    return get_override_group_for_quib_changes(changes)


@graphics_inverse_assigner(['Axes.plot'])
def get_override_group_for_axes_plot(pick_event: PickEvent, mouse_event: MouseEvent, args: List[Any]) \
        -> OverrideGroup:
    x_arg_indices, y_arg_indices = get_xdata_arg_indices_and_ydata_arg_indices(tuple(args))
    artist_index = pick_event.artist._index_in_plot
    return get_override_group_by_indices(x_arg_indices, y_arg_indices, artist_index, pick_event, mouse_event, args)


@graphics_inverse_assigner(['Axes.scatter'])
def get_override_group_for_axes_scatter(pick_event: PickEvent, mouse_event: MouseEvent, args: List[Any]) \
        -> OverrideGroup:
    x_arg_indices, y_arg_indices = [1], [2]
    artist_index = None
    return get_override_group_by_indices(x_arg_indices, y_arg_indices, artist_index, pick_event, mouse_event, args)
