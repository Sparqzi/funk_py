import builtins
from functools import wraps
from typing import Mapping, overload, Iterable, Union, Tuple


class Obj(dict):
    """
    ``Obj`` is a sort of wishy-washy map where branches can be implicitly
    generated easily.
        For example:

        .. code-block:: python

            holder = Obj()
            holder.inner.name = 42
            holder.outer[52] = 7
            holder.outer[37] = 'lorem'
            holder['general'] = 'Washington'

        Should generate:

        .. code-block:: python

            {
                'inner': {
                    'name': 42
                },
                'outer': {
                    52: 7,
                    37: 'lorem'
                },
                'general': 'Washington'
            }

    It has :meth:`~Obj.as_list` and :meth:`~Obj.as_tuple` methods which can be
    used to return only the values of the dict, and an :meth:`~Obj.as_dict`
    option which will return the entire dict.

    It can also be :meth:`hardened <Obj.harden>` so that new keys cannot be
    added and existing keys cannot be removed.
    """
    @overload
    def __init__(self, **kwargs): ...
    @overload
    def __init__(self, map_: Mapping, **kwargs): ...
    @overload
    def __init__(self, iterable: Iterable, **kwargs): ...

    def __init__(self, map_: Mapping = ..., **kwargs):
        if map_ is not ...:
            dict.__init__(self, map_, **kwargs)

        else:
            dict.__init__(self, **kwargs)

        # Always use super's __setattr__ method to avoid triggering own
        # __setattr__ method.
        dict.__setattr__(self, '_Obj__hardened', False)
        # The following is used by __setattr__ and __getattr__ methods later to
        # handle attributes that are not (usually) going to be set by the user
        # directly. It should primarily be for things like *shape*.
        dict.__setattr__(self, '_HIDE_THESE', ['shape'])

    _GEN_ERR = 'This Obj has been hardened. It can no longer {}.'

    @property
    def is_hardened(self) -> bool:

        return dict.__getattribute__(self, '_Obj__hardened')

    def harden(self):
        """
        *Hardens* the ``Obj``.

        When an ``Obj`` is hardened:

        - New keys/attributes may not be added to it and attempts to add new
          keys/attributes will fail, raising an exception.
        - Current keys/attributes may not be removed from it and attempts to do
          so will fail, raising an exception.

        .. warning::
            This will erase and replace the existing ``__setitem__``,
            ``__setattr__``, ``__getattr__``, ``__delitem__``, ``__delattr__``,
            ``pop``, ``popitem``, ``clear``, and ``update`` methods of the
            instance.
        """
        dict.__setattr__(self, '_Obj__hardened', True)

        no_new_msg = Obj._GEN_ERR.format('have new keys created')
        no_del_msg = Obj._GEN_ERR.format('have keys removed')
        blocked_msg = ('This Obj has been hardened. While the target key'
                       ' exists, it can not be changed because it is also an'
                       ' instance of Obj.')

        def to_wrap(attr):
            return wraps(dict.__getattribute__(self, attr))

        # Create new functions that will raise exceptions when trying to add or
        # remove keys and assign them in place of the original functions.
        @to_wrap('__getattr__')
        def new_getattr(i_self, item):
            # The following prevents *system* variables from effecting the
            # dictionary representation of the Obj.
            # Use the super's __getattribute__ method to prevent infinite loops
            # and to keep background data from being considered as elements in
            # the dictionary.
            if item in dict.__getattribute__(i_self, '_HIDE_THESE'):
                return dict.__getattribute__(i_self, item)

            if item not in i_self:
                raise AttributeError(
                    Obj.GEN_ERR.format('generate missing keys'), name=item)

            return i_self[item]

        @to_wrap('__setattr__')
        def new_setattr(i_self, key, value):
            # The following prevents *system* variables from effecting the
            # dictionary representation of the Obj.
            # Use the super's __getattribute__ and __setattr__ methods to
            # prevent infinite loops and to keep background data from being
            # considered as elements in the dictionary.
            if key in dict.__getattribute__(self, '_HIDE_THESE'):
                dict.__setattr__(self, key, value)

            if key in i_self:
                if isinstance(dict.__getitem__(i_self, key), Obj):
                    raise AttributeError(blocked_msg, name=key)

                dict.__setitem__(i_self, key, value)

            else:
                raise AttributeError(no_new_msg, name=key)

        @to_wrap('__setitem__')
        def new_setitem(i_self, key, value):
            # This method should not require the same check for *system*
            # variables that setattr requires. This is simply because its use
            # means the user actually intends to set the corresponding key-value
            # pair.
            # Items in _HIDE_THESE can be entered as keys before hardening, so
            # long as they are not set as an attribute, but instead as an actual
            # key-value pair.
            if key in i_self:
                dict.__setitem__(i_self, key, value)

            else:
                raise AttributeError(no_new_msg, name=key)

        @to_wrap('pop')
        def new_pop(i_self, key, default=...):
            raise AttributeError(no_del_msg, name=key)

        def new_delattr(i_self, item=...):
            raise AttributeError(no_del_msg, name=item)

        @to_wrap('clear')
        def new_clear(i_self):
            raise AttributeError(no_del_msg, name='ALL KEYS')

        @to_wrap('update')
        def new_update(i_self, map_: Mapping = ..., **kwargs):
            map_ = {} if map_ is ... else map_
            map_ = dict(map_) if not isinstance(map_, Mapping) else map_
            map_.update(kwargs)

            bad_keys, blocked_keys = i_self._scan_dead_keys(map_)

            if len(bad_keys):
                if len(blocked_keys):
                    raise AttributeError(
                        no_new_msg + ' Not even via update.\n' + blocked_msg,
                        name=f'Missing Keys: {repr(bad_keys)}\n'
                             f'Blocked Keys: {repr(blocked_keys)}')

                else:
                    raise AttributeError(no_new_msg + ' Not even via update.',
                                         name=repr(bad_keys))

            elif len(blocked_keys):
                raise AttributeError(blocked_msg, name=repr(blocked_keys))

            # Do not call dict.update here, it will cause any required
            # dict->Obj conversions not to occur.
            # any data in map_ should have been transferred to kwargs at the
            # beginning of this.
            i_self._no_check_update(map_)

        dict.__setattr__(self, '__getattr__', new_getattr)
        dict.__setattr__(self, '__setattr__', new_setattr)
        dict.__setattr__(self, '__setitem__', new_setitem)
        dict.__setattr__(self, 'pop', new_pop)
        dict.__setattr__(self, '__delattr__',
                         to_wrap('__delattr__')(new_delattr))
        dict.__setattr__(self, '__delitem__',
                         to_wrap('__delitem__')(new_delattr))
        dict.__setattr__(self, 'popitem', to_wrap('popitem')(new_delattr))
        dict.__setattr__(self, 'update', new_update)

        for val in self.values():
            if isinstance(val, Obj):
                val.harden()

    def _scan_dead_keys(self, map_: Mapping):
        # The reason this is written to NOT fail fast is so that as much
        # information as possible about what was wrong can be collected.
        bad_keys = []
        blocked_keys = []
        for key, val in map_.items():
            if key not in self:
                bad_keys.append(key)

            elif isinstance(t := dict.__getitem__(self, key), Obj):
                if isinstance(val, dict):
                    _bad_keys, _blocked_keys = t._scan_dead_keys(val)
                    bad_keys.extend(_bad_keys)
                    blocked_keys.extend(_blocked_keys)

                else:
                    blocked_keys.append(key)

        return bad_keys, blocked_keys

    def _no_check_update(self, map_: Mapping):
        """
        This method simply updates the dictionary without a check for
        collisions or bad keys. On a hardened ``Obj``, it is to be used only
        all key-value pairs are verified to be safe to add. On an unhardened
        ``Obj``, it should be safe.
        """
        for key, val in map_.items():
            if key in self:
                if isinstance(t := dict.__getitem__(self, key), Obj):
                    t._no_check_update(val)

                else:
                    dict.__setitem__(self, key, val)

            else:
                dict.__setitem__(self, key, val)

    @overload
    def update(self, **kwargs): ...

    @overload
    def update(self, iterable: Iterable, **kwargs): ...

    def update(self, map_: Mapping = ..., **kwargs):
        """
        This method updates the ``Obj`` much the same way that
        ``dict.update`` works. The major difference is that if a dictionary is
        set as the value for a key that already has an ``Obj`` as its value, the
        dictionary will be used to update the existing ``Obj`` instead of
        replacing it.
        """
        map_ = {} if map_ is ... else map_
        map_ = dict(map_) if not isinstance(map_, Mapping) else map_
        map_.update(kwargs)
        self._no_check_update(map_)

    def __getattr__(self, item):
        # The following prevents *system* variables from effecting the
        # dictionary representation of the Obj.
        # Use the super's __getattribute__ method to prevent infinite loops and
        # to keep background data from being considered as elements in the
        # dictionary.
        if item in dict.__getattribute__(self, '_HIDE_THESE'):
            return dict.__getattribute__(self, item)

        if item not in self:
            gimme = self[item] = Obj()
            return gimme

        return self[item]

    def __setattr__(self, key, value):
        # The following prevents *system* variables from effecting the
        # dictionary representation of the Obj.
        # Use the super's __getattribute__ and __setattr__ methods to prevent
        # infinite loops and to keep background data from being considered as
        # elements in the dictionary.
        if key in dict.__getattribute__(self, '_HIDE_THESE'):
            dict.__setattr__(self, key, value)

        else:
            self[key] = value

    def __delattr__(self, item):
        if item in self:
            dict.__delitem__(self, item)

    def _as_thing(self, thing: type, recur: Union[type, Tuple[type]] = ...):
        type_converter_map = {
            list: 'as_list',
            tuple: 'as_tuple',
            dict: 'as_dict'
        }

        def recursive_conversion(func, plug):
            return {
                k: getattr(v, type_converter_map[func])(plug) if isinstance(v, Obj) else v
                for k, v in dict.items(self)
            }

        match recur:
            case builtins.list | builtins.tuple | builtins.dict:
                ans = recursive_conversion(recur, recur)

            case [t, *rest] if t in (list, tuple, dict):
                ans = thing(recursive_conversion(recur[0],
                                                 rest if len(rest) else ...))

            case _:
                ans = dict.copy(self)

        if thing is dict:
            return ans

        return thing(ans.values())

    def as_list(self, recur: Union[type, Tuple[type]] = ...) -> list:
        """
        Generates a ``list`` of the values in an ``Obj``. These values may or
        may not be in the expected order.

        :param recur: The type of conversion that should be used on
            internally-nested ``Objs``. Valid types for this are ``list``,
            ``tuple``, and ``dict``, and it can be specified either for the
            entire depth of the ``Obj`` or as a tuple of those types to be used
            for each depth. If it is not provided, nested ``Objs`` will be
            included as-is.

            For Example:

            .. code-block:: python

                holder = Obj()
                holder.lorem.ipsum = 5
                holder.lorem.dolor = 6
                holder.lorem.sit = 7
                holder.amet.consectetur = 1
                holder.amet.adipiscing = 2
                holder.amet.elit.sed = 3
                holder.amet.elit.tempor = 4
                holder.sagittis[0] = 55
                holder.sagittis[1] = 56
                holder.sagittis[2] = 57
                holder.sagittis[3] = 58
                holder[543] = 'mi'

            ... which should essentially be ...

            .. code-block:: python

                {
                    'lorem': {
                        'ipsum': 5,
                        'dolor': 6,
                        'sit': 7
                    },
                    'amet': {
                        'consectetur': 1,
                        'adipiscing': 2,
                        'elit': {
                            'sed': 3,
                            'tempor': 4
                        }
                    },
                    'sagittis': {
                        0: 55,
                        1: 56,
                        2: 57,
                        3: 58
                    },
                    543: 'mi'
                }

            ... should behave in the following manner:

            Example 1 - No Recursive Re-formatting:

            .. code-block:: python

                ans = holder.as_list()

            ans should be:

            .. code-block:: python

                [
                    Obj({'ipsum': 5, 'dolor': 6, 'sit': 7}),
                    Obj({'consectetur': 1, 'adipiscing': 2,
                         'elit': Obj({'sed': 3, 'tempor': 4})}),
                    Obj({0: 55, 1: 56, 2: 57, 3: 58}),
                    'mi'
                ]

            Example 2 - Recur is a Type:

            .. code-block:: python

                ans = holder.as_list(list)

            ans should be:

            .. code-block:: python

                [
                    [5, 6, 7],
                    [1, 2, [3, 4]],
                    [55, 56, 57, 58],
                    'mi'
                ]

            Example 3 - Recur is a Tuple of Types (Longer than or Equal to
            the Max Depth of the Nesting):

            .. code-block:: python

                ans = holder.as_list((dict, tuple))

            ans should be:

            .. code-block:: python

                [
                    {'ipsum': 5, 'dolor': 6, 'sit': 7 },
                    {'consectetur': 1, 'adipiscing': 2, 'elit': (3, 4)},
                    {0: 55, 1: 56, 2: 57, 3: 58},
                    'mi'
                ]

            Example 4 - Recur is a Tuple of Types(Shorter than the Max Depth of
            the Nesting):

            .. code-block:: python

                ans = holder.as_list((tuple,))

            ans should be:

            .. code-block:: python

                [
                    (5, 6, 7),
                    (1, 2, Obj({'sed': 3, 'tempor': 4})),
                    (55, 56, 57, 58),
                    'mi'
                ]
        """
        return self._as_thing(list, recur)

    def as_tuple(self, recur: Union[type, Tuple[type]] = ...) -> tuple:
        """
        Generates a ``tuple`` of the values in an ``Obj``. These values may or
        may not be in the expected order.

        :param recur: The type of conversion that should be used on
            internally-nested ``Objs``. Valid types for this are ``list``,
            ``tuple``, and ``dict``, and it can be specified either for the
            entire depth of the ``Obj`` or as a tuple of those types to be used
            for each depth. If it is not provided, nested ``Objs`` will be
            included as-is.

            For Example:

            .. code-block:: python

                holder = Obj()
                holder.lorem.ipsum = 5
                holder.lorem.dolor = 6
                holder.lorem.sit = 7
                holder.amet.consectetur = 1
                holder.amet.adipiscing = 2
                holder.amet.elit.sed = 3
                holder.amet.elit.tempor = 4
                holder.sagittis[0] = 55
                holder.sagittis[1] = 56
                holder.sagittis[2] = 57
                holder.sagittis[3] = 58
                holder[543] = 'mi'

            ... which should essentially be ...

            .. code-block:: python

                {
                    'lorem': {
                        'ipsum': 5,
                        'dolor': 6,
                        'sit': 7
                    },
                    'amet': {
                        'consectetur': 1,
                        'adipiscing': 2,
                        'elit': {
                            'sed': 3,
                            'tempor': 4
                        }
                    },
                    'sagittis': {
                        0: 55,
                        1: 56,
                        2: 57,
                        3: 58
                    },
                    543: 'mi'
                }

            ... should behave in the following manner:

            Example 1 - No Recursive Re-formatting:

            .. code-block:: python

                ans = holder.as_tuple()

            ans should be:

            .. code-block:: python

                (
                    Obj({'ipsum': 5, 'dolor': 6, 'sit': 7}),
                    Obj({'consectetur': 1, 'adipiscing': 2,
                         'elit': Obj({'sed': 3, 'tempor': 4})}),
                    Obj({0: 55, 1: 56, 2: 57, 3: 58}),
                    'mi'
                )

            Example 2 - Recur is a Type:

            .. code-block:: python

                ans = holder.as_tuple(list)

            ans should be:

            .. code-block:: python

                (
                    [5, 6, 7],
                    [1, 2, [3, 4]],
                    [55, 56, 57, 58],
                    'mi'
                )

            Example 3 - Recur is a Tuple of Types (Longer than or Equal to
            the Max Depth of the Nesting):

            .. code-block:: python

                ans = holder.as_tuple((dict, tuple))

            ans should be:

            .. code-block:: python

                (
                    {'ipsum': 5, 'dolor': 6, 'sit': 7 },
                    {'consectetur': 1, 'adipiscing': 2, 'elit': (3, 4)},
                    {0: 55, 1: 56, 2: 57, 3: 58},
                    'mi'
                )

            Example 4 - Recur is a Tuple of Types(Shorter than the Max Depth of
            the Nesting):

            .. code-block:: python

                ans = holder.as_tuple((tuple,))

            ans should be:

            .. code-block:: python

                (
                    (5, 6, 7),
                    (1, 2, Obj({'sed': 3, 'tempor': 4})),
                    (55, 56, 57, 58),
                    'mi'
                )
        """
        return self._as_thing(tuple, recur)

    def as_dict(self, recur: Union[type, Tuple[type]] = ...) -> dict:
        """
        Generates a ``dict`` of the key-value pairs in an ``Obj``. These pairs
        may or may not be in the expected order.

        :param recur: The type of conversion that should be used on
            internally-nested ``Objs``. Valid types for this are ``list``,
            ``tuple``, and ``dict``, and it can be specified either for the
            entire depth of the ``Obj`` or as a tuple of those types to be used
            for each depth. If it is not provided, nested ``Objs`` will be
            included as-is.

            For Example:

            .. code-block:: python

                holder = Obj()
                holder.lorem.ipsum = 5
                holder.lorem.dolor = 6
                holder.lorem.sit = 7
                holder.amet.consectetur = 1
                holder.amet.adipiscing = 2
                holder.amet.elit.sed = 3
                holder.amet.elit.tempor = 4
                holder.sagittis[0] = 55
                holder.sagittis[1] = 56
                holder.sagittis[2] = 57
                holder.sagittis[3] = 58
                holder[543] = 'mi'

            ... which should essentially be ...

            .. code-block:: python

                {
                    'lorem': {
                        'ipsum': 5,
                        'dolor': 6,
                        'sit': 7
                    },
                    'amet': {
                        'consectetur': 1,
                        'adipiscing': 2,
                        'elit': {
                            'sed': 3,
                            'tempor': 4
                        }
                    },
                    'sagittis': {
                        0: 55,
                        1: 56,
                        2: 57,
                        3: 58
                    },
                    543: 'mi'
                }

            ... should behave in the following manner:

            Example 1 - No Recursive Re-formatting:

            .. code-block:: python

                ans = holder.as_tuple()

            ans should be:

            .. code-block:: python

                {
                    'lorem': Obj({'ipsum': 5, 'dolor': 6, 'sit': 7}),
                    'amet': Obj({'consectetur': 1, 'adipiscing': 2,
                         'elit': Obj({'sed': 3, 'tempor': 4})}),
                    'sagittis': Obj({0: 55, 1: 56, 2: 57, 3: 58}),
                    543: 'mi'
                }

            Example 2 - Recur is a Type:

            .. code-block:: python

                ans = holder.as_tuple(list)

            ans should be:

            .. code-block:: python

                {
                    'lorem': [5, 6, 7],
                    'amet': [1, 2, [3, 4]],
                    'sagittis': [55, 56, 57, 58],
                    543: 'mi'
                }

            Example 3 - Recur is a Tuple of Types (Longer than or Equal to
            the Max Depth of the Nesting):

            .. code-block:: python

                ans = holder.as_tuple((dict, tuple))

            ans should be:

            .. code-block:: python

                {
                    'lorem': {'ipsum': 5, 'dolor': 6, 'sit': 7 },
                    'amet': {'consectetur': 1, 'adipiscing': 2, 'elit': (3, 4)},
                    'sagittis': {0: 55, 1: 56, 2: 57, 3: 58},
                    543: 'mi'
                }

            Example 4 - Recur is a Tuple of Types(Shorter than the Max Depth of
            the Nesting):

            .. code-block:: python

                ans = holder.as_tuple((tuple,))

            ans should be:

            .. code-block:: python

                {
                    'lorem': (5, 6, 7),
                    'amet': (1, 2, Obj({'sed': 3, 'tempor': 4})),
                    'sagittis': (55, 56, 57, 58),
                    543: 'mi'
                }
        """
        return self._as_thing(dict, recur)
