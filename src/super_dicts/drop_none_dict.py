from typing import Any, Union, Callable, Mapping


class DropNoneDict(dict):
    class _NoneIfLater:
        def __init__(i_self, value: Any, none_val: Any, plug_in: Callable = ...,
                plug_out: str = ...):
            i_self.value = value
            i_self.none_val = none_val
            i_self.plug_in = plug_in
            i_self.plug_out = plug_out

        def __call__(i_self, self) -> Any:
            return DropNoneDict.none_if(self, i_self.value, i_self.none_val,
                                        plug_in=i_self.plug_in,
                                        plug_out=i_self.plug_out)

    def none_if(self, value: Any, none_val: Any = ..., *,
                plug_in: Callable = ..., plug_out: str = ...) -> Any:
        """
        Changes a value to the correct "None" value of the containing dict if
        it meets specified criteria.

        :param value: The value that is being tested.
        :param none_val: The value that should also be "None".
        :param plug_in: A function that should be enacted on the value if it
            is not "None".
        :param plug_out: A function of the value, which should be called
            (without arguments) and the result of which should be returned
            if the value is not "None".
        """
        if type(self) is not DropNoneDict:
            # The below starts with self because of a messy situation which
            # occurs when none_if is used in a dictionary that isn't yet
            # constructed.
            return DropNoneDict._NoneIfLater(self, value, plug_in=plug_in,
                                             plug_out=plug_out)

        if value == none_val:
            return self._none_condition

        elif plug_in is not ...:
            return plug_in(value)

        elif plug_out is not ...:
            return getattr(value, plug_out)()

        return value

    def __set_check_func(self):
        """Sets the check_func that the DropNoneDict will use to check if
        values belong."""
        check_val = self._none_condition
        if check_val in [None, ..., True, False] or callable(check_val):
            self._check_func = lambda x: x is not check_val

        else:
            self._check_func = lambda x: x != check_val

    def __init__(self, map_: Mapping = ..., *, none_condition: Any = None,
                 **kwargs):
        """
        A dictionary that will automatically drop values of None.

        :param map_: A Mapping to be used to instantiate the dictionary.
        :param none_condition: What value gets auto-dropped? Defaults to None.
        :param kwargs: The kwargs representing key-val pairs to put in the
            dict.
        """
        self._none_condition = none_condition
        self.__set_check_func()
        dict.__init__(self, self._handle_gen_args(map_, kwargs))

    @property
    def none_condition(self) -> Any:
        return self._none_condition

    @none_condition.setter
    def none_condition(self, value: Any):
        self._none_condition = value
        self.__set_check_func()

    def _handle_gen_args(self,
                         map_: Mapping = ...,
                         kwargs: dict = ...) -> dict:
        """Handles the args at __init__."""
        output = {}
        if map_ is not ...:
            output.update(self._filter_map(map_))

        if kwargs is not ...:
            output.update(self._filter_map(kwargs))

        return output

    def _filter_map(self, map_: Union[Mapping, dict]) -> dict:
        """Filters out bad args from map_ and adds the rest."""
        output = {}
        for key, val in map_.items():
            if type(val) is DropNoneDict._NoneIfLater:
                val = val(self)

            if self._check_func(val):
                output[key] = val

        return output

    def __setitem__(self, k, v):
        if not self._check_func(v):
            if k in self:
                del self[k]

        else:
            dict.__setitem__(self, k, v)

    def update(self, map_: Mapping = ..., **kwargs):
        dict.update(self, self._handle_gen_args(map_, kwargs))
