from functools import wraps, update_wrapper
from typing import Hashable


def has_alternatives(name: Hashable, *more_names: str):
    """
    Gives a function the ability to have alternative versions which can be switched between at will.

    :param name: The name of the alternative for the initially-decorated function.
    :param more_names: Any other names desired to alias to this version of the function.
    """
    def wrapper(funk: callable) -> callable:
        options = {name: funk}
        for _name in more_names:
            options[_name] = funk

        class AlternativeFunk:
            def __init__(self, method=None):
                update_wrapper(self, method)
                self._inst = None
                self.cur_funk = funk
                self.cur_funks = {}

            def __call__(self, *args, **kwargs):
                if self._inst is not None:
                    return self.cur_funks[self._inst](self._inst, *args, **kwargs)

                return self.cur_funk(*args, **kwargs)

            def __get__(self, inst, owner):
                # This is how we know what class the method belongs to, if necessary.
                if inst is not None:
                    self._inst = inst
                    if inst not in self.cur_funks:
                        self.cur_funks[inst] = self.cur_funk

                else:
                    self._inst = None

                return self

            def set_alternative(self, name: Hashable):
                """
                Sets the alternative of the function to be used. Will throw an error if an invalid
                alternative is selected.

                :param name: The name of the desired alternative.
                """
                if self._inst is not None:
                    self.cur_funks[self._inst] = options[name]

                else:
                    self.cur_funk = options[name]

            def alternative(self, name: Hashable, *more_names: str):
                """
                Can be used to decorate other functions.

                **Example of Usage:**

                .. code-block:: python

                    @has_alternatives("llama")
                    def llama(shrub: str, /, age: int):
                        print(f'I am a llama. My favorite type of shrub is {shrub}.\n'
                              f'I am {age} years old.')

                    @llama.alternative("alpaca")
                    def alpaca(apple: str, /, age: int):
                        print(f'I am an alpaca. My favorite type of apple is {apple}.\n'
                              f'I am {age} years old.')

                .. warning::
                    While it is advised to only decorate functions with the same signature in this
                    fashion, it is not enforced. Please take this into consideration.

                :param name: The name to assign the alternative.
                :param more_names: Any other names desired to alias to this version of the function.
                """
                def inner_wrapper(_funk: callable) -> callable:
                    options[name] = _funk
                    for _name in more_names:
                        options[_name] = _funk

                    return self

                return inner_wrapper

        return AlternativeFunk(funk)

    return wrapper
