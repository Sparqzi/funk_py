from timeit import timeit
from typing import Dict, Set, Union, Tuple, Any, Iterable


def too_slow_func(desc: str):
    def too_slow(number: int, max_duration: float, t1, t2, func: callable):
        duration = timeit(lambda: func(t1, t2), number=number)
        assert duration < max_duration, \
            (f'{func.__name__} worked for two {desc}, but did not perform'
             f' adequately with regards to speed. {desc.title()} compared'
             f' were:\n'
             f'{repr(t1)}\n'
             f'{repr(t2)}\n'
             f'{number} iterations were performed.\n'
             f'Expected rate was {number / max_duration} executions per'
             f' second.\n'
             f'Actual rate was {number / duration} executions per second.')

    return too_slow


def build_nested_dict(callbacks: Dict[int, dict] = None,
                      inner_callbacks: Set[int] = None,
                      *, base: Union[Iterable[Tuple[Any, Any]], int],
                      callback: int = None,
                      key1: Any = None, instruction1: dict = None,
                      key2: Any = None, instruction2: dict = None):
    builder = dict(base)
    if callback is not None:
        callbacks[callback] = builder

    if key1:
        type_ = instruction1.get('type', dict)
        builder[key1] = build_nest(type_, callbacks, inner_callbacks,
                                   **instruction1)

    if key2:
        type_ = instruction2.pop('type', dict)
        builder[key2] = build_nest(type_, callbacks, inner_callbacks,
                                   **instruction2)

    return builder


def build_nested_sequence(type_: type,
                          callbacks: Dict[int, Union[tuple, list]] = None,
                          inner_callbacks: Set[int] = None,
                          *, base: Union[tuple, int],
                          callback: int = None,
                          point1: int = None, instruction1: dict = None,
                          point2: int = None, instruction2: dict = None):
    if point1:
        builder = list(base[:point1])
        if callback is not None:
            callbacks[callback] = builder

        type__ = instruction1.pop('type', type_)
        builder.append(
            build_nest(type__, callbacks, inner_callbacks, **instruction1))
        if point2:
            if point2 == -1:
                builder.extend(base[point1:])
                type__ = instruction2.pop('type', type_)
                builder.append(
                    build_nest(type__, callbacks, inner_callbacks,
                               **instruction2))

            else:
                builder.extend(base[point1:point2])
                type__ = instruction2.pop('type', type_)
                builder.append(
                    build_nest(type__, callbacks, inner_callbacks,
                               **instruction2))
                builder.extend(base[point2:])

        else:
            builder.extend(base[point1:])

        if callback is not None and callback in inner_callbacks:
            return builder

        return type_(builder)

    if callback is not None:
        callbacks[callback] = type_(base)

    return type_(base)


def build_nest(type_: type, callbacks: Dict[int, Union[tuple, list]] = None,
               inner_callbacks: Set[int] = None, *,
               base: Union[tuple, int], callback: int = None,
               point1: int = None, key1: Any = None, instruction1: dict = None,
               point2: int = None, key2: Any = None, instruction2: dict = None):
    if callbacks is None:
        callbacks = {}
        inner_callbacks = set()

    if type(base) is int:
        inner_callbacks.add(base)
        return callbacks[base]

    if type_ in (list, tuple):
        return build_nested_sequence(type_, callbacks, inner_callbacks,
                                     base=base, callback=callback,
                                     instruction1=instruction1, point1=point1,
                                     instruction2=instruction2, point2=point2)
    else:
        return build_nested_dict(callbacks, inner_callbacks,
                                 base=base, callback=callback,
                                 instruction1=instruction1, key1=key1,
                                 instruction2=instruction2, key2=key2)
