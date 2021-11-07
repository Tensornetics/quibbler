from typing import Optional, List, Any

from matplotlib.widgets import Slider

from pyquibbler.quib import Quib
from pyquibbler.quib.utils import quib_method

from .widget_graphics_function_quib import WidgetGraphicsFunctionQuib
from ...assignment import PathComponent


class SliderGraphicsFunctionQuib(WidgetGraphicsFunctionQuib):
    """
    A quib representing a slider. Will automatically add a listener and update the relevant quib
    """
    WIDGET_CLS = Slider

    def _on_change(self, new_value: float):
        val = self._get_args_values().get('valinit')
        if isinstance(val, Quib):
            val.assign_value(new_value)
        else:
            # We only need to invalidate children if we didn't assign
            self.invalidate_and_redraw_at_path()

    def _invalidate_self(self, path: List[PathComponent]):
        # We don't want to invalidate a slider that is within dragging as we don't want to recreate the slider the user
        # is currently using (so as to allow dragging and so on)
        # Note that this fix will not work when the slider is within another graphicsfunctionquib
        if self._cache is not None and self._cache.get_value().drag_active:
            return
        return super(SliderGraphicsFunctionQuib, self)._invalidate_self(path)

    def _call_func(self, valid_path: Optional[List[PathComponent]]) -> Any:
        slider = super()._call_func(None)
        slider.on_changed(self._on_change)
        return slider

    @property
    @quib_method
    def val(self):
        return self.get_value().val
