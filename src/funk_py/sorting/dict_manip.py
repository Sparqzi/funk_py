from copy import deepcopy
from typing import (Generator, Optional, Union, Any, Callable, Dict, Tuple, Iterable, Mapping,
                    Type, List)

from funk_py.modularity.basic_structures import pass_
from funk_py.modularity.logging import make_logger, logs_vars

main_logger = make_logger('dict_manip', env_var='DICT_MANIP_LOG_LEVEL', default_level='warning')


_skip_message = 'Skipped a key-val pair in convert_tuplish_dict '


def convert_tuplish_dict(data: Union[dict, list], pair_name: str = None, key_name: str = None,
                         val_name: str = None) -> dict:
    """
    Handles the conversion of data structured as either a dictionary or a list containing key-value
    pairs into a dictionary representation. The conversion process adheres to specific rules based
    on the following criteria:

    1. If ``pair_name`` is specified.
    2. If both ``key_name`` **and** ``val_name`` are specified.
        *Be aware that specifying only one of these will result in both being ignored.*
    3. If ``key_name`` is equal to ``val_name`` and both are specified.

    When ``pair_name`` is specified and ``key_name``, ``val_name``, or both are missing, the
    function conducts a depth-first search to locate a dictionary containing ``pair_name`` as a key.
    It traverses through lists and their nested lists to find the desired pairs. If a dictionary
    with ``pair_name`` as a key is found, the function inspects the corresponding value. If the
    value is a list, it identifies the lowest-level lists within it and constructs pairs using the
    :func:`~merge_tuplish_pair` function. If successful, this process is repeated for other lists.
    If elements in the list are dictionaries with only one key, the function delves deeper into
    them following the same search pattern.

    When both ``key_name`` and ``val_name`` are specified but ``pair_name`` is not, the search
    method depends on whether ``key_name`` equals ``val_nam``. If they are equal, the function
    performs the same search as it would for ``pair_name`` but searches for ``key_name`` instead.
    If they are unequal, it searches for a dictionary containing both ``key_name`` and ``val_name``
    in the same manner as for ``pair_name``. Once the target dictionary is found, the function
    evaluates only one pair from it. If the value under ``key_name`` is a list, it iterates
    through it to ensure there are no un-hashable values within, then constructs the pair using
    :func:`~merge_tuplish_pair`. This process is repeated for as many pairs as it can find.

    When ``pair_name``, ``key_name``, and ``val_name`` are all specified, the search method is the
    same as for ``pair_name`` until a dictionary containing ``pair_name`` is found. Once such a
    dictionary is found, the same process as when `key_name` and ``val_name`` are specified is
    attempted on the value under the ``pair_name`` key.

    If neither ``pair_name``, ``key_name``, nor ``val_name`` is specified, the search method
    attempts to find each lowest-level list just as it normally would when ``pair_name`` is the only
    value specified.

    .. note::
        When attempting to find a dictionary containing target key(s) :func:`convert_tuplish_dict`
        will stop at dictionaries containing more than one key if they do not contain the target
        key.

    :param data: The data to treat as a tuplish dict.
    :type data: Union[dict, list]
    :param pair_name: The name used to represent a pair. If omitted, will not expect pairs to be
        under keys.
    :type pair_name: str
    :param key_name: The name used to represent a key. If either this or ``val_name`` is omitted,
        neither will be used and pairs will be constructed using the best identifiable method.
    :type key_name: str
    :param val_name: The name used to represent a value. If either this or ``key_name`` is omitted,
        neither will be used and pairs will be constructed using the best identifiable method.
    :type val_name: str
    :return: A flat dictionary made of key-value pairs found in the given data.

    .. note::
        Please be aware that the returned dictionary may not be completely flat, as there is a
        chance of a value being under a path of keys.
    """
    builder = {}
    if pair_name is not None:
        if key_name is not None and val_name is not None:
            if key_name == val_name:
                _ctd_pair_search(data, pair_name, _ctd_search_when_skv, builder, key_name)

            else:
                _ctd_pair_search(data, pair_name, _ctd_search_when_dkv, builder, key_name, val_name)

        else:
            _ctd_pair_search(data, pair_name, _ctd_search_when_nkv, builder)

    elif key_name is not None and val_name is not None:
        if key_name == val_name:
            _ctd_search_when_skv(data, key_name, builder)

        else:
            _ctd_search_when_dkv(data, key_name, val_name, builder)

    else:
        _ctd_search_when_nkv(data, builder)

    return builder


def _ctd_is_good_key(key: Any) -> bool:
    try:
        hash(key)

    except TypeError as e:
        if 'unhashable type:' in str(e):
            main_logger.info(_skip_message + 'because the key was unhashable.')

        else:
            main_logger.info(_skip_message + f'for unexpected error. {e}')

        return False

    except Exception as e:
        main_logger.info(_skip_message + f'for unexpected error. {e}')
        return False

    return True


def _ctd_search_when_skv(data: Union[dict, list], key_name, builder):
    """_convert_tuplish_dict_search_when_same_key_and_value"""
    for pair in dive_to_dicts(data):
        if key_name in pair:
            pair = pair[key_name]
            if (isinstance(pair, list) and len(pair) > 1
                    and all(_ctd_is_good_key(key) for key in pair[:-1])):
                merge_tuplish_pair(pair, builder)

            else:
                main_logger.info(_skip_message + 'because it didn\'t look like a complete pair.')


def _ctd_search_when_dkv(data: Union[dict, list], key_name, val_name, builder):
    """_convert_tuplish_dict_search_when_diff_key_and_value"""
    for vals in dive_to_dicts(data):
        if key_name in vals and val_name in vals:
            key = vals[key_name]
            val = vals[val_name]
            if isinstance(key, list):
                if all(_ctd_is_good_key(k) for k in key):
                    pair = key + [val]
                    merge_tuplish_pair(pair, builder)

            elif _ctd_is_good_key(key):
                builder[key] = val


