from typing import Generator, Optional, Union, Any, Callable

from funk_py.modularity.logging import make_logger


main_logger = make_logger('dict_manip', env_var='DICT_MANIP_LOG_LEVEL', default_level='warning')


_skip_message = 'Skipped a key-val pair in convert_tuplish_dict '


def convert_tuplish_dict(data: Union[dict, list], pair_name: str = None, key_name: str = None,
                         val_name: str = None) -> dict:
    """
    Handles converting a ``dict`` or ``list`` with key-val pairs into a dictionary of those key-val
    pairs. It follows specific rules based on the following criteria:

    1. if ``pair_name`` is specified.

    2. if **both** ``key_name`` and ``val_name`` are specified. *Be aware that specifying only one
        of these will result in them both being ignored.

    3. if ``key_name`` is equal to ``val_name`` and **both** are specified.

    :param data: The data to treat as a tuplish dict.
    :param pair_name: The name used to represent a pair. If omitted, will not expect pairs to be
        under keys.
    :param key_name: The name used to represent a key. If either this or ``val_name`` is omitted,
        neither will be used and pairs will be constructed using the best identifiable method.
    :param val_name: The name used to represent a value. If either this or ``key_name`` is omitted,
        neither will be used and pairs will be constructed using the best identifiable method.
    :return: A ``dict`` composed of
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
    for pair in _dive_to_dicts(data):
        if key_name in pair:
            pair = pair[key_name]
            if (isinstance(pair, list) and len(pair) > 1
                    and all(_ctd_is_good_key(key) for key in pair[:-1])):
                merge_tuplish_pair(pair, builder)

            else:
                main_logger.info(_skip_message + 'because it didn\'t look like a complete pair.')


def _ctd_search_when_dkv(data: Union[dict, list], key_name, val_name, builder):
    """_convert_tuplish_dict_search_when_diff_key_and_value"""
    for vals in _dive_to_dicts(data):
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
    diver = _dive_to_lowest_list(data)
    for pair in diver:
        if len(pair) > 1 and all(_ctd_is_good_key(key) for key in pair[:-1]):
            merge_tuplish_pair(pair, builder)

        else:
            diver.send(True)


def _ctd_pair_search(data: Union[dict, list], pair_name, func: Callable, builder, *args):
    for potential_pair in _dive_to_dicts(data, pair_name):
        func(potential_pair[pair_name], *args, builder)


def merge_tuplish_pair(pair: list, builder: dict):
    worker = builder
    for i in range(len(pair) - 1):
        if (t := pair[i]) in worker:
            if isinstance(worker[t], dict) and i < len(pair) - 2:
                worker = worker[t]

            else:
                main_logger.info(f'Can\'t merge into dict correctly. Attempted to merge '
                                 f'{repr(pair[i + 1:])} into {repr(worker[t])}.')

        else:
            if i < len(pair) - 2:
                # Do not change to worker = worker[t] = {}, makes infinitely-nested list
                # This is because the bytecode is compiled left-to-right for the objects assigned
                # to.
                worker[t] = worker = {}

            else:
                worker[t] = pair[i + 1]


def merge_to_dict(data: dict, builder: dict):
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


def _dive_to_dicts(data: Union[dict, list], *needed_keys) -> Generator[dict, None, None]:
    if len(needed_keys):
        if isinstance(data, dict):
            if all(key in data for key in needed_keys):
                yield data

            elif t := _get_val_if_only_one_key(data):
                for val in _dive_to_dicts(t):
                    yield val

        elif isinstance(data, list):
            for val in data:
                for result in _dive_to_dicts(val):
                    if all(key in result for key in needed_keys):
                        yield result

    else:
        if isinstance(data, dict):
            yield data

        elif isinstance(data, list):
            for val in data:
                for result in _dive_to_dicts(val):
                    yield result


def _dive_to_lowest_list(data: Union[dict, list]) \
        -> Generator[Optional[list], Optional[bool], None]:
    if isinstance(data, dict):
        if (t := _get_val_if_only_one_key(data)) is not None:
            # The following piece cannot be made into a separate function without being a waste of
            # time. By default, due to the nature of generators, this whole segment of code would
            # have to be replicated here again in order for it to function. We cannot pass a yield
            # out of a generator, and we can't send a value in without sending it in.
            diver = _dive_to_lowest_list(t)
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
                    diver = _dive_to_lowest_list(val)
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
                    diver = _dive_to_lowest_list(val)
                    for vals in diver:
                        try_deeper = yield vals
                        if try_deeper:
                            diver.send(try_deeper)
                            yield


def _get_val_if_only_one_key(data: dict) -> Any:
    if len(data) == 1:
        return next(iter(data.values()))

    return None
