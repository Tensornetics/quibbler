from pyquibbler.utilities.basic_types import Flag, Mutable

""" Debug """

DEBUG = Flag(False)

LOG_TO_STDOUT = Flag(False)

LOG_TO_FILE = Flag(False)

END_DRAG_IMMEDIATELY = Flag(False)  # Useful when debugging graphics inverse assignment

SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS = Flag(True)


""" Lazy """

LAZY = Flag(True)

GRAPHICS_LAZY = Flag(False)


""" Graphics """

PLOT_WITH_PICKER_TRUE_BY_DEFAULT = Flag(True)

# Effective number of pixels in mouse events. None for infinity
GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION = Mutable(1000)

WARN_ON_UNSUPPORTED_BACKEND = Flag(True)


""" Override dialog """

OVERRIDE_DIALOG_IN_SEPARATE_WINDOW = Flag(False)

OVERRIDE_DIALOG_AS_TEXT_FOR_GRAPHICS_ASSIGNMENT = Flag(False)

OVERRIDE_DIALOG_AS_TEXT_FOR_NON_GRAPHICS_ASSIGNMENT = Flag(True)


""" repr """

PRETTY_REPR = Flag(True)

REPR_RETURNS_SHORT_NAME = Flag(False)

REPR_WITH_OVERRIDES = Flag(True)

GET_VARIABLE_NAMES = Flag(True)


""" non-quiby functions """

LEN_BOOL_ETC_RAISE_EXCEPTION = Flag(True)

ITER_RAISE_EXCEPTION = Flag(False)

