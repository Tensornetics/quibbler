from __future__ import annotations

import contextlib
import weakref

from typing import Set, Dict, Optional
from matplotlib.figure import Figure
from matplotlib.pyplot import fignum_exists
from matplotlib._pylab_helpers import Gcf
from matplotlib.pyplot import get_backend

from pyquibbler.debug_utils import timeit

from .graphics_update import GraphicsUpdateType

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib

QUIBS_TO_REDRAW: Dict[GraphicsUpdateType, weakref.WeakSet[Quib]] = {GraphicsUpdateType.DRAG: weakref.WeakSet(),
                                                                    GraphicsUpdateType.DROP: weakref.WeakSet()}
QUIBS_TO_NOTIFY_OVERRIDING_CHANGES: weakref.WeakSet[Quib] = weakref.WeakSet()
IN_AGGREGATE_REDRAW_MODE = False
IN_DRAGGING_MODE = False


@contextlib.contextmanager
def aggregate_redraw_mode(temporarily: bool = False):
    """
    In aggregate redraw mode, no axeses will be redrawn until the end of the context manager

    is_dragging:
        True: only update GraphicsUpdateType.DRAG and notify of overriding changes (so ipywidgets are also updated)
        False: like above and also update GraphicsUpdateType.DROP
        None: do not update any graphics and do not notify
    """
    global IN_AGGREGATE_REDRAW_MODE
    if IN_AGGREGATE_REDRAW_MODE:
        yield
    else:
        IN_AGGREGATE_REDRAW_MODE = True
        try:
            yield
        finally:
            IN_AGGREGATE_REDRAW_MODE = False
        if not temporarily:
            _redraw_quibs_with_graphics(GraphicsUpdateType.DRAG)
            if not is_dragging():
                _redraw_quibs_with_graphics(GraphicsUpdateType.DROP)
            _notify_of_overriding_changes()


def start_dragging():
    from pyquibbler import Project
    global IN_DRAGGING_MODE
    if IN_DRAGGING_MODE:
        return
    IN_DRAGGING_MODE = True
    project = Project.get_or_create()
    project.push_empty_group_to_undo_stack()
    project.start_pending_undo_group()


def end_dragging():
    from pyquibbler import Project
    global IN_DRAGGING_MODE
    if not IN_DRAGGING_MODE:
        return
    IN_DRAGGING_MODE = False
    _redraw_quibs_with_graphics(GraphicsUpdateType.DROP)
    project = Project.get_or_create()
    project.remove_last_undo_group_if_empty()
    project.set_undo_redo_buttons_enable_state()


def is_dragging():
    return IN_DRAGGING_MODE


@contextlib.contextmanager
def skip_canvas_draws(should_skip: bool = True):

    original_canvas_draw = None
    if should_skip:
        figure_managers = Gcf.get_all_fig_managers()
        if figure_managers:

            def _skip_draw(*args, **kwargs):
                return

            canvas_class = type(figure_managers[0].canvas)
            original_canvas_draw = canvas_class.draw
            canvas_class.draw = _skip_draw
    try:
        yield
    finally:
        if original_canvas_draw is not None:
            canvas_class.draw = original_canvas_draw


def _redraw_quibs_with_graphics(graphics_update: GraphicsUpdateType):
    global QUIBS_TO_REDRAW
    quib_refs = QUIBS_TO_REDRAW[graphics_update]
    with timeit("quib redraw", f"redrawing {len(quib_refs)} quibs"), skip_canvas_draws():
        for quib in quib_refs:
            quib.handler.reevaluate_graphic_quib()

    figures = {figure for quib in quib_refs for figure in quib.handler.get_figures() if figure is not None}

    redraw_figures(figures)
    quib_refs.clear()


def _notify_of_overriding_changes():
    with timeit("override_notify", f"notifying overriding changes for {len(QUIBS_TO_NOTIFY_OVERRIDING_CHANGES)} quibs"):
        for quib in QUIBS_TO_NOTIFY_OVERRIDING_CHANGES:
            quib.handler.on_overrides_changes()

    QUIBS_TO_NOTIFY_OVERRIDING_CHANGES.clear()


def redraw_quib_with_graphics_or_add_in_aggregate_mode(quib: Quib, graphics_update: GraphicsUpdateType):
    global QUIBS_TO_REDRAW
    if not (graphics_update == GraphicsUpdateType.DRAG or graphics_update == GraphicsUpdateType.DROP):
        return

    QUIBS_TO_REDRAW[graphics_update].add(quib)
    if not IN_AGGREGATE_REDRAW_MODE:
        _redraw_quibs_with_graphics(graphics_update)


def notify_of_overriding_changes_or_add_in_aggregate_mode(quib: Quib):
    global QUIBS_TO_NOTIFY_OVERRIDING_CHANGES
    QUIBS_TO_NOTIFY_OVERRIDING_CHANGES.add(quib)
    if not IN_AGGREGATE_REDRAW_MODE:
        _notify_of_overriding_changes()


def redraw_canvas(canvas):
    """
    Redraw a specified canvas
    """
    if get_backend() == 'TkAgg':
        # `canvas.start_event_loop(0.001)` works with tk, but cause sometimes the kernel to
        # get stuck when dragging rectangle_selector in jupyterlab.
        # canvas.draw() works better with tk
        canvas.draw()
    else:
        # `canvas.draw()` does not work with osx. it just doesn't redraw.
        # based on https://matplotlib.org/stable/api/animation_api.html, we use instead:
        canvas.draw_idle()
        canvas.start_event_loop(0.001)


def redraw_figures(figures: Set[Figure]):
    """
    Actual redrawing of figure- this should be WITHOUT rendering anything except for the new artists
    """
    canvases = {figure.canvas for figure in figures if fignum_exists(figure.number)}
    with timeit("redraw", f"redraw {len(figures)} figures"):
        for canvas in canvases:
            redraw_canvas(canvas)
