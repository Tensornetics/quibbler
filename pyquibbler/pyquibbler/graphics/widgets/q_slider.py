from numbers import Number

from matplotlib.widgets import Slider, RangeSlider

from pyquibbler.assignment.rounding import round_to_num_digits
from pyquibbler.utilities.decorators import squash_recursive_calls
from .base_q_widget import QWidget


class QWidgetSlider(QWidget):
    """
    Base class for Quibbler Sliders
    """
    def __init__(self, ax, label, valmin, valmax, valinit, **kwargs):
        self.on_release = None
        self._drag_active = False
        super().__init__(ax, label, valmin, valmax, valinit, **kwargs)

    @property
    def drag_active(self):
        return self._drag_active

    @drag_active.setter
    def drag_active(self, value):
        if self._drag_active is value:
            return
        self._drag_active = value
        if not value and self.on_release:
            self.on_release(self.val)

    def _stepped_value(self, val):
        """Return *val* coerced to closest number in the ``valstep`` grid."""

        val = super()._stepped_value(val)
        if isinstance(self.valstep, Number):
            val = round_to_num_digits(val, 15)  # prevents values like 1.0000000000001
        return val

    # we drop drag events created during redraw due to continuous drag
    # otherwise, kernel can get stuck (observed in jupyterlab with tk backend).
    @squash_recursive_calls
    def set_val(self, val):
        with self.avoid_redraws_if_created_in_get_value_context():
            super().set_val(val)


class QSlider(QWidgetSlider, Slider):
    """
    Like Slider but with:
    * on_release callback, which is called when drag is released
    * rounding step_value

    """
    pass


class QRangeSlider(QWidgetSlider, RangeSlider):
    """
    Like RangeSlider but with:
    * on_release callback, which is called when drag is released
    * rounding step_value
    """
    pass
