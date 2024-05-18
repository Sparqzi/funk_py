from typing import Generator, Optional, Union, Any, Callable, Dict, Tuple, Iterable

from funk_py.modularity.logging import make_logger


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
