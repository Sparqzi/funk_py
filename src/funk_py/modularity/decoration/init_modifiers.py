from functools import wraps
from typing import Callable, Iterable, overload, Union
import inspect


__MODIFIER = 'inner_method'


def __mm(func: Callable, type_: type) -> Callable:
    def wrapper(inner_func: Callable) -> Callable:
        if ('.' in func.__qualname__ and '<locals>' not in func.__qualname__) \
                or (__MODIFIER in func.__qualname__ and func.from_class):
            # For methods that need a self...
            @wraps(func)
            def inner_method(*args, **kwargs):
                if len(args) > 1 and type(args[1]) is type_:
                    i_args, i_kwargs = inner_func(*args[1:], **kwargs)
                    return func(args[0], *i_args, **i_kwargs)

                return func(*args, **kwargs)

            inner_method.__signature__ = inspect.signature(func)
            inner_method.from_class = True
            return inner_method

        # For methods that don't need a self...
        @wraps(func)
        def inner_method(*args, **kwargs):
            if type(args[0]) is type_:
                i_args, i_kwargs = inner_func(*args, **kwargs)
                return func(*i_args, **i_kwargs)

            return func(*args, **kwargs)

        inner_method.__signature__ = inspect.signature(func)
        inner_method.from_class = False
        return inner_method

    return wrapper


def listable(allow_too_many: bool = False) -> Callable:
    """
    Make it so that a function can take a list of its arguments as the only
    argument. It will still be able to take its normal arguments.

    :param allow_too_many: Should the function ignore extra args?
    """
    def wrapper_wrapper(func: Callable):
        @overload
        def list_method(l: list): ...

        if allow_too_many:
            # Determine the number of args the function can accept.
            func_length = len(inspect.signature(func).parameters)

            # Make sure arg count is limited per total args in the function.
            # only return the args.
            @__mm(func, list)
            def list_method(*args, **kwargs):
                # Make sure there was only one argument...
                if len(args) + len(kwargs) == 1:
                    return args[0][: func_length], {}

                # if not, don't do anything special.
                return args, kwargs

        else:
            # Only return the args.
            @__mm(func, list)
            def list_method(*args, **kwargs):
                # Make sure there was only one argument...
                if len(args) + len(kwargs) == 1:
                    return args[0], {}

                # if not, don't do anything special.
                return args, kwargs

        return list_method

    # If the function to be decorated was passed right in...
    if callable(allow_too_many):
        return wrapper_wrapper(allow_too_many)

    # Otherwise
    return wrapper_wrapper


def dictable(extra_routes: dict = None, slices: dict = None,
             needs: Iterable = None, needs_not: Iterable = None):
    """
    Make it so that a function can take a dictionary of its arguments as a
    single argument. It will still be able to take its normal arguments.

    :param extra_routes: Any extra key aliases that should be used to convert
        dictionaries.
    :param slices: Any slices of keys which should be combined into a single
        input. This has limited testing, so avoid use if possible.
    :param needs: Keys that must be in the dictionary in order for it to
        be interpreted as a dict instantiation. This is only needed if the
        first argument of the original function can be a dictionary, and the
        function can be called with only one argument.
    :param needs_not: Keys that must not be in the dictionary in order for it
        to be interpreted as a dict instantiation. This is only needed if the
        first argument of the original function can be a dictionary, and the
        function can be called with only one argument.
    """
    def wrapper_wrapper(func: Callable):
        @overload
        def dict_method(d: dict): ...

        # Get the arguments of the source function and make sure they are
        # aliased by default.
        func_args = inspect.signature(func)
        match_dict = {arg: arg for arg in func_args.parameters.keys()}
        if extra_routes is not None:
            match_dict.update(extra_routes)

        if needs_not is None:
            need_check = (lambda d: d) if needs is None \
                else (lambda d: all(k in d for k in needs))

        else:
            need_check = (lambda d: not any(k in d for k in needs_not)) \
                if needs is None \
                else (lambda d: not any(k in d for k in needs_not)
                      and all(k in d for k in needs))

        # Slices check is extra. Don't include it if unneeded.
        if slices is None:
            # Used to transform args if the type check is a dictionary.
            @__mm(func, dict)
            def dict_method(*args, **kwargs):
                # Make sure there was only one argument...
                d = args[0]
                if len(args) + len(kwargs) == 1 and need_check(d):
                    builder = {match_dict[key]: val
                               for key, val
                               in d.items()
                               if key in match_dict}

                    return [], builder

                # if not, don't do anything special.
                return args, kwargs

        else:
            # Used to transform args if the type check is a dictionary.
            @__mm(func, dict)
            def dict_method(*args, **kwargs):
                # Make sure there was only one argument...
                d = args[0]
                if len(args) + len(kwargs) == 1 and need_check(d):
                    builder = {match_dict[key]: val
                               for key, val
                               in d.items()
                               if key in match_dict}
                    # Handle feeding slices of the dictionary to defined
                    # parameters.
                    for key, val in slices.items():
                        c = {}
                        for k in key:
                            if k in d:
                                c[k] = d[k]

                        builder[val] = c

                    return [], builder

                # if not, don't do anything special.
                return args, kwargs

        return dict_method

    # If the function to be decorated was passed right in...
    if callable(t := extra_routes):
        extra_routes = None
        return wrapper_wrapper(t)

    # otherwise...
    return wrapper_wrapper


def class_init(*overrides: Union[str, Callable]) -> Callable:
    """
    Make it so that a function assigns arguments directly to the same-named
    properties of its containing class.

    :param overrides: Any names that should not be handled directly from the
        decorator.
    """
    def wrapper_wrapper(func: Callable):
        func_args = inspect.signature(func).parameters
        func_arg_keys = list(func_args.keys())[1:]
        valid_func_args = {i: func_arg_keys[i]
                           for i
                           in range(len(func_arg_keys))
                           if func_arg_keys[i] not in overrides}
        func_arg_values = list(func_args.values())[1:]
        valid_func_defaults = {func_arg_keys[i]: func_arg_values[i].default
                               for i
                               in range(len(func_arg_values))
                               if func_arg_values[i].default
                               is not func_arg_values[i].empty}
        del func_arg_values
        func_arg_keys = list(valid_func_args.values())

        @wraps(func)
        def class_init_method(self, *args, **kwargs):
            unfilled = func_arg_keys.copy()
            for i in range(len(args)):
                if i in valid_func_args:
                    setattr(self, valid_func_args[i], args[i])
                    unfilled.remove(valid_func_args[i])

            kwargs.update({key: val
                           for key, val
                           in valid_func_defaults.items()
                           if key in unfilled
                           and key not in kwargs})

            for keyword, arg in kwargs.items():
                if keyword in func_arg_keys:
                    setattr(self, keyword, arg)
                    unfilled.remove(keyword)

            func(self, *args, **kwargs)

        return class_init_method

    # if the function to be decorated was passed right in...
    if callable(t := overrides[0]):
        overrides = []
        return wrapper_wrapper(t)

    # otherwise
    return wrapper_wrapper
