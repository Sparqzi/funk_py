from typing import Union, Optional, Tuple, Mapping, Hashable, Iterable


class MultiValueDict(dict):
    def __init__(self, __m: Mapping = None, **kwargs):
        """
        A dictionary where each key can have multiple values. Values for this
        dictionary should be hashable.

        :param __m: Initialize dictionary from mappings.

        :param kwargs: Initialize dictionary from key-val pairs.
        """
        if __m is None:
            __m = {}

        __m = dict(__m)
        __m.update(kwargs)

        dict.__init__(self, MultiValueDict.__convert_dict(__m))

    @staticmethod
    def __convert_dict(dictionary: dict,
                       builder: dict = None) -> Optional[dict]:
        """
        An internal helper function that handles converting a dictionary and
        either adding it to an existing dictionary or returning a new one.

        :param dictionary: A dictionary containing the key-val pairs that
            should be added.
        :param builder: A builder which new keys and values should be added
            to.
        :return: Returns a dictionary when no builder was passed. Otherwise
            operates on builder.
        """
        b_was_none = False
        if builder is None:
            b_was_none = True
            builder = {}

        for key, val in dictionary:
            if key not in builder:
                builder[key] = set()

            if type(val) is list:
                for i_val in val:
                    builder[key].add(i_val)

            else:
                builder[key].add(val)

        if b_was_none:
            return builder

    def __setitem__(self, key, value: Union[list, Hashable]):
        """
        Set a value or multiple values in the dict by key.

        :param key: The key to add the value at.
        :param value: The value to add.
        """
        if key in self:
            dict.__setitem__(self, key,
                             set(value)
                             if type(value) is list
                             else {value})

        else:
            dict.__setitem__(self, key, set())
            dict.__getitem__(self, key).add(value)

    def __getitem__(self, key):
        """Get an item from the dict by key."""
        return list(dict.__getitem__(self, key))

    def __delitem__(self, key: Union[str, Tuple[str, Hashable]]):
        """
        Delete a key-val pair from the dict by key. Can also be used to target
        a specific value or index.

        :param key: If a str is given, will check for the key with that string.
            If a tuple of a str and any hashable object is given, will check
            first for the key, then for the hashable object then delete
            that object from the key. Will delete the key if there is nothing
            left in its set.
        """
        if type(key) is tuple:
            if key[0] in self:
                if key[1] in (t := dict.__getitem__(self, key[1])):
                    if len(t) > 1:
                        t.remove(key[1])

                    else:
                        dict.__delitem__(self, key[0])

            else:
                raise KeyError(repr(key))

        elif key in self:
            dict.__delitem__(self, key)

        else:
            raise KeyError(repr(key))

    def update(self, __m: Mapping = None, **kwargs) -> None:
        """
        Update this MultiValueDict with another dict's values.

        :param __m: Add a mapping.
        :param kwargs: Add key-val pairs via keyword args.
        """
        if __m is None:
            __m = {}

        __m = dict(__m)
        __m.update(**kwargs)

        temp = dict(self)
        MultiValueDict.__convert_dict(__m, temp)
        dict.update(temp)

    def add_to_keys(self, keys: Iterable, value: Hashable):
        """
        Add a value to multiple keys in this MultiValueDict. Will add keys
        if they do not exist already.

        :param keys: An iterable containing the keys to add the value to.
        :param value: The value to be added to the keys.
        """
        for key in keys:
            if key in self:
                dict.__getitem__(self, key).add(value)

            else:
                dict.__setitem__(self, key, {value})

    def __iadd__(self,
                 other: Union[Tuple[str, Hashable], Tuple[str, Iterable]]):
        if type(other) is tuple:
            if isinstance(other[1], Hashable):
                if other[0] in self:
                    dict.__getitem__(self, other[0]).add(other[1])
                    return

                dict.__setitem__(self, other[0], {other[1]})
                return

            elif isinstance(other[1], Iterable):
                if other[0] in self:
                    temp = dict.__getitem__(self, other[0])
                    for item in other[1]:
                        temp.add(item)

                    return

                dict.__setitem__(self, other[0], set(other[1]))
                return

        raise ValueError(f'{type(other)} cannot be added to {type(self)}.')