def _ctd_search_when_nkv(data: Union[dict, list], builder):
    """_convert_tuplish_dict_search_when_no_key_or_no_value"""
    diver = dive_to_lowest_lists(data)
    for pair in diver:
        if len(pair) > 1 and all(_ctd_is_good_key(key) for key in pair[:-1]):
            merge_tuplish_pair(pair, builder)

        else:
            diver.send(True)


def _ctd_pair_search(data: Union[dict, list], pair_name, func: Callable, builder, *args):
    """_convert_tuplish_dict_pair_search"""
    for potential_pair in dive_to_dicts(data, pair_name):
        func(potential_pair[pair_name], *args, builder)


def merge_tuplish_pair(pair: list, builder: dict, unsafe: bool = False):
    """
    Merges a list representing a key-value pair into a dictionary builder.

    This function iterates over the elements of the input pair list, representing a key-value pair,
    and merges it into the given dictionary builder. The builder is progressively updated to
    construct a nested dictionary structure based on the keys in the pair list. It will construct
    paths that are missing on its own.

    :param pair: A list representing a key-value pair, where all items except the last represent a
        *path* of keys under which the last item is to be stored.
    :type pair: list
    :param builder: The dictionary to merge ``pair`` into.
    :type builder: dict
    :param unsafe: Whether a failure to merge should actually raise an error. Defaults to ``False``.
    :type unsafe: bool

    .. warning::

        Default behavior is if the function encounters a key in the pair list that already exists in
        the builder and the corresponding value is not a dictionary, but there are more keys
        involved in the path to the value, it will not attempt to update the value or build the
        dictionary any deeper, but instead will do nothing to ``builder``. It logs a message under
        the ``dict_manip`` logger at the info level when this occurs. You can turn on this logger by
        setting the ``DICT_MANIP_LOG_LEVEL`` environment variable to ``'info'``.
    """
    # Given this function is frequently called at the deepest point on a stack of calls, it is built
    # to NOT be recursive. This helps ensure stack limit is not exceeded.
    worker = builder
    for i in range(len(pair) - 1):
        if (t := pair[i]) in worker:
            if isinstance(worker[t], dict) and i < len(pair) - 2:
                worker = worker[t]

            elif i == len(pair) - 2:
                worker[t] = pair[-1]
                break

            else:
                msg = (f'Can\'t merge into dict correctly. Attempted to merge '
                       f'{repr(pair[i + 1:])} into {repr(worker[t])}.')
                main_logger.info(msg)
                if unsafe:
                    raise ValueError(msg)

        else:
            if i < len(pair) - 2:
                # Do not change to worker = worker[t] = {}, makes infinitely-nested list
                # This is because the bytecode is compiled left-to-right for the objects assigned
                # to.
                worker[t] = worker = {}

            else:
                worker[t] = pair[i + 1]


def merge_to_dict(data: dict, builder: dict):
    """
    Merges ``data`` into ``builder`` while doing as much as possible to preserve ``builder``'s
    structure. If it finds a value that coincides with another value's position within ``builder``,
    it will perform the following in an attempt to turn those values into a singular list:
    - If both the value in ``builder`` and in ``data`` are lists, it will use the value from
    ``data`` to extend the value in ``builder``.
    - If the value in ``builder`` is a list, but the value in ``data`` is not, it will append the
    value from ``data`` to the value in ``builder``.
    - If the value in ``builder`` is not a list, but the value in ``data`` is, a list shall be
    constructed containing the items from ``data`` and the value from ``builder``.
    - If the value in ``builder`` and the value in ``data`` are not lists, it will create a list
    where each of them is an item.

    .. warning::

        If a value in ``data`` is at the same position as a dictionary in ``builder``,
        ``merge_to_dict`` will not attempt to add that value at the risk of deleting an intended
        branch in ``builder``. It logs a message under the ``dict_manip`` logger at the info level
        when this occurs. You can turn on this logger by setting the ``DICT_MANIP_LOG_LEVEL``
        environment variable to ``'info'``.

    :param data: The dictionary to have its values merged into ``builder``.
    :type data: dict
    :param builder: The dictionary to merge the values from ``data`` into.
    :type builder: dict
    """
    for key, val in data.items():
        if key in builder:
            if type(t := builder[key]) is dict:
                if type(val) is dict:
                    merge_to_dict(val, t)

                else:
                    main_logger.info(f'Can\'t merge into dict correctly. Attempted to merge '
                                     f'{repr(val)} into {repr(t)}.')

            elif type(t) is list:
                if type(val) is list:
                    t.extend(val)

                else:
                    t.append(val)

            elif type(val) is list:
                builder[key] = [t] + val

            else:
                builder[key] = [t] + [val]

        else:
            builder[key] = val


def dive_to_dicts(data: Union[dict, list], *needed_keys) -> Generator[dict, None, None]:
    """
    This will find the dictionaries at the lowest level within a list [1]_. The list may contain
    other lists, which will be searched for dictionaries as well. It is a ``Generator``, and can be
    iterated through.

    .. warning::
        This will not find the lowest-level dictionaries, but every **highest-level** dictionary
        **ignoring** dictionaries that only have one key **unless** that key happens to be the only
        value in ``needed_keys``, in which case it will return that dictionary.

    :param data: The data to find highest-level dictionaries in.
    :type data: Union[dict, list]
    :param needed_keys: The keys that found dictionaries **must** contain. If there are no
        ``needed_keys`` specified, then any dictionary will be considered valid and will be
        returned.
    :type needed_keys: Any

    .. [1] or a dictionary, if the dictionary only has one key
        *and its key doesn't coincide with the only key in* ``needed_keys``, otherwise only the
        dictionary passed will be considered.
    """
    if len(needed_keys):
        if isinstance(data, dict):
            if all(key in data for key in needed_keys):
                yield data

            elif t := _get_val_if_only_one_key(data):
                for val in dive_to_dicts(t):
                    yield val

        elif isinstance(data, list):
            for val in data:
                for result in dive_to_dicts(val):
                    if all(key in result for key in needed_keys):
                        yield result

    else:
        if isinstance(data, dict):
            yield data

        elif isinstance(data, list):
            for val in data:
                for result in dive_to_dicts(val):
                    yield result


