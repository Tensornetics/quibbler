import functools


def quibbler_user_function(evaluate_now=True, pass_quibs=False):
    """
    Decorate your function with this in order for quibbler to automatically unpack quibs sent as arguments to this
    function, while reruninng this function every time any argument quib changes.

    Any graphics created in this function will also be redrawn if any argument quib changes.

    :param evaluate_now: Should this function be run immediately (evaluate_now=False), or only when
     it's needed down the line?
    (evaluate_now=False) - if you do any graphics in this function you should probably set evaluate_now=False
    :param pass_quibs: Should this function receive quibs or their values?
    """
    from pyquibbler.quib.graphics import GraphicsFunctionQuib

    def _decorator(func):
        @functools.wraps(func)
        def _wrapper(*args, **kwargs):
            return GraphicsFunctionQuib.create(func=func, func_args=args, func_kwargs=kwargs, evaluate_now=evaluate_now,
                                               pass_quibs=pass_quibs)

        return _wrapper

    return _decorator
