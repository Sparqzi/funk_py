from typing import Any, Mapping, Iterable


class MultiKeyDict(dict):
    class __Holder(list):
        """Holds and acts as a reference for values in the MultiKeyDict."""
        class ValNode:
            __slots__ = 'value', 'pos'

            def __hash__(self):
                return self.pos

        def __init__(i_self):
            list.__init__(i_self)

        def append(i_self, object_: Any) -> bool:
            """Appends a value to the __Holder."""
            c = type(object_)
            for obj in i_self:
                if (c is type(obj.value) and object_ == obj.value) or \
                        (obj.value is None and object_ is None):
                    return True

            list.append(i_self, i_self.ValNode())
            list.__getitem__(i_self, -1).value = object_
            list.__getitem__(i_self, -1).pos = len(i_self) - 1
            return False

        def index(i_self, value: Any, start: int = ...,
                  stop: int = ...) -> int:
            if value is None:
                for i in range(len(i_self)):
                    if list.__getitem__(i_self, i).value is None:
                        return i

            else:
                for i in range(len(i_self)):
                    if list.__getitem__(i_self, i).value == value:
                        return i

            raise ValueError(f"'{value}' is not in __Holder")

        def __contains__(i_self, item):
            if item is None:
                for obj in list.__iter__(i_self):
                    if obj.value is None:
                        return True

            else:
                for obj in list.__iter__(i_self):
                    if obj.value == item:
                        return True

            return False

        def __setitem__(i_self, index: int, value):
            t = list.__getitem__(i_self, index)
            t.value = value

        def __getitem__(i_self, index: int):
            return list.__getitem__(i_self, index)

        def __delitem__(i_self, index: int):
            for i in range(index + 1, len(i_self)):
                list.__getitem__(i_self, i).pos -= 1

            list.__delitem__(i_self, index)

    class _ValuesView:
        """An object used to view the values inside of a MultiKeyDict."""
        def __init__(i_self, parent: 'MultiKeyDict'):
            i_self.parent = parent
            i_self._index = 0

        def __iter__(i_self):
            return i_self

        def __next__(i_self):
            h = i_self.parent._holder
            if i_self._index < len(h):
                i_self._index += 1
                return h[i_self._index - 1].value

            raise StopIteration

    class _ItemsView:
        """An object used to view the items inside of a MultiKeyDict."""
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

    def __init__(self, map_: Mapping, **kwargs):
        """
        Checks a mapping for keys using the same value and assigns them a
        reference to a holder for the value.

        :param map_: A mapping
        :param kwargs: Keywords to use to build a mapping or add on to a
            mapping.
        """
        self._holder = self.__Holder()
        dict.__init__(self)
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

        i = self._holder.index(value) if self._holder.append(value) else -1
        for key in keys:
            dict.__setitem__(self, key, self._holder[i])

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
                del self._holder[v.pos]

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
                del self._holder[v.pos]

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
                del self._holder[v.pos]

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
            multiple keys were sought. Otherwise the value corresponding to
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
                ans = dict.get(self, k, default)
                if ans is default \
                        or ans == default and type(default) == type(ans):
                    default_in = True

                else:
                    counter.add(ans)

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
