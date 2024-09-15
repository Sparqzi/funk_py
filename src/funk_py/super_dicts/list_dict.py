from typing import Union, Callable, Any, Tuple, Iterable


class ListDict(list):
    def __init__(self, key_function: Callable, values: Iterable = ...):
        """
        A list that sort of acts like a dictionary...

        :param key_function: The function that should be called on each item to get its appropriate
            key.
        :param values: The values that should be put in the list.
        """
        list.__init__(self)
        self.__key_function = key_function
        if values is not ...:
            for item in values:
                list.append(self, self.__process_item(item))

    def __process_item(self, item) -> Tuple[Any, str]:
        """
        An internal helper function used to apply the key_function to incoming values.

        :param item: The item that needs to be converted to a key-value pair.
        :return: A tuple consisting of the value and key for the item.
        """
        return item, self.__key_function(item)

    def __locate_index(self, key: Union[str, int, slice, Tuple[str, int]]) -> int:
        """
        An internal helper function used to determine what index an item should be at. Will throw an
            error if the key is invalid.

        :param key: The key/index that should be sought.
        :return: An integer indicating the item's index in the list.
        """
        if type(key) in [int, slice]:
            return key

        elif type(key) is tuple:
            target_count = key[1]
            key = key[0]

        else:
            target_count = 1

        count = 0
        for i in range(len(self)):
            if list.__getitem__(self, i)[1] == key:
                count += 1
                if count == target_count:
                    return i

        raise KeyError(key)

    def __setitem__(self, key: Union[str, int, slice, Tuple[str, int]], value) -> None:
        """
        Sets an item in the ListDict. Will raise an exception if the item index cannot be
            determined.

        :param key: If this is a ``str``, will attempt to find an item with a matching key. Will
            raise an exception if it cannot be located. If this is an ``int`` or a ``slice``, normal
            list indexing rules will be used to search. If this is a ``tuple`` consisting of a
            ``str`` and an ``int`` (*n), it will attempt to find items with matching keys, then
            replaces the *nth* element with a matching key.
        :param value: The value that should be assigned in place of the old value.
        :return: Does not return anything.
        """
        index = self.__locate_index(key)
        if type(index) is slice:
            list.__setitem__(self, index, [self.__process_item(val) for val in value])

        else:
            list.__setitem__(self, index, self.__process_item(value))

    def __getitem__(self, key: Union[str, int, slice, Tuple[str, int]]) -> Any:
        """
        Gets an item from the ListDict. Will raise an exception if the item index cannot be
            determined.

        :param key: If this is a ``str``, will attempt to find an item with a matching key. Will
            raise an exception if it cannot be located. If this is an ``int`` or a ``slice``, normal
            list indexing rules will be used to search. If this is a ``tuple`` consisting of a
            ``str`` and an ``int`` (*n*), will attempt to find items with matching keys, then return
            the *nth* element with a matching key.
        :return: The item(s) at the desired key/index.
        """
        if type(key) is slice:
            return self.__class__([t[0] for t in list.__getitem__(self, self.__locate_index(key))])

        return list.__getitem__(self, self.__locate_index(key))[0]

    def get(self, key: Union[str, Tuple[str, int]], default: Any = None) -> Any:
        """
        Gets an item from the ``ListDict`` by *key*. Will not raise an exception if the *key*
        does not exist, but will instead return default.

        :param key: If this is a ``str``, will attempt to find an item with a matching key. If this
            is a ``tuple`` consisting of a ``str`` and an ``int`` (*n*), will attempt to find items
            with matching keys, then return the *nth* element with a matching key.
        :param default: The default value to return if requested key does not exist.
        :return: The item at the desired key or - should the key not be found - default.
        """
        if type(key) in [int, slice]:
            raise KeyError(f'{repr(key)} is not a valid key for {type(self)}.')

        try:
            return list.__getitem__(self, self.__locate_index(key))

        except KeyError:
            return default

    def pop(self, key: Union[str, int, Tuple[str, int]] = ...) -> Any:
        """
        Pops an item from the ``ListDict``. Will raise an exception if the item index cannot be
            determined.

        :param key: If this is a ``str``, will attempt to find an item with a matching key. Will
            raise an exception if it cannot be located. If this is an ``int``, normal list indexing
            rules will be used to search. If this is a ``tuple`` consisting of a ``str`` and an
            ``int`` (*n*), will attempt to find items with matching keys, then return the *nth*
            element with a matching key. If omitted, the last item in the list will be returned.
        :return: The item at the desired key/index, will also delete from the list.
        """
        if not len(self):
            raise IndexError('pop from empty list')

        if key is ...:
            return list.pop(self)

        else:
            return list.pop(self, self.__locate_index(key))

    def __delitem__(self, key) -> None:
        """
        Deletes an item from the ListDict. Will raise an exception if the item index cannot be
            determined.

        :param key: If this is a ``str``, will attempt to find an item with a matching key. Will
            raise an exception if it cannot be located. If this is an ``int`` or a ``slice``, normal
            list indexing rules will be used to search. If this is a ``tuple`` consisting of a
            ``str`` and an ``int`` (*n*), will attempt to find items with matching keys, then return
            the *nth* element with a matching key.
        :return: No return.
        """
        list.__delitem__(self, self.__locate_index(key))

    def __contains__(self, item) -> bool:
        """
        Figure out if an item is contained in the ``ListDict``.

        :param item: If this is a ``str``, a search for a key will be done. Otherwise, a search for
            an exact match will be carried out.
        :return: A bool indicating whether the item was found in the ``ListDict``.
        """
        if type(item) is str:
            for i in range(len(self)):
                if list.__getitem__(self, i)[1] == item:
                    return True

        else:
            for i in range(len(self)):
                if list.__getitem__(self, i)[0] == item:
                    return True

        return False

    def append(self, obj) -> None:
        """Append an item..."""
        list.append(self, self.__process_item(obj))

    def extend(self, iterable: Iterable) -> None:
        """Extend with an iterable..."""
        list.extend(self, [self.__process_item(item) for item in iterable])

    def remove(self, value) -> None:
        """Remove a value..."""
        found = False
        for i in range(len(self)):
            if list.__getitem__(self, i) == value:
                list.__delitem__(self, i)
                found = False
                break

        if not found:
            raise ValueError(f'{repr(value)} not in {type(self)}.')

    def values(self) -> Iterable:
        """Get an iterable of the values of the ListDict..."""
        return iter(item[0] for item in list.__iter__(self))

    def keys(self) -> Iterable:
        """Get an iterable of the keys of the ListDict..."""
        return iter(item[1] for item in list.__iter__(self))

    def items(self) -> Iterable:
        """Get an iterable of the keys and values of the ListDict..."""
        return list.__iter__(self)

    def insert(self, index: int, obj) -> None:
        """Insert a value into the ListDict..."""
        list.insert(self, index, self.__process_item(obj))

    def index(self, value, start: int = ..., stop: int = ...) -> int:
        """Find the index of a value in the ListDict..."""
        return list.index(list(self.values()), value, start, stop)

    def __iter__(self) -> Iterable:
        """Iterate over the values of the ListDict..."""
        return iter(item[0] for item in list.__iter__(self))
