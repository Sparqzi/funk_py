from inspect import getsource
import operator
from typing import Any, Callable, Optional, ParamSpec, overload, Mapping, Iterable, Union, Tuple

from funk_py.modularity.logging import make_logger, logs_vars

Args = ParamSpec("Args")


class Singleton:
    """
    A simple Singleton structure which when inherited from, will make a class follow the singleton
    pattern.
    """
    def __init_subclass__(cls, **kwargs):
        def __new__(cls_):
            if not hasattr(cls_, 'instance'):
                cls_.instance = super().__new__(cls_)

            return cls_.instance

        def __str__(self) -> str:
            return kwargs['str_']

        def __repr__(self) -> str:
            return kwargs['repr_']

        cls.__new__ = __new__
        cls.__str__ = __str__
        cls.__repr__ = __repr__

        return cls


class Shareable:
    __slots__ = ('v',)

    def __init__(self, v):
        """This class is really just a node with no concept of its relationship to other nodes."""
        self.v = v


def pass_(x: Any) -> Any:
    """Return ``x``."""
    return x


class Speed:
    """
    A simple structure which holds a number of times to do something and a time in seconds during
    which to do it.
    """
    def __init__(self, number: int, duration: float):
        self._number = number
        self._duration = duration

    @property
    def number(self) -> int:
        """The number of times to do the thing."""
        return self._number

    @property
    def duration(self) -> float:
        """The time in seconds to do it during."""
        return self._duration

    @property
    def rate(self):
        """The rate at which it would be done."""
        return self._number / self._duration

    def __eq__(self, other) -> bool: return self._comp(operator.eq, other)

    def __lt__(self, other) -> bool: return self._comp(operator.lt, other)

    def __le__(self, other) -> bool: return self._comp(operator.le, other)

    def __gt__(self, other) -> bool: return self._comp(operator.gt, other)

    def __ge__(self, other) -> bool: return self._comp(operator.ge, other)

    def __ne__(self, other) -> bool: return self._comp(operator.ne, other)

    def _comp(self, _operator, other):
        if isinstance(other, Speed):
            return _operator(self._number / self._duration, other)

        elif (t := type(other)) is int:
            return _operator(self._number // self._duration, other)

        elif t is float:
            return _operator(self._number / self._duration, other)

        else:
            raise TypeError(f'{type(other)} cannot be compared to a Speed.')

    def __add__(self, other) -> Union['Speed', int, float]:
        if isinstance(other, Speed):
            return Speed(self._number + other.number, self._duration + other.duration)

        elif (t := type(other)) is int:
            return self._number // self._duration + other

        elif t is float:
            return self.number / self.duration + other

        else:
            raise TypeError(f'{type(other)} cannot be added to a Speed.')

    def __sub__(self, other) -> Union['Speed', int, float]:
        if isinstance(other, Speed):
            return Speed(self._number - other.number, self._duration - other.duration)

        elif (t := type(other)) is int:
            return self._number // self._duration - other

        elif t is float:
            return self.number / self.duration - other

        else:
            raise TypeError(f'{type(other)} cannot be subtracted from a Speed.')

    def __truediv__(self, other) -> 'Speed':
        if isinstance(other, Speed):
            return Speed(self._number // other.number, self._duration / other.duration)

        elif (t := type(other)) is int:
            return Speed(self._number // other, self._duration)

        elif t is float:
            return Speed(self._number / other, self._duration)

        else:
            raise TypeError(f'{type(other)} cannot be subtracted from a Speed.')

    def __mul__(self, other) -> 'Speed':
        if isinstance(other, Speed):
            return Speed(self._number * other.number, self._duration * other.duration)

        elif type(other) in (int, float):
            return Speed(int(self._number * other), self._duration)

        else:
            raise TypeError(f'{type(other)} cannot be subtracted from a Speed.')

    def __neg__(self): raise TypeError('Speed is not allowed to be negative.')

    def __repr__(self): return f'<Speed number={self._number}, duration={self._duration}>'

    def __str__(self):
        return (f'{self._number} time{"" if self._number == 1 else "s"} per {self._duration} '
                f'second{"" if self._duration == 1 else "s"}')

    def __abs__(self): return self._number / self._duration


def simple_trinomial(check_func: Callable[[Any, Args], bool],
                     check_func2: Callable[[Any, Args], bool] = None) \
        -> Callable[[Any, Any, Args], Optional[bool]]:
    """
    Generates a callable which accepts two arguments and compares them via ``check_func`` or - if
    both are specified - ``check_func`` **and** ``check_func2``.
    - If only the first or only the second returns ``True``, the function will return ``False``.
    - If both return ``True``, the function will return ``True``.
    - If both return False, the function will return ``...`` (ellipsis).

    :param check_func: This is the first function used to check inputs. If ``check_func2`` is also
        specified, this will only be used to check the first input to the generated function. If
        ``check_func2`` is not specified, this will be used to check both inputs to the generated
        function. This may have varargs used, but if ``check_func2`` is specified, its signature
        should match.
    :param check_func2: This is the second function used to check inputs. If not specified, then
        ``check_func`` will be used to check both inputs to the generated function. This may have
        varargs used, but should only do so if ``check_func`` accepts them.
    :return: A function which can be used to check two values against ``check_func`` (and
        ``check_func2``) to verify if they both pass criteria, only one passes criteria, or neither
        passes criteria. Useful for checking for instances of classes.
    """
    if check_func2 is None:
        def check_it(val1, val2, *args) -> Optional[bool]:
            if check_func(val1, *args):
                return check_func(val2, *args)

            if check_func(val2, *args):
                return False

            return ...

        return check_it

    def check_it(val1, val2, *args) -> Optional[bool]:
        if check_func(val1, *args):
            return check_func2(val2, *args)

        if check_func2(val2, *args):
            return False

        return ...

    return check_it


obj_logger = make_logger('Obj', 'OBJ_LOGGING', show_function=False, default_level='warning',
                         TRACE=5)


class ObjAttributeError(AttributeError):
    """An error associated with setting or getting an attribute from an :class:`~Obj`."""
    pass


class Obj(dict):
    """
    ``Obj`` is a sort of wishy-washy map where branches can be implicitly generated easily.
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

    It has :meth:`~Obj.as_list` and :meth:`~Obj.as_tuple` methods which can be used to return only
    the values of the dict, and an :meth:`~Obj.as_dict` option which will return the entire dict.

    It can also be :meth:`hardened <Obj.harden>` so that new keys cannot be added and existing keys
    cannot be removed.
    """

    _GEN_ERR = 'This Obj has been hardened. It can no longer {}.'
    no_new_msg = _GEN_ERR.format('have new keys created')
    no_del_msg = _GEN_ERR.format('have keys removed')
    blocked_msg = ('This Obj has been hardened. While the target key exists, it can not be '
                   'changed because it is also an instance of Obj.')

    @overload
    def __init__(self, **kwargs): ...

    @overload
    def __init__(self, map_: Mapping, **kwargs): ...

    @overload
    def __init__(self, iterable: Iterable, **kwargs): ...

    @logs_vars(obj_logger, 'self',
               start_message='Initializing new instance of Obj...',
               start_message_level='info',
               end_message='Obj initialized.',
               end_message_level='info',
               var_message_level='trace')
    def __init__(self, map_: Mapping = ..., **kwargs):
        # Don't use dict.__init__ to add the map_ and kwargs, since nested maps should be
        # transformed to new Obj's, Obj should handle it with _no_check_update, since that will
        # check for those instances.
        dict.__init__(self)
        map_ = {} if map_ is ... else dict(map_)
        map_.update(kwargs)
        self._no_check_update(map_)

        # Always use super's __setattr__ method to avoid triggering own __setattr__ method.
        dict.__setattr__(self, '_hardened', False)
        # The following is used by __setattr__ and __getattr__ methods later to handle attributes
        # that are not (usually) going to be set by the user directly. It should primarily be for
        # things like *shape*.
        dict.__setattr__(self, '_HIDE_THESE', ['shape'])

    @property
    def is_hardened(self) -> bool:
        """
        Whether the ``Obj`` is hardened. When hardened, an ``Obj`` cannot have new keys assigned nor
        can existing keys be removed.
        """
        return dict.__getattribute__(self, '_hardened')

    def harden(self):
        """
        *Hardens* the ``Obj``.

        When an ``Obj`` is hardened:

        - New keys/attributes may not be added to it and attempts to add new keys/attributes will
          fail, raising an exception.

        - Current keys/attributes may not be removed from it and attempts to do so will fail,
          raising an exception.

        .. warning::
            This will erase and replace the existing ``__setitem__``, ``__setattr__``,
            ``__getattr__``, ``__getitem__``, ``__delitem__``, ``__delattr__``, ``pop``,
            ``popitem``, ``clear``, and ``update`` methods of the instance.
        """
        obj_logger.info('Hardening an instance of Obj...')
        if dict.__getattribute__(self, '_hardened') is True:
            obj_logger.info('Obj already hardened. Exiting.')
            return

        dict.__setattr__(self, '_hardened', True)

        def new_pop(key, default=...): raise ObjAttributeError(Obj.no_del_msg, name=key)

        def new_delattr(item=...): raise ObjAttributeError(Obj.no_del_msg, name=item)

        def new_clear(): raise ObjAttributeError(Obj.no_del_msg, name='ALL KEYS')

        def setting_msg(orig: str, new: str):
            return 'Setting self.__dict__[\'' + orig + '\'] to self.' + new + '...'

        def new_func_msg(func): return 'Should become:\n' + getsource(func)

        def override_func_safely(old_func_name: str, new_func: callable):
            obj_logger.trace(setting_msg(old_func_name, new_func.__name__))
            obj_logger.trace(new_func_msg(self._hardened_getattr))
            self.__dict__[old_func_name] = new_func
            obj_logger.trace(old_func_name + ' overridden.')

        obj_logger.debug('Replacing methods capable of mutating the class with'
                         ' new methods...')
        override_func_safely('__getattr__', self._hardened_getattr)
        override_func_safely('__getitem__', self._hardened_getitem)
        override_func_safely('__setattr__', self._hardened_setattr)
        override_func_safely('_setitem_to_be_disguised', self._hardened_setitem)
        override_func_safely('pop', new_pop)
        override_func_safely('__delattr__', new_delattr)
        override_func_safely('__delitem__', new_delattr)
        override_func_safely('popitem', new_delattr)
        override_func_safely('update', self._hardened_update)
        override_func_safely('clear', new_clear)
        obj_logger.debug('Methods replaced.')

        obj_logger.info('Checking for internal Objs to harden...')
        for val in self.values():
            if isinstance(val, Obj):
                obj_logger.debug('Found one...')
                val.harden()
                obj_logger.debug('Hardened internal Obj. Continuing to evaluate...')

        obj_logger.info('Done checking for internal Objs to harden.')
        obj_logger.info('Done hardening instance of Obj.')

    @logs_vars(obj_logger, 'self',
               start_message='Checking for keys that can no longer be changed, but for which a'
                             ' change is being attempted...',
               end_message='Finished checking for conflicting keys.',
               var_message_level='trace')
    def _scan_dead_keys(self, map_: Mapping):
        # The reason this is written to NOT fail fast is so that as much information as possible
        # about what was wrong can be collected. We want to have this information, so we can give
        # the user a detailed error message.
        bad_keys = []
        blocked_keys = []
        for key, val in map_.items():
            obj_logger.trace(f'Checking\n'
                             f'Key: {repr(key)}\n'
                             f'Value: {repr(val)}')
            if not dict.__contains__(self, key):
                obj_logger.trace('BAD KEY! Obj does not already contain key.')
                bad_keys.append(key)

            elif isinstance(t := dict.__getitem__(self, key), Obj):
                obj_logger.trace('Obj contains instance of Obj at key. Checking if safe...')
                if isinstance(val, dict):
                    obj_logger.trace('val is an instance of dict, should be used to update '
                                     ' internal Obj, checking internal Obj...')
                    _bad_keys, _blocked_keys = t._scan_dead_keys(val)
                    obj_logger.trace('adding any bad keys to existing bad keys...')
                    bad_keys.extend([str(key) + ':' + b_key for b_key in _bad_keys])
                    obj_logger.trace('adding any blocked keys to existing blocked keys...')
                    blocked_keys.extend([str(key) + ':' + b_key for b_key in _blocked_keys])

                else:
                    obj_logger.trace('BLOCKED KEY! val is not an instance of dict.')
                    blocked_keys.append(key)

        return bad_keys, blocked_keys

    def _raise_correct_errors(self, map_, extra_msg: str = ''):
        """
        When working on a hardened ``Obj``, there are multiple ways keys or values can be considered
        invalid. This just checks all of those when needed. It also handles checking nested Obj
        instances.

        :param map_: The ``Mapping`` to update with.
        :param extra_msg: Any message that should be appended to the default message if an error
            occurs.
        """
        bad_keys, blocked_keys = self._scan_dead_keys(map_)
        if len(bad_keys):
            if len(blocked_keys):
                msg = (Obj.no_new_msg + Obj.blocked_msg
                       + (' ' if extra_msg else '') + extra_msg)
                name1 = f'Missing Keys: {repr(bad_keys)}'
                name2 = f'Blocked Keys: {repr(blocked_keys)}'
                obj_logger.error(msg)
                obj_logger.error(name1)
                obj_logger.error(name2)
                raise ObjAttributeError(msg, name=name1 + '\n' + name2)

            else:
                msg = Obj.no_new_msg + (' ' if extra_msg else '') + extra_msg
                name = repr(bad_keys)
                obj_logger.error(msg)
                obj_logger.error(name)
                raise ObjAttributeError(msg, name=name)

        elif len(blocked_keys):
            msg = Obj.blocked_msg + (' ' if extra_msg else '') + extra_msg
            name = repr(blocked_keys)
            obj_logger.error(msg)
            obj_logger.error(name)
            raise ObjAttributeError(msg, name=name)

    @logs_vars(obj_logger, 'self',
               start_message='Performing update...',
               start_message_level='info',
               end_message='Update completed...',
               end_message_level='info')
    def _no_check_update(self, map_: Mapping):
        """
        This method simply updates the dictionary without a check for collisions or bad keys. On a
        hardened ``Obj``, it is to be used only all key-value pairs are verified to be safe to add.
        On an unhardened ``Obj``, it should be safe.
        """
        for key, val in map_.items():
            obj_logger.trace(f'Checking\n'
                             f'Key: {repr(key)}\n'
                             f'Value: {repr(val)}')
            if dict.__contains__(self, key):
                obj_logger.trace('Key exists. Checking if it should be replaced or updated...')
                if isinstance(val, dict):
                    obj_logger.trace('Val is an instance of dict. Checking whether to replace '
                                     ' original or update original...')
                    # We could build the Obj for the dict right away, but that isn't very efficient
                    # if we're going to be updating another Obj with it. Instead, check if there is
                    # an Obj to add it to first.
                    if isinstance(t := dict.__getitem__(self, key), Obj):
                        obj_logger.trace('Value at key is already an Obj. Updating it with val...')
                        t._no_check_update(val)

                    else:
                        obj_logger.trace('Value is not already an Obj. Replacing with new Obj '
                                         ' generated from val...')
                        dict.__setitem__(self, key, Obj(val))

                else:
                    obj_logger.trace('Val is not an instance of dict. Replacing with val...')
                    dict.__setitem__(self, key, val)

            elif isinstance(val, dict):
                obj_logger.trace('Key does not exist. Adding pair...')
                obj_logger.trace('Val is an instance of dict. Generating a new Obj and adding it '
                                 'at the key...')
                dict.__setitem__(self, key, Obj(val))

            else:
                obj_logger.trace('Key does not exist. Adding pair...')
                obj_logger.trace('Val is not an instance of dict. Adding val at key...')
                dict.__setitem__(self, key, val)

    @overload
    def update(self, **kwargs): ...

    @overload
    def update(self, iterable: Iterable, **kwargs): ...

    def update(self, map_: Mapping = ..., **kwargs):
        """
        This method updates the ``Obj`` much the same way that ``dict.update`` works. The major
        difference is that if a dictionary is set as the value for a key that already has an ``Obj``
        as its value, the dictionary will be used to update the existing ``Obj`` instead of
        replacing it.
        """
        map_ = {} if map_ is ... else map_
        map_ = dict(map_) if not isinstance(map_, Mapping) else map_
        map_.update(kwargs)
        self._no_check_update(map_)

    def _hardened_update(self, map_: Mapping = ..., **kwargs):
        map_ = {} if map_ is ... else map_
        map_ = dict(map_) if not isinstance(map_, Mapping) else map_
        map_.update(kwargs)

        self._raise_correct_errors(map_, ' Not even via update.')

        # Do not call dict.update here, it will cause any required dict->Obj conversions not to
        # occur. Any data in map_ should have been transferred to kwargs at the beginning of this.
        self._no_check_update(map_)

    ACTUALLY_ATTRIBUTE = 'Attribute in _HIDE_THESE. Proceeding to actually {} attribute...'

    @logs_vars(obj_logger, 'self',
               start_message='Getting attribute of Obj via unhardened method...',
               end_message='Attribute retrieved.')
    def __getattr__(self, item):
        # The following prevents *system* variables from effecting the
        # dictionary representation of the Obj.
        # Use the super's __getattribute__ method to prevent infinite loops and
        # to keep background data from being considered as elements in the
        # dictionary.
        if item in dict.__getattribute__(self, '_HIDE_THESE'):
            obj_logger.debug(Obj.ACTUALLY_ATTRIBUTE.format('get'))
            return dict.__getattribute__(self, item)

        if not dict.__contains__(self, item):
            obj_logger.debug('New attribute detected. Generating new Obj and adding...')
            value = Obj()
            dict.__setitem__(self, item, value)
            return value

        return dict.__getitem__(self, item)

    @logs_vars(obj_logger, 'self',
               start_message='Getting attribute of Obj via hardened method...',
               end_message='Finished getting.')
    def _hardened_getattr(self, item):
        # The following prevents *system* variables from effecting the
        # dictionary representation of the Obj.
        # Use the super's __getattribute__ method to prevent infinite loops
        # and to keep background data from being considered as elements in
        # the dictionary.
        if item in dict.__getattribute__(self, '_HIDE_THESE'):
            obj_logger.debug(Obj.ACTUALLY_ATTRIBUTE.format('get'))
            return dict.__getattribute__(self, item)

        if item not in self:
            msg = Obj._GEN_ERR.format('generate missing keys')
            name = repr(item)
            obj_logger.error(msg)
            obj_logger.error(name)
            raise ObjAttributeError(msg, name=name)

        return dict.__getitem__(self, item)

    @logs_vars(obj_logger, 'self',
               start_message='Setting attribute of Obj via unhardened method...',
               end_message='Attribute set.')
    def __setattr__(self, key, value):
        # The following prevents *system* variables from effecting the dictionary representation of
        # the Obj. Use the super's __getattribute__ and __setattr__ methods to prevent infinite
        # loops and to keep background data from being considered as elements in the dictionary.
        if key in dict.__getattribute__(self, '_HIDE_THESE'):
            obj_logger.debug(Obj.ACTUALLY_ATTRIBUTE.format('set'))
            dict.__setattr__(self, key, value)

        else:
            self._no_check_update({key: value})

    @logs_vars(obj_logger, 'self',
               start_message='Setting attribute of Obj via hardened method...',
               end_message='Finished setting.')
    def _hardened_setattr(self, key, value):
        # The following prevents *system* variables from effecting the dictionary representation of
        # the Obj.
        if key in dict.__getattribute__(self, '_HIDE_THESE'):
            obj_logger.debug(Obj.ACTUALLY_ATTRIBUTE.format('set'))
            dict.__setattr__(self, key, value)

        map_ = {key: value}
        self._raise_correct_errors(map_)
        self._no_check_update(map_)

    @logs_vars(obj_logger, 'self',
               start_message='Setting item of Obj via unhardened method...',
               end_message='Item set.')
    def _setitem_to_be_disguised(self, key, value):
        self._no_check_update({key: value})

    def __setitem__(self, key, value):
        self._setitem_to_be_disguised(key, value)

    @logs_vars(obj_logger, 'self',
               start_message='Setting item of Obj via hardened method...',
               end_message='Finished setting.')
    def _hardened_setitem(self, key, value):
        map_ = {key: value}
        self._raise_correct_errors(map_)
        self._no_check_update(map_)

    @logs_vars(obj_logger, 'self',
               start_message='Getting item of Obj via unhardened method...',
               end_message='Item retrieved.')
    def __getitem__(self, key):
        if key in self:
            return dict.__getitem__(self, key)

        obj_logger.debug('Attribute does not exist. Generating new Obj...')
        new_obj = Obj()
        dict.__setitem__(self, key, new_obj)
        return new_obj

    @logs_vars(obj_logger, 'self',
               start_message='Getting item of Obj via hardened method...',
               end_message='Finished getting.')
    def _hardened_getitem(self, item):
        if item not in self:
            msg = Obj._GEN_ERR.format('generate missing keys')
            name = repr(item)
            obj_logger.error(msg)
            obj_logger.error(name)
            raise ObjAttributeError(msg, name=name)

        return dict.__getitem__(self, item)

    @logs_vars(obj_logger, 'self',
               start_message='Deleting attribute via unhardened method...',
               end_message='Attribute deleted if it existed.')
    def __delattr__(self, item):
        if dict.__contains__(self, item):
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

        if recur in (list, tuple, dict):
            ans = recursive_conversion(recur, recur)

        elif type(recur) is tuple and recur[0] in (list, tuple, dict):
            ans = thing(recursive_conversion(recur[0], recur[1:] if len(recur[1:]) else ...))

        else:
            ans = dict.copy(self)

        if thing is dict:
            return ans

        return thing(ans.values())

    def as_list(self, recur: Union[type, Tuple[type]] = ...) -> list:
        """
        Generates a ``list`` of the values in an ``Obj``. These values should be in the expected
        order.

        :param recur: The type of conversion that should be used on internally-nested ``Objs``.
            Valid types for this are ``list``, ``tuple``, and ``dict``, and it can be specified
            either for the entire depth of the ``Obj`` or as a tuple of those types to be used for
            each depth. If it is not provided, nested ``Objs`` will be included as-is.

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

            **Example 1 -** No Recursive Re-formatting:

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

            **Example 2 -** Recur is a Type:

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

            **Example 3 -** Recur is a Tuple of Types (Longer than or Equal to the Max Depth of the
            Nesting):

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

            **Example 4 -** Recur is a Tuple of Types(Shorter than the Max Depth of the Nesting):

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
        Generates a ``tuple`` of the values in an ``Obj``. These values may or may not be in the
        expected order.

        :param recur: The type of conversion that should be used on internally-nested ``Objs``.
            Valid types for this are ``list``, ``tuple``, and ``dict``, and it can be specified
            either for the entire depth of the ``Obj`` or as a tuple of those types to be used for
            each depth. If it is not provided, nested ``Objs`` will be included as-is.

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

            **Example 1 -** No Recursive Re-formatting:

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

            **Example 2 -** Recur is a Type:

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

            **Example 3 -** Recur is a Tuple of Types (Longer than or Equal to the Max Depth of the
            Nesting):

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

            **Example 4 -** Recur is a Tuple of Types(Shorter than the Max Depth of the Nesting):

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
        Generates a ``dict`` of the key-value pairs in an ``Obj``. These pairs may or may not be in
        the expected order.

        :param recur: The type of conversion that should be used on internally-nested ``Objs``.
            Valid types for this are ``list``, ``tuple``, and ``dict``, and it can be specified
            either for the entire depth of the ``Obj`` or as a tuple of those types to be used for
            each depth. If it is not provided, nested ``Objs`` will be included as-is.

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

            **Example 1 -** No Recursive Re-formatting:

            .. code-block:: python

                ans = holder.as_dict()

            ans should be:

            .. code-block:: python

                {
                    'lorem': Obj({'ipsum': 5, 'dolor': 6, 'sit': 7}),
                    'amet': Obj({'consectetur': 1, 'adipiscing': 2,
                         'elit': Obj({'sed': 3, 'tempor': 4})}),
                    'sagittis': Obj({0: 55, 1: 56, 2: 57, 3: 58}),
                    543: 'mi'
                }

            **Example 2 -** Recur is a Type:

            .. code-block:: python

                ans = holder.as_dict(list)

            ans should be:

            .. code-block:: python

                {
                    'lorem': [5, 6, 7],
                    'amet': [1, 2, [3, 4]],
                    'sagittis': [55, 56, 57, 58],
                    543: 'mi'
                }

            **Example 3 -** Recur is a Tuple of Types (Longer than or Equal to the Max Depth of the
                Nesting):

            .. code-block:: python

                ans = holder.as_dict((dict, tuple))

            ans should be:

            .. code-block:: python

                {
                    'lorem': {'ipsum': 5, 'dolor': 6, 'sit': 7 },
                    'amet': {'consectetur': 1, 'adipiscing': 2, 'elit': (3, 4)},
                    'sagittis': {0: 55, 1: 56, 2: 57, 3: 58},
                    543: 'mi'
                }

            **Example 4 -** Recur is a Tuple of Types(Shorter than the Max Depth of the Nesting):

            .. code-block:: python

                ans = holder.as_dict((tuple,))

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

    def __repr__(self) -> str:
        return '(Obj) ' + dict.__repr__(self)
