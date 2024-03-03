from functools import wraps
from typing import Mapping, Any, Callable, Iterable

from funk_py.modularity.logging import make_logger

main_logger = make_logger('super_dicts', 'SUPER_DICT_LOGGER',
                          default_level='warning', TRACE=5)

from funk_py.super_dicts.drop_none_dict import DropNoneDict      # noqa
from funk_py.super_dicts.list_dict import ListDict               # noqa
from funk_py.super_dicts.multi_value_dict import MultiValueDict  # noqa


@wraps(DropNoneDict.__init__)
def drop_none_dict(map_: Mapping = ..., *, none_condition: Any = None,
                   **kwargs) -> DropNoneDict:
    """
    Creates a dictionary that will automatically drop values of None. Pair with
    none_if function to drop default values that aren't covered by the standard
    default in the dictionary.

    :param map_: A Mapping to be used to instantiate the dictionary.
    :param none_condition: What value gets auto-dropped? Defaults to None.
    :param kwargs: The kwargs representing key-val pairs to put in the
        dict.
    """
    return DropNoneDict(map_, none_condition=none_condition, **kwargs)


def none_if(value: Any, none_val: Any = ..., *, plug_in: Callable = ...,
            plug_out: str = ...):
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
    return DropNoneDict.none_if(value, none_val, plug_in, plug_out)


def multi_key_dict(map_: Mapping = ..., **kwargs) -> MultiKeyDict:
    """
    Checks a mapping for keys using the same value and assigns them a
    reference to a holder for the value.

    :param map_: A mapping
    :param kwargs: Keywords to use to build a mapping or add on to a
        mapping.
    """
    return MultiKeyDict(map_, **kwargs)


def multi_value_dict(map_: Mapping = ..., **kwargs) -> MultiValueDict:
    """
    A dictionary where each key can have multiple values. Values for this
    dictionary should be hashable.

    :param map_: Initialize dictionary from mappings.

    :param kwargs: Initialize dictionary from key-val pairs.
    """
    return MultiValueDict(map_, **kwargs)


def list_dict(key_function: Callable, values: Iterable = None):
    """
    A list that sort of acts like a dictionary...

    :param key_function: The function that should be called on each item
        to get its appropriate key.
    :param values: The values that should be put in the list.
    """
    return ListDict(key_function, values)