def dive_to_lowest_lists(data: Union[dict, list]) -> Generator[Optional[list], Optional[bool], None]:
    """
    This will find the lowest-level lists within a list [2]_. The list may contain other lists,
    which will be searched through to see if they contain lists as well. It will keep searching
    until it has found all the lists which contain no lists. It is a `generator, and can be iterated
    through, but also has a valid ``send`` option. When sent the boolean value ``True`` via its
    ``.send`` method, it will continue to iterate through lowest-level lists, but will **also**
    check inside any dictionaries contained within the current list to see if there are lowest-level
    lists within those, whereas it would not normally do so.

    :param data: The dictionary or list to search for lowest-level lists in.
    :type data: Union[dict, list]
    :return: A generator which can be used ot iterate over all lowest-level lists inside a
        dictionary or list. This generator has can be sent a boolean value of ``True`` during
        iteration to change its behavior.

    .. [2] or a dictionary, if the dictionary only has one key, otherwise it will not return
        anything.
    """
    if isinstance(data, dict):
        if (t := _get_val_if_only_one_key(data)) is not None:
            # The following piece cannot be made into a separate function without being a waste of
            # time. By default, due to the nature of generators, this whole segment of code would
            # have to be replicated here again in order for it to function. We cannot pass a yield
            # out of a generator, and we can't send a value in without sending it in.
            diver = dive_to_lowest_lists(t)
            for vals in diver:
                try_deeper = yield vals
                if try_deeper:
                    diver.send(try_deeper)
                    yield

    elif isinstance(data, list):
        has_list = False
        for val in data:
            if isinstance(val, list):
                has_list = True
                break

        if has_list:
            for val in data:
                if isinstance(val, list):
                    # The following piece cannot be made into a separate function without being a
                    # waste of time. By default, due to the nature of generators, this whole segment
                    # of code would have to be replicated here again in order for it to function. We
                    # cannot pass a yield out of a generator, and we can't send a value in without
                    # sending it in.
                    diver = dive_to_lowest_lists(val)
                    for vals in diver:
                        try_deeper = yield vals
                        if try_deeper:
                            diver.send(try_deeper)
                            yield

        else:
            try_deeper = yield data
            if try_deeper:
                yield
                for val in data:
                    # The following piece cannot be made into a separate function without being a
                    # waste of time. By default, due to the nature of generators, this whole segment
                    # of code would have to be replicated here again in order for it to function. We
                    # cannot pass a yield out of a generator, and we can't send a value in without
                    # sending it in.
                    diver = dive_to_lowest_lists(val)
                    for vals in diver:
                        try_deeper = yield vals
                        if try_deeper:
                            diver.send(try_deeper)
                            yield


def _get_val_if_only_one_key(data: dict) -> Any:
    if len(data) == 1:
        return next(iter(data.values()))

    return None


def align_to_list(order: Union[list, dict], to_align: dict, default: Any = None) -> list:
    """
    Realigns the values from a dictionary to the order specified by ``order``. It does not require
    all expected keys to be in ``to_align``.

    :param order: The order that keys should go in. If this is a list, it will be used as-is. If it
        is a dictionary, its keys will be converted to a list which will be used in its place.
    :param to_align: The dictionary to align to order.
    :param default: The default value that should be used at a position if no value is specified for
        it in ``to_align``.
    :return: A list of the values from ``to_align`` in the order specified by ``order``.
    """
    if type(order) is dict:
        order = list(order.keys())

    output = [default] * len(order)
    for k, v in to_align.items():
        if k in order:
            output[order.index(k)] = v

    return output


def acc_(builder: Dict[str, list], key: Any, val: Any):
    if key in builder:
        builder[str(key)].append(str(val))

    else:
        builder[str(key)] = [str(val)]


def nest_under_keys(data: Any, *keys) -> dict:
    """Generates a nested dictionary using ``keys`` as the nesting keys."""
    worker = data
    for key in reversed(keys):
        worker = {key: worker}

    return worker


def get_subset(data: dict, *keys) -> dict:
    """
    Retrieves a subset of keys from a dictionary in the format of a dictionary. Any keys that do not
    exist will simply be omitted.
    """
    return {key: data[key] for key in keys if key in data}


def get_subset_values(data: dict, *keys) -> tuple:
    """
    Retrieves a subset values (based on ``keys``) from a dictionary in the format of a tuple. Any
    keys that do not exist will have ``None`` as their value.
    """
    return tuple(data.get(key, None) for key in keys)


def tuples_to_dict(*pairs: Tuple[Any, Any], all_pairs: Iterable[Tuple[Any, Any]] = None) -> dict:
    """Constructs a dictionary from provided tuples."""
    builder = {}
    if all_pairs is not None:
        builder.update({k: v for k, v in all_pairs})

    builder.update({k: v for k, v in pairs})
    return builder


def get_val_from_path(source: dict, *path: Any, default: Any = None, unsafe: bool = False) -> Any:
    """
    Follow a path through a dictionary to find the value at the end.

    :param source: The dictionary to get a value from.
    :param path: The paht of keys to follow to get to the desired value inside ``source``.
    :param default: A default value to return if the path ends prematurely. Will be ignored if
        unsafe is ``True``.
    :param unsafe: Whether to raise an exception if the path ends early. Overrides ``default``.
    :return: The value at the end of the desired path in ``source``, if it exists. Otherwise,
        ``default``.
    """
    for key in path:
        if key in source:
            source = source[key]

        elif unsafe:
            msg = f'Path failed at {key}'
            main_logger.error(msg)
            raise KeyError(msg)

        else:
            return default

    return source


