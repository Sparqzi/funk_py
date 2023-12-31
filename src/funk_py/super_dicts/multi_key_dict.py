from typing import Callable, Iterable, Union, Any, Mapping


def v_is(value):
    return value is False or value is True or value is None or value is ...


def _eq_list(list_: Union[list, tuple]):
    def _eq(o_list: list):
        if not isinstance(o_list, list) or len(list_) != len(o_list):
            return False

        for i in range(len(list_)):
            v, o = list_[i], o_list[i]

            if not _compare_values(v, o):
                return False

    return _eq


def _eq_dict(dict_: dict):
    def _eq(o_dict: dict):
        if not isinstance(o_dict, dict) or len(dict_) != len(o_dict):
            return False

        for key, val in dict_.items():
            if key in o_dict:
                if not _compare_values(val, o_dict[key]):
                    return False

            else:
                return False

    return _eq


def _eq_set(set_: set):
    def _eq(o_set: set):
        if not isinstance(o_set, set) or len(set_) != len(o_set):
            return False

        for val in set_:
            if val not in o_set:
                return False

    return _eq


SPECIAL_HANDLED_TYPES = (list, dict, tuple, set)
SPECIAL_TYPE_HANDLERS = (_eq_list, _eq_dict, _eq_list, _eq_set)


def _compare_values(v1, v2):
    if (t1 := v_is(v1)) ^ (t2 := v_is(v2)):
        return False

    elif t1 and t2:
        return v1 is v2

    elif (t1 := callable(v1)) ^ (t2 := callable(v2)):
        return False

    # Ignore linter for below. It's trying its best, but the second set of
    # walrus operators confuses it.
    elif t1 and t2:  # noqa
        return _eq_func(v1)(v2)

    elif all(not isinstance(v1, t) for t in SPECIAL_HANDLED_TYPES):
        return v1 == v2

    return _check_for_thing(v1, v2, SPECIAL_HANDLED_TYPES,
                            SPECIAL_TYPE_HANDLERS)


def _check_for_thing(v1, v2, types, c_funcs):
    _type = types[0]
    if (t1 := isinstance(v1, _type)) ^ (t2 := isinstance(v2, _type)):
        return False

    elif t1 and t2:
        return c_funcs[0](v1)(v2)

    elif len(types) > 1:
        return _check_for_thing(v1, v2, types[1:], c_funcs[1:])

    return v1 == v2


def _hash_func(func: Callable):
    _code = func.__code__
    _hash = hash(_code.co_code)
    _hash += hash(_code.co_consts)
    _hash += _code.co_nlocals
    _hash += _code.co_argcount
    _hash += _code.co_kwonlyargcount
    return hash(_hash)


def _eq_func(func: Callable):
    _code = func.__code__
    p1 = _code.co_code
    p2 = _code.co_consts
    p3 = _code.co_argcount
    p4 = _code.co_nlocals
    p5 = _code.co_kwonlyargcount
    p6 = _code.co_posonlyargcount
    p7 = _code.co_flags

    def _eq(o_func: Callable):
        if not callable(o_func):
            return False

        o_code = o_func.__code__
        return (o_code.co_code == p1 and o_code.co_consts == p2
                and o_code.co_argcount == p3  and o_code.co_nlocals == p4
                and o_code.co_kwonlyargcount == p5
                and o_code.co_posonlyargcount == p6 and o_code.co_flags == p7)

    return _eq


_HASH_LIST = hash('lIsT')
_HASH_DICT = hash('dIcTiOnArY')
_HASH_SET = hash('sEt')
_HASH_UNKNOWN = hash('uNkNoWn')


