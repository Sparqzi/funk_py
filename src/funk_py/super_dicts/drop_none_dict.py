from typing import Any, Union, Callable, Mapping

from funk_py.super_dicts import main_logger
from funk_py.modularity.logging import logs_vars


class DropNoneDict(dict):
    class _NoneIfLater:
        @logs_vars(main_logger, 'i_self',
                   start_message='Creating new DropNoneDict._NoneIfLater...',
                   end_message='Created new DropNoneDict._NoneIfLater.',
                   start_message_level='info', end_message_level='info')
        def __init__(i_self, value: Any, none_val: Any, plug_in: Callable = ...,
                     plug_out: str = ...):
            i_self.value = value
            i_self.none_val = none_val
            i_self.plug_in = plug_in
            i_self.plug_out = plug_out

        @logs_vars(main_logger, 'i_self',
                   start_message='Attempting to calculate result of DropNoneDict._NoneIfLater...')
        def __call__(i_self, self) -> Any:
            main_logger.debug(f'Applied To: {self}')
            return DropNoneDict.none_if(self, i_self.value, i_self.none_val,
                                        plug_in=i_self.plug_in,
                                        plug_out=i_self.plug_out)

    @logs_vars(main_logger,
               start_message='Calling DropNoneDict.none_if...')
    def none_if(self, value: Any, none_val: Any = ..., *, plug_in: Callable = ...,
                plug_out: str = ...) -> Any:
        """
        Changes a value to the correct "None" value of the containing dict if it meets specified
            criteria.

        :param value: The value that is being tested.
        :param none_val: The value that should also be "None".
        :param plug_in: A function that should be enacted on the value if it is not "None".
        :param plug_out: A function of the value, which should be called (without arguments) and the
            result of which should be returned if the value is not "None".
        """
        if type(self) is not DropNoneDict:
            # The below starts with self because of a messy situation which occurs when none_if is
            # used in a dictionary that isn't yet constructed.
            main_logger.trace('none_if is not being called on a DropNoneDict instance, generating '
                              'a DropNoneDict._NoneIfLater...')
            return DropNoneDict._NoneIfLater(self, value, plug_in=plug_in,
                                             plug_out=plug_out)

        if value == none_val:
            main_logger.trace(f'value is equal to none_val. Returning'
                              f' _none_condition ({self._none_condition})...')
            return self._none_condition

        elif plug_in is not ...:
            main_logger.trace('plug_in is present, attempting plug_in with value...')
            try:
                output = plug_in(value)

            except Exception:
                main_logger.error(f'plug_in was attempted in none_if, but plugging {value} into '
                                  f'{plug_in} raised an exception.')
                raise

            main_logger.trace('Returning result...')
            return output

        elif plug_out is not ...:
            main_logger.trace('plug_out is present, attempting plug_out on value...')
            try:
                output = getattr(value, plug_out)()

            except AttributeError:
                main_logger.error(f'plug_out was attempted in none_if, but {value} did not have '
                                  f'the attribute {plug_out}')
                raise

            main_logger.trace('Returning result...')
            return output

        main_logger.trace('value should not be equated to None, returning value...')
        return value

    def __set_check_func(self):
        """Sets the check_func that the DropNoneDict will use to check if values belong."""
        main_logger.debug('Setting the check_func for a DropNoneDict...')
        check_val = self._none_condition
        main_logger.debug(f'check_val = {check_val}')
        if check_val in [None, ..., True, False] or callable(check_val):
            main_logger.trace('Since check_val is in [None, ..., True, False], the check should be '
                              'for the same item...')
            main_logger.trace('Setting _check_func to - lambda x: x is not check_val')
            self._check_func = lambda x: x is not check_val

        else:
            main_logger.trace('Since check_val is not in [None, ..., True, False], the check '
                              'should be for value only...')
            main_logger.trace('Setting _check_func to - lambda x: x != check_val')
            self._check_func = lambda x: x != check_val

        main_logger.debug('Done setting check_func for DropNoneDict.')

    @logs_vars(main_logger,
               start_message='Creating a new DropNoneDict...',
               end_message='Created new DropNoneDict.',
               start_message_level='info', end_message_level='info')
    def __init__(self, map_: Mapping = ..., *, none_condition: Any = None, **kwargs):
        """
        A dictionary that will automatically drop values of None.

        :param map_: A Mapping to be used to instantiate the dictionary.
        :param none_condition: What value gets auto-dropped? Defaults to None.
        :param kwargs: The kwargs representing key-val pairs to put in the dict.
        """
        self._none_condition = none_condition
        self.__set_check_func()
        main_logger.trace('Setting values...')
        dict.__init__(self, self._handle_gen_args(map_, kwargs))
        main_logger.trace('Values set.')

    @property
    def none_condition(self) -> Any: return self._none_condition

    @none_condition.setter
    def none_condition(self, value: Any):
        main_logger.info(f'Setting none_condition for a DropNoneDict to'
                         f' {value}...')
        self._none_condition = value
        self.__set_check_func()

    @logs_vars(main_logger,
               start_message='Handling general arguments and forming dictionary for '
                             'DropNoneDict...',
               end_message='General arguments handled.')
    def _handle_gen_args(self, map_: Mapping = ..., kwargs: dict = ...) -> dict:
        """Handles the args at __init__."""
        output = {}
        if map_ is not ...:
            main_logger.trace('map_ exists. Parsing and updating output...')
            output.update(self._filter_map(map_))

        if kwargs is not ...:
            main_logger.trace('kwargs exists. Parsing and updating output...')
            output.update(self._filter_map(kwargs))

        return output

    def _filter_map(self, map_: Union[Mapping, dict]) -> dict:
        """Filters out bad args from map_ and adds the rest."""
        main_logger.trace(f'Filtering out bad values from {map_}...')

        output = {}
        for key, val in map_.items():
            if type(val) is DropNoneDict._NoneIfLater:
                main_logger.trace(f'{key} has a DropNoneDict._NoneIfLater as its value. Finalizing '
                                  f'DropNoneDict._NoneIfLater...')
                val = val(self)

            if self._check_func(val):
                main_logger.trace(f'{val} does not equate to the current DropNoneDict\'s None. '
                                  f'Adding {key}: {val} to output...')
                output[key] = val

        main_logger.trace('Finished filtering out bad values. Returning filtered map...')
        return output

    def __setitem__(self, k, v):
        main_logger.debug(f'Setting key {k} to {v} in DropNoneDict...')

        if not self._check_func(v):
            main_logger.trace(f'Value is effectively None. Deleting key {k} if it exists...')
            if k in self:
                del self[k]

        else:
            main_logger.trace('Value is not effectively None. Proceeding...')
            dict.__setitem__(self, k, v)

    def update(self, map_: Mapping = ..., **kwargs):
        main_logger.debug(f'Updating DropNoneDict with {map_}')
        dict.update(self, self._handle_gen_args(map_, kwargs))
