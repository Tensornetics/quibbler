import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib import widgets

from pyquibbler import iquib
from tests.integration.quib.graphics.widgets.utils import count_redraws, quibbler_image_comparison


@pytest.fixture
def roi():
    return iquib(np.array([.2, .8, 0.2, 0.8]))


@pytest.fixture
def rectangle_selector(roi, axes):
    selector = widgets.RectangleSelector(axes, extents=roi)
    plt.pause(0.1)
    return selector


@quibbler_image_comparison(baseline_images=['move'])
def test_rectangle_selector_move(get_live_widgets, roi, rectangle_selector, get_axes_middle, create_button_press_event,
                                 create_motion_notify_event, create_button_release_event, get_only_live_widget,
                                 axes):
    middle_x, middle_y = get_axes_middle()
    axes_x, axes_y, width, height = axes.bbox.bounds
    new_x = axes_x + width * .7
    new_y = axes_y + height * .7

    with count_redraws(rectangle_selector):
        create_button_press_event(middle_x, middle_y)
        create_motion_notify_event(new_x, new_y)
        create_button_release_event(new_x, new_y)

    assert len(get_live_widgets()) == 1
    new_roi = roi.get_value()
    # We are apparently not exact and the values are coming out to be .399997 instead of .4, so we're rounding.
    # If this turns out to be a real issue, we need to fix and create regression around this
    new_roi = list(map(lambda x: round(x, 1), new_roi))
    assert np.array_equal(new_roi, [0.4, 1., 0.4, 1.])