@logs_vars(main_logger)
def get_one_of_keys(source: dict, *keys: Union[Any, list], default: Any = None) -> Any:
    """
    Get the value at one of the keys (or key paths) specified in ``keys`` from ``source``. Will
    return default if none of the keys/key paths exist in ``source``.

    :param source: The source ``dict`` to get the value from.
    :type source: dict
    :param keys: The possible keys or key paths the sought value could be located at.
    :type keys: Union[Any, list]
    :param default: The default value to return if the target value cannot be found.
    :type default: Any
    :return: The target value, if it is found. Otherwise, ``default``.
    """
    for key in keys:
        if isinstance(key, list):
            diver = source
            found = True
            for k in key:
                if k in diver:
                    diver = diver[k]

                else:
                    found = False
                    break

            if found:
                return diver

        elif key in source:
            return source[key]

    return default


_NO_MERGE = 'Cannot merge a non-dict to a dict.'
_METHOD = 'method'
_ARGS = 'args'
_KWARGS = 'kwargs'


class DictBuilder:
    """
    A builder for dictionaries that has a few helpful methods for merging in data from other
    dictionaries.
    """

    class _Instruction:
        # This class and _Cur implement the following patterns.
        # Chain of Responsibility
        # Command Pattern
        # Builder Pattern
        # Fluent Interface
        # Interpreter Pattern (loosely)
        # Proxy Pattern
        # Decorator Pattern
        def __init__(inner_self, method: str, *args, **kwargs):
            # Construct the base of a chain.
            inner_self._chain = [{_METHOD: method, _ARGS: args, _KWARGS: kwargs}]

        def __call__(inner_self, *args, **kwargs) -> 'DictBuilder._Instruction':
            # Update the last instruction in chain with the received args and kwargs. The user
            # intends to call a function and did not just want a value.
            inner_self._chain[-1].update({_ARGS: args, _KWARGS: kwargs})
            # Return self so that the reference doesn't go away.
            return inner_self

        def __getattr__(inner_self, item: str) -> 'DictBuilder._Instruction':
            # Add the new method to the chain, but don't assume the arguments. If there are any,
            # they will be added by __call__.
            inner_self._chain.append({_METHOD: item})
            # Return self so that the reference doesn't go away.
            return inner_self

        def __getitem__(inner_self, key: str):
            # Add __getitem__ and args/kawrgs to chain.
            inner_self._chain.append({_METHOD: '__getitem__', _ARGS: (key,), _KWARGS: {}})
            # Return self so that the reference doesn't go away.
            return inner_self

        def list(inner_self) -> 'DictBuilder._Instruction':
            inner_self._chain.append({_METHOD: lambda x: list(x)})
            return inner_self

        def tuple(inner_self) -> 'DictBuilder._Instruction':
            inner_self._chain.append({_METHOD: lambda x: tuple(x)})
            return inner_self

        def _evaluate(inner_self, parent: 'DictBuilder') -> Any:
            attr = parent
            for instruction in inner_self._chain:
                if type(t := instruction[_METHOD]) is not str:
                    attr = t(attr)

                else:
                    attr = getattr(attr, t)

                if _ARGS in instruction:
                    attr = attr(*[a._evaluate()
                                  if type(a) in (DictBuilder._Cur, DictBuilder._Instruction)
                                  else a
                                  for a in instruction[_ARGS]],
                                **{k: v._evaluate()
                                   if v in (DictBuilder._Cur, DictBuilder._Instruction)
                                   else v
                                   for k, v in instruction[_KWARGS].items()})

            return attr

    class _Cur:
        # This class and _Instruction implement the following patterns.
        # Chain of Responsibility
        # Command Pattern
        # Builder Pattern
        # Fluent Interface
        # Interpreter Pattern (loosely)
        # Proxy Pattern
        # Decorator Pattern
        def __getitem__(self, key):
            return DictBuilder._Instruction('__getitem__', key)

        @staticmethod
        def get(key: Any, default: Any = None):
            return DictBuilder._Instruction('get', key, default)

        @staticmethod
        def keys() -> 'DictManip._Instruction':
            return DictBuilder._Instruction('keys')

        @staticmethod
        def values() -> 'DictManip._Instruction':
            return DictBuilder._Instruction('values')

        @staticmethod
        def items() -> 'DictManip._Instruction':
            return DictBuilder._Instruction('items')

        @staticmethod
        def _evaluate(parent: 'DictBuilder') -> Any:
            return parent

    #: _Cur: A placeholder that can be used to represent the current ``DictBuilder`` inside its own
    #: methods and allows the use of a few types of getters including __getitem__, get, keys,
    #: values, and items' methods.
    #:
    #: .. warning::
    #:     Using this can have unintended consequences and can allow recursion. Use at your own
    #:     risk.
    CUR = _Cur() 

    def __new__(cls, *args, clazz: Type = dict, **kwargs):
        if clazz is None:
            clazz = dict

        inst = super().__new__(cls)
        if issubclass(clazz, dict):
            inst.__class = clazz
            return inst

        else:
            msg = f'clazz must inherit from dict, but it does not. Provided {clazz}.'
            main_logger.error(msg)
            raise TypeError(msg)

    def __init__(self, _map: Mapping = ..., *, clazz: Type = dict, _other: dict = None,
                 _transformer: Callable = pass_, **kwargs):
        """
        :param _map: The ``Mapping`` to start the builder out with. Works like it does for ``dict``.
        :type _map: Mapping
        :param clazz: A dictionary class to inherit from. Used to make sure the builder is the
            desired type of dictionary.
        :type clazz: Type
        :param _other: The *other* dictionary to use for :meth:`~DictBuilder.pull_from_other`,
            :meth:`~DictBuilder.get_from_other`, :meth:`~DictBuilder.update_from_other`,
            and :meth:`~DictBuilder.get_one_of_keys_from_other`. If this is not specified, those
            methods will not work. It can be changed later.
        :type _other: dict
        :param _transformer: The default transformer to use for values retrieved from another dict.
            Defaults to a function that does nothing to the input.
        :type _transformer: Callable
        :param kwargs: The ``kwargs`` to construct the starting builder with. Works like it does for
            ``dict``.
        """
        if 'clazz' in kwargs:
            del kwargs['clazz']

        if _map is ...:
            self.__builder = self.__class(**kwargs)

        else:
            self.__builder = self.__class(_map, **kwargs)

        if _other is not None:
            self._check_dict(_other)

        self.__other = _other

        self._check_transformer(_transformer)
        self.__transformer = _transformer

    @property
    def clazz(self) -> type:
        """The default class for the ``DictBuilder``."""
        return self.__class

    @property
    def other(self) -> dict:
        return self.__other

    @other.setter
    def other(self, other: dict):
        if other is not None:
            self._check_dict(other)

        self.__other = other

    @property
    def transformer(self) -> Callable:
        return self.__transformer

    @transformer.setter
    def transformer(self, transformer: Callable):
        self._check_transformer(transformer)
        self.__transformer = transformer

    def use(self, other: dict = ..., transformer: Callable = ...) -> 'DictBuilder':
        """
        Set parameter defaults for ``other`` and/or ``transformer``.

        :param other: The new ``other`` to use. If omitted ``other`` will not be changed. If
            ``None`` is given, then the current ``other`` will be erased, and
            :meth:`~DictBuilder.pull_from_other`, :meth:`~DictBuilder.get_from_other`,
            :meth:`~DictBuilder.update_from_other`, and
            :meth:`~DictBuilder.get_one_of_keys_from_other` will cease to work until a new ``other``
            is specified.
        :param transformer: The new ``transformer`` to use as a default transformer in functions. If
            omitted, ``transformer`` will remain the same. If ``None`` is given, then transformer
            will be set to its default value (a non-transforming function).
        :return: The current ``DictBuilder`` for chaining.
        """
        if other is not ...:
            self._check_dict(other)
            self.__other = other

        if transformer is not ...:
            if transformer is None:
                transformer = pass_

            self._check_transformer(transformer)
            self.__transformer = transformer

        return self

    def _check_dict(self,
                    other: Union[dict, 'DictBuilder._Cur', 'DictBuilder._Instruction']) -> dict:
        if type(other) is DictBuilder._Cur:
            return self.__builder

        elif type(other) is DictBuilder._Instruction:
            # Evaluate the instruction first to make sure it produces a dictionary.
            if not isinstance(t := other._evaluate(self), dict):
                raise TypeError('Invalid type for other.')

            return t

        elif not isinstance(other, dict):
            raise TypeError('Invalid type for other.')

        return other

    @staticmethod
    def _check_transformer(transformer: Callable):
        if not callable(transformer):
            raise TypeError('Invalid type for transformer.')

    def _choose_transformer(self, transformer: Optional[Callable]):
        if transformer is ...:
            return self.__transformer

        elif transformer is None:
            return pass_

        self._check_transformer(transformer)
        return transformer

    def _check_has_other(self):
        if self.__other is None:
            raise TypeError('No other is set for this DictBuilder. Cannot complete request.')

    @staticmethod
    def _pathify_as(_as: Union[Any, list], val: Any):
        if isinstance(_as, list):
            (path := list(_as)).append(val)

        else:
            path = _as, val

        return path

    def _process_key(self, other: dict,
                     key: Any,
                     transformer: Callable,
                     unsafe: bool,
                     default: Any = ...) -> Any:
        if type(key) in (DictBuilder._Cur, DictBuilder._Instruction):
            key = key._evaluate(self)

        if isinstance(key, list):
            key = [v._evaluate()
                   if type(v) in (DictBuilder._Cur, DictBuilder._Instruction)
                   else v
                   for v in key]
            val = get_val_from_path(other, *key, unsafe=unsafe, default=...)
            if val is ...:
                return default

            return transformer(val)

        val = other.get(key, ...)
        if val is ...:
            return default

        return transformer(val)

    @logs_vars(main_logger, start_message='Getting a value from another dictionary...',
               start_message_level='info',
               end_message='Finished attempt to get a value from another dictionary.',
               end_message_level='info')
    def pull_from(self, other: Union[dict, 'DictBuilder._Cur', 'DictBuilder._Instruction'],
                  key: Any,
                  _as: Any,
                  transformer: Callable = ...) -> 'DictBuilder':
        """
        Get a value from another dictionary at a given key, and insert it at the key specified in
        ``_as``. Using this will raise an error if the key doesn't exist in ``other`` or if it
        cannot safely be added to the ``DictBuilder``.

        :param other: The dictionary to grab the key from.
        :type other: dict
        :param key: The key at which to find a value in ``other``.
        :type key: Union[Any, list]
        :param _as: The key at which to place the found value from ``other``.
        :type _as: Union[Any, list]
        :param transformer: A transformer that should be called on a value if found.
        :type transformer: Callable
        :return: The current ``DictBuilder`` for chaining.
        """
        other = self._check_dict(other)
        transformer = self._choose_transformer(transformer)
        val = self._process_key(other, key, transformer, True)
        if val is ...:
            raise ValueError('An invalid value was used.')

        path = self._pathify_as(_as, val)
        merge_tuplish_pair(path, self.__builder, unsafe=True)
        return self

    def pull_from_other(self, key: Any,
                        _as: Any,
                        transformer: Callable = ...) -> 'DictBuilder':
        """
        Get a value from the ``DictBuilder's`` ``other`` at a given key, and insert it at the key
        specified in ``_as``. Using this will raise an error if the key doesn't exist in ``other``
        or if it cannot safely be added to the ``DictBuilder``.

        :param key: The key at which to find a value in ``other``.
        :type key: Union[Any, list]
        :param _as: The key at which to place the found value from ``other``.
        :type _as: Union[Any, list]
        :param transformer: A transformer that should be called on a value if found.
        :type transformer: Callable
        :return: The current ``DictBuilder`` for chaining.
        """
        self._check_has_other()
        self.pull_from(self.__other, key, _as, transformer)
        return self

    @logs_vars(main_logger, start_message='Getting a value from another dictionary...',
               start_message_level='info',
               end_message='Finished attempt to get a value from another dictionary.',
               end_message_level='info')
    def get_from(self, other: Union[dict, 'DictBuilder._Cur', 'DictBuilder._Instruction'],
                 key: Any,
                 _as: Any,
                 transformer: Callable = ...,
                 default: Any = ...) -> 'DictBuilder':
        """
        Get a value from another dictionary at a given key, and insert it at the key specified in
        ``_as``. If ``key`` cannot be found in other or ``the value cannot be added to this
        ``DictBuilder``, then the value simply won't be added.

        :param other: The dictionary to grab the key from.
        :type other: dict
        :param key: The key at which to find a value in ``other``.
        :type key: Union[Any, list]
        :param _as: The key at which to place the found value from ``other``.
        :type _as: Union[Any, list]
        :param transformer: A transformer that should be called on a value if found.
        :type transformer: Callable
        :param default: The default value to use if a value cannot be found. If omitted, and the
            value is not found, then the value simply won't be added.
        :return: The current ``DictBuilder`` for chaining.
        """
        other = self._check_dict(other)
        transformer = self._choose_transformer(transformer)
        val = self._process_key(other, key, transformer, False, default)
        if val is ...:
            return self

        path = self._pathify_as(_as, val)
        merge_tuplish_pair(path, self.__builder)
        return self

    def get_from_other(self, key: Any,
                       _as: Any,
                       transformer: Callable = ...,
                       default: Any = ...) -> 'DictBuilder':
        """
        Get a value from the ``DictBuilder's`` ``other`` at a given key, and insert it at the key
        specified in ``_as``. If ``key`` cannot be found in ``other`` or the value cannot be added
        to this ``DictBuilder``, then the value simply won't be added.

        :param key: The key at which to find a value in ``other``.
        :type key: Union[Any, list]
        :param _as: The key at which to place the found value from ``other``.
        :type _as: Union[Any, list]
        :param transformer: A transformer that should be called on a value if found.
        :type transformer: Callable
        :param default: The default value to use if a value cannot be found. If omitted, and the
            value is not found, then the value simply won't be added.
        :return: The current ``DictBuilder`` for chaining.
        """
        self._check_has_other()
        self.get_from(self.__other, key, _as, transformer, default)
        return self
    
    @logs_vars(main_logger, start_message='Updating from a list...',
               start_message_level='info',
               end_message='Finished attempt to update from list.',
               end_message_level='info')
    def update_from_list(self, other: List[dict],
                          _as: Any = None,
                          transformer: Callable = ...,
                          unsafe: bool = False,
                          classes: Union[List[Type[dict]], Type[dict]] = None) -> 'DictBuilder':
        """
        Update this ``DictBuilder`` from another dict.

        :param other: The dictionary to update with.
        :type other: dict
        :param _as: The key at which to place update with the found value from ``other``. If not
            specified, will simply update the entire ``DictBuilder``.
        :type _as: Union[Any, None, list]
        :param transformer: A transformer that should be called on the value being used to update
            the ``DictBuilder``.
        :type transformer: Callable
        :param unsafe: Whether an error should be raised if the desired operation cannot be
            completed.
        :type unsafe: bool
        :param classes: The types of internal dictionaries to generate if parts of paths do not
            exist. Will override what type of dictionary is used at each point in the path until
            the end of ``_as``. There are different behaviors based on how this is specified (or not
            specified).

            - If this is a ``list``, each class will be used in succession while following the path
              specified by ``_as``. If the end is reached before ``_as`` is over, new dictionaries
              will be of the same type as the ``DictBuilder.clazz``. If this longer than ``_as``, it
              will only be used for needed locations.
            - If this is a single type, any new dicts generated when following the path described by
              ``_as`` will be of the type specified.
            - If this is not specified, each generated dictionary will be of the same type as the
              ``DictBuilder.clazz``.
        :type classes: Optional[Union[List[Type[dict]], Type[dict]]]
        :return: The current ``DictBuilder`` for chaining.
        """
        transformer = self._choose_transformer(transformer)

        worker = self.__builder
        worker = self._update_seek(_as, worker, unsafe, classes)
        for val in dive_to_dicts(other):
            if not isinstance(t := transformer(val), dict):
                if unsafe:
                    main_logger.error(_NO_MERGE)
                    raise ValueError(_NO_MERGE)

                continue

            worker.update(t)

        return self

    @logs_vars(main_logger, start_message='Updating from another dictionary...',
               start_message_level='info',
               end_message='Finished attempt to update from another dictionary.',
               end_message_level='info')
    def update_from(self, other: Union[dict, 'DictBuilder._Cur', 'DictBuilder._Instruction'],
                    key: Any = None,
                    _as: Any = None,
                    keys: list = None,
                    transformer: Callable = ...,
                    unsafe: bool = False,
                    classes: Union[List[Type[dict]], Type[dict]] = None,
                    val_is_list: bool = False) -> 'DictBuilder':
        """
        Update this ``DictBuilder`` from another dict.

        :param other: The dictionary to update with.
        :type other: dict
        :param key: The key at which the source dictionary should be in ``other``. If not specified
            ``other`` will be used as-is unless ``keys`` is specified.
        :type key: Union[Any, None, list]
        :param _as: The key at which to place update with the found value from ``other``. If not
            specified, will simply update the entire ``DictBuilder``.
        :type _as: Union[Any, None, list]
        :param keys: A list of possible keys at which the source dictionary might be located in
            ``other``. Each key should follow the same rules as ``key``. If ``key`` is specified,
            ``key`` will be attempted first, then ``keys`` will be attempted.
        :type keys: Optional[List[Union[Any, None, list]]]
        :param transformer: A transformer that should be called on the value being used to update
            the ``DictBuilder``.
        :type transformer: Callable
        :param unsafe: Whether an error should be raised if the desired operation cannot be
            completed.
        :type unsafe: bool
        :param classes: The types of internal dictionaries to generate if parts of paths do not
            exist. Will override what type of dictionary is used at each point in the path until
            the end of ``_as``. There are different behaviors based on how this is specified (or not
            specified).

            - If this is a ``list``, each class will be used in succession while following the path
              specified by ``_as``. If the end is reached before ``_as`` is over, new dictionaries
              will be of the same type as the ``DictBuilder.clazz``. If this longer than ``_as``, it
              will only be used for needed locations.
            - If this is a single type, any new dicts generated when following the path described by
              ``_as`` will be of the type specified.
            - If this is not specified, each generated dictionary will be of the same type as the
              ``DictBuilder.clazz``.
        :type classes: Optional[Union[List[Type[dict]], Type[dict]]]
        :param val_is_list: Whether the value at ``key`` in ``other`` should be considered as a list
            and its values iterated over and individually used to update the ``DictBuilder``.
            Defaults to ``False``.
        :type val_is_list: bool
        :return: The current ``DictBuilder`` for chaining.
        """
        other = self._check_dict(other)
        transformer = self._choose_transformer(transformer)

        val = self._update_find_in_other(other, key, keys, unsafe)
        if val is ...:
            main_logger.info('Target value could not be located.')
            if unsafe:
                k = [key]
                if keys is not None:
                    k.extend(keys)

                raise ValueError(f'Could not find key in other.\nkey={k}')

            return self

        if not (val_is_list or isinstance(transformer(val), dict)):
            if unsafe:
                main_logger.error(_NO_MERGE)
                raise ValueError(_NO_MERGE)

            return self

        self._update_vals(val, _as, unsafe, transformer, classes, val_is_list)
        return self

    def update_from_other(self, key: Any = None,
                          _as: Union[Any, None, list] = None,
                          keys: List[Any] = None,
                          transformer: Callable = ...,
                          unsafe: bool = False,
                          classes: Union[List[Type[dict]], Type[dict]] = None,
                          val_is_list: bool = False) -> 'DictBuilder':
        """
        Update this ``DictBuilder`` from it's stored ``other``.

        :param key: The key at which the source dictionary should be in ``other``. If not specified
            ``other`` will be used as-is unless ``keys`` is specified.
        :type key: Optional[Union[Any, None, list]]
        :param _as: The key at which to place update with the found value from ``other``. If not
            specified, will simply update the entire ``DictBuilder``.
        :type _as: Union[Any, None, list]
        :param keys: A list of possible keys at which the source dictionary might be located in
            ``other``. Each key should follow the same rules as ``key``. If ``key`` is specified,
            ``key`` will be attempted first, then ``keys`` will be attempted.
        :type keys: Optional[List[Union[Any, None, list]]]
        :param transformer: A transformer that should be called on the value being used to update
            the ``DictBuilder``.
        :type transformer: Callable
        :param unsafe: Whether an error should be raised if the desired operation cannot be
            completed.
        :type unsafe: bool
        :param classes: The types of internal dictionaries to generate if parts of paths do not
            exist. Will override what type of dictionary is used at each point in the path until
            the end of ``_as``. There are different behaviors based on how this is specified (or not
            specified).

            - If this is a ``list``, each class will be used in succession while following the path
              specified by ``_as``. If the end is reached before ``_as`` is over, new dictionaries
              will be of the same type as the ``DictBuilder.clazz``. If this longer than ``_as``, it
              will only be used for needed locations.
            - If this is a single type, any new dicts generated when following the path described by
              ``_as`` will be of the type specified.
            - If this is not specified, each generated dictionary will be of the same type as the
              ``DictBuilder.clazz``.
        :type classes: Optional[Union[List[Type[dict]], Type[dict]]]
        :param val_is_list: Whether the value at ``key`` in ``other`` should be considered as a list
            and its values iterated over and individually used to update the ``DictBuilder``.
            Defaults to ``False``.
        :type val_is_list: bool
        :return: The current ``DictBuilder`` for chaining.
        """
        self._check_has_other()
        self.update_from(self.__other, key, _as, keys, transformer, unsafe, classes, val_is_list)
        return self

    def _update_vals(self, val: Any,
                     _as: Any,
                     unsafe: bool,
                     transformer: Callable,
                     classes: Union[List[Type[dict]], Type[dict]],
                     val_is_list: bool):
        worker = self.__builder
        worker = self._update_seek(_as, worker, unsafe, classes)
        if val_is_list:
            # Don't assume there is a list just because the user expected one to be there.
            if isinstance(val, list):
                for _val in dive_to_dicts(val):
                    if not isinstance(t := transformer(_val), dict):
                        if unsafe:
                            main_logger.error(_NO_MERGE)
                            raise ValueError(_NO_MERGE)

                        continue

                    worker.update(t)

            elif not isinstance(t := transformer(val), dict):
                # If we don't have a list, make sure we don't need to raise an exception.
                if unsafe:
                    main_logger.error(_NO_MERGE)
                    raise ValueError(_NO_MERGE)

            else:
                # If a dictionary is present instead of a list, use that to update.
                worker.update(t)

            return

        worker.update(transformer(val))

    def _update_process_key(self, key: Any):
        if type(key) in (DictBuilder._Cur, DictBuilder._Instruction):
            return key._evaluate(self)

        if isinstance(key, list):
            return [v._evaluate()
                    if type(v) in (DictBuilder._Cur, DictBuilder._Instruction)
                    else v
                    for v in key]

        return key

    def _update_find_in_other(self, other: dict, key: Any, keys: List[Any], unsafe: bool = False):
        # Find a key in other, if it exists. Return ... if it doesn't.
        if key is not None:
            key = self._update_process_key(key)
            if keys is not None:
                keys = [self._update_process_key(k) for k in keys]
                # If the user specified both key and keys, that is silly, but handle feeding both
                # into get_one_of_keys for them. No need to raise an exception.
                return get_one_of_keys(other, key, *keys, default=...)

            elif isinstance(key, list):
                # Only a key is present and it specifies a path. Follow the path.
                return get_val_from_path(other, *key, unsafe=unsafe, default=...)

            # Simple key is specified.
            return other.get(key, ...)

        elif keys is not None:
            # key isn't specified, but keys is. Try to get one of keys.
            keys = [self._update_process_key(k) for k in keys]
            return get_one_of_keys(other, *keys, default=...)

        # If neither keys nor key is specified, assume the user wants the entire dictionary.
        return other

    @logs_vars(main_logger, start_message='Attempting to locate target to update...')
    def _update_seek(self, _as: Any,
                     worker: dict,
                     unsafe: bool,
                     classes: Union[None, List[Type[dict]], Type[dict]]):
        if _as is not None:
            needed = len(_as)
            if type(classes) is list:
                if (t := len(classes) - needed) < 0:
                    classes += [self.__class] * -t

            elif classes is None:
                classes = [self.__class] * needed

            else:
                classes = [classes] * needed

            for t in classes:
                if not issubclass(t, dict):
                    msg = (f'All used classes must inherit from dict, but it does not. Provided'
                           f'{classes}.')
                    main_logger.error(msg)
                    raise TypeError(msg)

            clazz = iter(classes)
            if isinstance(_as, list):
                for val in _as:
                    worker = self._update_seek_next(val, worker, unsafe, next(clazz))

            else:
                worker = self._update_seek_next(_as, worker, unsafe, next(clazz))

        main_logger.debug(f'Found the target worker. Value is {worker}.')
        return worker

    @staticmethod
    def _update_seek_next(val: Any, worker: dict, unsafe: bool, clazz: Type[dict]):
        if val in worker:
            if isinstance(worker[val], dict):
                worker = worker[val]

            elif unsafe:
                msg = 'An invalid path was encountered while updating from another dictionary.'
                main_logger.error(msg)
                raise ValueError(msg)

            else:
                worker[val] = worker = clazz()

        else:
            worker[val] = worker = clazz()

        return worker

    @logs_vars(main_logger, start_message='Getting one of the keys from another dictionary...',
               start_message_level='info',
               end_message='Finished attempt to get one of the keys from another dictionary.',
               end_message_level='info')
    def get_one_of_keys_from(self, other: dict,
                             _as: Any,
                             *keys: Any,
                             transformer: Callable = ...,
                             default: Any = ...) -> 'DictBuilder':
        """
        Gets the value at one of the keys (or key paths) specified in ``keys`` from ``other`` and
        adds it at ``_as`` within the ``DictBuilder``.

        :param other: The source ``dict`` to get the value from.
        :type other: dict
        :param _as: The key or key path to add a found value at.
        :type _as: Union[Any, list]
        :param keys: The possible keys or key paths the sought value could be located at.
        :type keys: Union[Any, list]
        :param default: The default value to return if the target value cannot be found. If this is
            not specified, then should no value be found, a value simply won't be added.
        :type default: Any
        :return: The current ``DictBuilder`` for chaining.
        """
        other = self._check_dict(other)
        transformer = self._choose_transformer(transformer)
        keys = [self._update_process_key(k) for k in keys]

        val = get_one_of_keys(other, *keys, ...)
        if val is ...:
            if default is ...:
                return self

            val = default

        else:
            val = transformer(val)

        path = self._pathify_as(_as, val)
        merge_tuplish_pair(path, self.__builder)

        return self

    def get_one_of_keys_from_other(self, _as: Union[Any, list],
                                   *keys: Union[Any, list],
                                   transformer: Callable = ...,
                                   default: Any = ...) -> 'DictBuilder':
        """
        Gets the value at one of the keys (or key paths) specified in ``keys`` from the
        ``DictBuilder's`` ``other`` and adds it at ``_as`` within the ``DictBuilder``.

        :param _as: The key or key path to add a found value at.
        :type _as: Union[Any, list]
        :param keys: The possible keys or key paths the sought value could be located at.
        :type keys: Union[Any, list]
        :param default: The default value to return if the target value cannot be found. If this is
            not specified, then should no value be found, a value simply won't be added.
        :type default: Any
        :return: The current ``DictBuilder`` for chaining.
        """
        self._check_has_other()
        return self.get_one_of_keys_from(self.__other, _as, *keys, transformer=transformer,
                                         default=default)

    @logs_vars(main_logger, start_message='Updating dictionary...', start_message_level='info',
               end_message='Finished updating.', end_message_level='info')
    def update(self, _map: Mapping = ..., **kwargs) -> 'DictBuilder':
        self.__builder.update(_map, **kwargs)
        return self

    def __delitem__(self, key) -> 'DictBuilder':
        del self.__builder[key]
        return self

    def __getitem__(self, key):
        return self.__builder[key]

    def get(self, key: Any, default: Any = None):
        return self.__builder.get(key, default)

    def __setitem__(self, key, value) -> 'DictBuilder':
        self.__builder[key] = value
        return self

    def keys(self) -> list:
        return list(self.__builder.keys())

    def values(self) -> list:
        return list(self.__builder.values())

    def items(self) -> list:
        return list(self.__builder.items())

    def build(self, strict: bool = True) -> dict:
        """
        Build the dictionary from the DictBuilder.

        :param strict: Whether to return a strict copy of the dictionary, maintaining all types.
            ``True`` will result all internal dictionaries being maintained as their original types.
            ``False`` will result in all internal dictionaries being converted to ``dict``.
        :type strict: bool
        :return: The dictionary that was built.
        """
        result = deepcopy(self.__builder)
        if strict:
            return result

        return self._convert_all_to_dicts(result)

    def _convert_all_to_dicts(self, source: dict) -> dict:
        # One return statement. Returns worker.
        if type(source) is dict:
            worker = source

        else:
            worker = dict(source)

        for key, val in source.items():
            if isinstance(val, dict):
                worker[key] = self._convert_all_to_dicts(val)

            else:
                worker[key] = val

        return worker
