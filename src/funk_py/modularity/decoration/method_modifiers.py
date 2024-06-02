from functools import wraps, update_wrapper
from typing import Hashable


def has_alternatives(name: Hashable, *more_names: str):
    def wrapper(funk: callable) -> callable:
        options = {name: funk}
        for _name in more_names:
            options[_name] = funk

        cur_funk = funk

        class AlternativeFunk:
            def __init__(self, method=None):
                update_wrapper(self, method)
                self._inst = None

            def __call__(self, *args, **kwargs):
                if self._inst is not None:
                    return cur_funk(self._inst, *args, **kwargs)

                return cur_funk(*args, **kwargs)

            def __get__(self, inst, owner):
                # This is how we know what class a the method belongs to, if necessary.
                if inst is not None:
                    self._inst = inst

                return self

            @staticmethod
            def set_alternative(name: Hashable):
                nonlocal cur_funk
                print(name)
                print(options.get(name))
                cur_funk = options[name]

            def alternative(self, name: Hashable, *more_names: str):
                def inner_wrapper(_funk: callable) -> callable:
                    options[name] = _funk
                    for _name in more_names:
                        options[_name] = _funk

                    return self

                return inner_wrapper

        return AlternativeFunk(funk)

    return wrapper
