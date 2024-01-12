from typing import Any, Callable, Optional, ParamSpec


Args = ParamSpec("Args")


class Singleton:
    def __init_subclass__(cls, **kwargs):
        def __new__(cls_):
            if not hasattr(cls_, 'instance'):
                cls_.instance = super().__new__(cls_)

            return cls_.instance

        def __str__(self) -> str:
            return kwargs['str_']

        def __repr__(self) -> str:
            return kwargs['repr_']

        cls.__new__ = __new__
        cls.__str__ = __str__
        cls.__repr__ = __repr__

        return cls


class Shareable:
    __slots__ = ('v',)

    def __init__(self, v):
        self.v = v


def pass_(x: Any) -> Any:
    return x


def simple_trinomial(check_func: Callable[[Any, Args], bool],
                     check_func2: Callable[[Any, Args], bool] = None) \
        -> Callable[[Any, Any, Args], Optional[bool]]:
    if check_func2 is None:
        def check_it(val1, val2, *args) -> Optional[bool]:
            if check_func(val1, *args):
                return check_func(val2, *args)

            if check_func(val2, *args):
                return False

            return ...

        return check_it

    def check_it(val1, val2, *args) -> Optional[bool]:
        if check_func(val1, *args):
            return check_func2(val2, *args)

        if check_func2(val2, *args):
            return False

        return ...

    return check_it
