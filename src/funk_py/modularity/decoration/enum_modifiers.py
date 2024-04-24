from enum import Enum
from functools import wraps
from inspect import signature
from typing import Type, Callable


def converts_enums(func: Callable):
    sig = signature(func)
    # Determine which arguments should be enums in advance...
    converter_dict = {}
    for param_name, param in sig.parameters.items():
        param_type = param.annotation
        if isinstance(param_type, Type) and issubclass(param_type, Enum):
            converter_dict[param_name] = (param_type, {m.value: m for m in param_type})

    if not len(converter_dict):
        # Cover the case where - for whatever reason - someone used this to decorate a function with
        # no enumerable arguments. We don't want to introduce extra calculations that do nothing
        # (if we can avoid it reasonably).
        return func

    @wraps(func)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        for param_name, _def in converter_dict.items():
            _type, converter = _def
            val = bound.arguments[param_name]
            if not isinstance(val, _type):
                bound.arguments[param_name] = converter.get(val, None)

        return func(*bound.args, **bound.kwargs)

    return wrapper