class MkD(dict):
    class __Holder(set):
        """Holds and acts as a reference for values in the MultiKeyDict."""
        class ValNode(object):
            def __init__(i_i_self, value):
                i_i_self.value = value
                # Handles the screwy ones...
                if v_is(value):
                    i_i_self._hash = hash(value)
                    i_i_self._eq = lambda other: other.value is value
                    return

                try:
                    i_i_self._hash = hash(value)
                    i_i_self._eq = lambda other: i_i_self.value == other.value
                    return

                except TypeError as e:
                    if 'unhashable type:' in str(e):
                        if callable(value):
                            i_i_self._eq = _eq_func(value)
                            i_i_self._hash = _hash_func(value)
                            return

                        elif isinstance(value, list) or type(value) is tuple:
                            i_i_self._eq = _eq_list(value)
                            i_i_self._hash = _HASH_LIST
                            return

                        elif isinstance(value, dict):
                            i_i_self._eq = _eq_dict(value)
                            i_i_self._hash = _HASH_DICT
                            return

                        elif isinstance(value, set):
                            i_i_self._eq = _eq_set(value)
                            i_i_self._hash = _HASH_SET
                            return

                        else:
                            i_i_self._eq = \
                                lambda other: _compare_values(value, other.value)
                            i_i_self._hash = _HASH_UNKNOWN
                            return

                    raise e

            def __eq__(i_i_self, other):
                return i_i_self._eq(other)

            def __hash__(i_i_self):
                return i_i_self._hash

        def __init__(i_self):
            set.__init__(i_self)

        def add(i_self, object_: Any) -> bool:
            """Appends a value to the __Holder."""
            temp = i_self.ValNode(object_)
            set.add(i_self, temp)
            return tuple(set.intersection(i_self, {temp}))[0]

        def __contains__(i_self, item):
            temp = i_self.ValNode(item)
            return set.__contains__(i_self, temp)

        def remove(i_self, __element):
            temp = i_self.ValNode(__element)
            set.remove(i_self, temp)

    class _ValuesView:
        """An object used to view the values inside a MultiKeyDict."""
        def __init__(i_self, parent: 'MultiKeyDict'):
            i_self.parent = parent
            i_self._index = 0
            i_self._values = list(parent._holder)

        def __iter__(i_self):
            return i_self

        def __next__(i_self):
            if i_self._index < len(i_self._values):
                i_self._index += 1
                return i_self._values[i_self._index - 1].value

            raise StopIteration

    class _ItemsView:
        """An object used to view the items inside a MultiKeyDict."""
        def __init__(i_self, parent: 'MultiKeyDict'):
            i_self.parent = parent
            i_self.keys = list(parent.keys())
            i_self._index = 0

        def __iter__(i_self):
            return i_self

        def __next__(i_self):
            if i_self._index < len(i_self.keys):
                i_self._index += 1
                key = i_self.keys[i_self._index - 1]
                return key, dict.__getitem__(i_self.parent, key).value

            raise StopIteration

    def __init__(self, map_: Mapping = ..., **kwargs):
        """
        Checks a mapping for keys using the same value and assigns them a
        reference to a holder for the value.

        :param map_: A mapping
        :param kwargs: Keywords to use to build a mapping or add on to a
            mapping.
        """
        self._holder = self.__Holder()
        dict.__init__(self)
        if map_ is ...:
            map_ = {}

        temp_dict = dict(map_, **kwargs)
        for key, val in temp_dict.items():
            self._process_key_val_pair(key, val)

    def _process_key_val_pair(self, keys: Iterable, value):
        """
        Internal method that processes a key-value pair.

        :param keys: key will be iterated over to create new key-val pairs.
        :param value: value will be searched for in existing values. If the
            value is found, the _Holder reference of that value will be used to
            represent it in generated key-val pairs. If not, a new _Holder
            reference will be created to represent it in key-val pairs.
        """
        if not isinstance(keys, Iterable) or type(keys) is str:
            keys = [keys]

        for key in keys:
            dict.__setitem__(self, key, self._holder.add(value))

    def __getitem__(self, key):
        """
        Used to get the value of a key from the MultiKeyDict.

        :param key: This may be a tuple, and if it is, a list of the values for
            the keys passed will be returned. Otherwise, the key passed will be
            located, and its corresponding value returned. Will raise an
            exception if the key is not in the MultiKeyDict.
        :return: The value corresponding to the key if a single key was passed.
            Otherwise, the values corresponding to the keys in the form of a
            tuple.
        """
        if type(key) is tuple:
            answer = tuple(dict.__getitem__(self, k).value for k in key)
            if len(answer) == 1:
                return answer[0]

            else:
                return answer

        return dict.__getitem__(self, key).value

    def __setitem__(self, key, value):
        """
        Used to set key-val pairs for the MultiKeyDict.

        :param key: If anything other than a tuple is used for the key, it
            will be converted to a list of one element. The keys passed will
            then be assigned the appropriate values, and their old values will
            be checked to ensure they are still needed. If any values become
            unutilized, they will be deleted.
        :param value: The value to assign to key(s).
        """
        self._process_key_val_pair(key, value)

    def __delitem__(self, key):
        """
        Used to delete keys from the MultiKeyDict.

        :param key: If anything other than a tuple is used as the key, it will
            be converted to a list of one element. The keys passed will then be
            deleted from the dictionary, and if any values become unutilized,
            they will be deleted as well.
        """
        if type(key) is not tuple:
            key = [key]

        # construct a set of values possibly removed and remove keys
        counter = set()
        for k in key:
            counter.add(dict.__getitem__(self, k))
            dict.__delitem__(self, k)

        # if any values are completely removed, delete them
        val_list = set(dict.values(self))
        for v in counter:
            if v not in val_list:
                self._holder.remove(v)

    def values(self) -> _ValuesView:
        """
        Returns an iterable to view the values in a MultiKeyDict. Values are
        treated as unique.

        :return: MultiKeyDict._ValuesView
        """
        return self._ValuesView(self)

    def items(self) -> _ItemsView:
        """
        Returns an iterable to view items in a MultiKeyDict.

        :return: MultiKeyDict._ItemsView
        """
        return self._ItemsView(self)

    def pop(self, key, default=...):
        """
        Pop the value(s) corresponding to given key(s). A value will only be
        fully-removed if there are no longer any keys referencing it.

        :param key: If a single item is used as a key, it will be converted to
            a list of one element for searches. The key(s) passed will be
            located if possible, and their corresponding value(s) returned in a
            list.
        :param default: The default value used to fill in for keys that don't
            exist.
        :return: A tuple of the values corresponding to the keys if multiple
            keys were sought. Otherwise the value corresponding to the key
            sought.
        """
        if type(key) is not tuple:
            key = [key]

        # construct a set of values possibly removed and pop keys and values
        output = []
        # if default is ..., will have to test each key to verify it exists.
        if default is ...:
            for k in key:
                if key not in self:
                    raise KeyError(f"{repr(k)}")

                output.append(dict.pop(self, k))

        # do not need to test if there is a default
        else:
            for k in key:
                output.append(dict.pop(self, k, default))

        # if any values are completely removed, delete them
        val_list = set(dict.values(self))
        for v in output:
            if v not in val_list:
                self._holder.remove(v)

        return output[0].value if len(output) == 1 \
            else tuple(v.value for v in output)

    def pop_unique(self, key, default=...):
        """
        Pop the value(s) corresponding to given key(s). A value will only be
        fully-removed if there are no longer any keys referencing it. Will
        only return unique values.

        :param key: If a single item is used as a key, it will be converted to
            a list of one element for searches. The key(s) passed will be
            located if possible, and their corresponding value(s) returned in a
            list.
        :param default: The default value used to fill in for keys that don't
            exist.
        :return: A tuple of the unique values corresponding to the keys if
            multiple keys were sought. Otherwise the value corresponding
            to the key sought.
        """
        if type(key) is not tuple:
            key = [key]

        # construct a set of values possibly removed and pop keys and values
        counter = set()
        # if default is ..., will have to test each key to verify it exists.
        if default is ...:
            for k in key:
                if k not in self:
                    raise KeyError(f"{repr(k)}")

                counter.add(dict.pop(self, k))

        # do not need to test if there is a default
        else:
            for k in key:
                counter.add(dict.pop(self, k, default))

        # if any values are completely removed, delete them
        val_list = set(dict.values(self))
        for v in counter:
            if v not in val_list:
                self._holder.remove(v)

        return [v.value for v in counter]

    def get(self, *keys, default=...) -> Any:
        """
        Used to get the value(s) of key(s) from the MultiKeyDict without the
        likelihood of raising an exception. Will return values in a tuple
        format, and will only return unique values.

        :param keys: If a single item is used as a key, it will be converted to
            a list of one element for searches. The key(s) passed will be
            located if possible, and their corresponding value(s) returned in a
            list.
        :param default: The default value used to fill in for keys that don't
            exist.
        :return: A tuple of the values corresponding to the keys if multiple
            keys were sought. Otherwise the value corresponding to the key
            sought.
        """
        output = []
        for k in keys:
            if k not in self:
                output.append(default)
                continue

            output.append(dict.__getitem__(self, k).value)

        return output[0] if len(output) == 1 else tuple(output)

    def get_items(self, keys: Iterable, default=...) -> dict:
        """
        Used to get the items corresponding to an Iterable of keys. Will
        not raise an error for keys that don't exist.

        :param keys: An Iterable which contains keys whose values are sought.
        :param default: The default value for keys that don't exist. If not
            specified, will omit keys that don't exist from the output
            dictionary.
        :return: A dictionary with the items that were found.
        """
        output = {}
        for k in keys:
            if k not in self:
                if default is not ...:
                    output[k] = default

                continue

            output[k] = dict.__getitem__(self, k).value

        return output

    def get_unique(self, *keys, default=...):
        """
        Used to get the value(s) of key(s) from the MultiKeyDict without the
        likelihood of raising an exception. Will return values in a tuple
        format, and will only return unique values.

        :param keys: If a single item is used as a key, it will be converted to
            a list of one element for searches. The key(s) passed will be
            located if possible, and their corresponding value(s) returned in a
            list.
        :param default: The default value used to fill in for keys that don't
            exist. If left empty, missing keys will not insert any value.
        :return: A tuple of the unique values corresponding to the keys if
            multiple keys were sought. Otherwise, the value corresponding to
            the key sought.
        """
        counter = set()
        default_in = False
        # if default is ..., will have to test each key to verify it exists.
        if default is ...:
            for k in keys:
                if k in self:
                    counter.add(dict.__getitem__(self, k))

        # do not need to test if there is a default
        else:
            for k in keys:
                if k in self:
                    ans = dict.get(self, k, default)
                    counter.add(ans)

                else:
                    default_in = True

        output = [v.value for v in counter]
        if default_in:
            output.append(default)

        return output

    def update(self, __m: Mapping = None, **kwargs) -> None:
        """
        Used to integrate another mapping into this one.

        :param __m: The mapping to integrate.
        :param kwargs: Keyword args to construct from.
        """
        d = dict(__m, **kwargs) if __m is not None else dict(**kwargs)
        for key, val in d.items():
            self._process_key_val_pair(key, val)
