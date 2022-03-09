class Singleton(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance


class Default(Singleton):
    """
    default is a singleton instance which is used as a dummy value in quib assignments to indicate
    removal of overriding assignments.

    default allows removing quib assignments in any quib-assignment syntax, such as:

    quib[2:5] = default
    quib.assign(default)
    quib['year'] = default
    """


default = Default()