from collections import namedtuple
from enum import Enum
from functools import wraps
from inspect import signature as sgntr, Parameter
from typing import Type, Callable, Any

from funk_py.modularity.type_matching import TypeMatcher as Tm


def converts_enums(func: Callable):
    sig = sgntr(func)
    # Determine which arguments should be enums in advance...
    converter_dict = {}
    for param_name, param in sig.parameters.items():
        param_type = param.annotation
        if isinstance(param_type, Type) and issubclass(param_type, Enum):
            converter_dict[param_name] = (param_type, {m.value: m for m in param_type})

    if not len(converter_dict):
        # Cover the case where - for whatever reason - someone used this to decorate a function with
        # no enumerable arguments. We don't want to introduce extra calculations that do nothing
        # (if we can avoid it reasonably).
        return func

    @wraps(func)
    def wrapper(*args, **kwargs):
        bound = sig.bind(*args, **kwargs)
        for param_name, _def in converter_dict.items():
            _type, converter = _def
            val = bound.arguments[param_name]
            if not isinstance(val, _type):
                bound.arguments[param_name] = converter.get(val, None)

        return func(*bound.args, **bound.kwargs)

    return wrapper


_SENTINEL = '_-`;\\7\'"4J'


_FuncArgSpec = namedtuple('_FuncArgSpec', ('name', 'func',))
_ArgEnum = namedtuple('_ArgEnum', ('name', 'args', 'kwargs'))


class CarrierEnumMeta(type):
    @staticmethod
    def __get_tm(parameter: Parameter):
        if parameter.annotation is parameter.empty:
            return Tm(Any)

        return Tm(parameter.annotation)

    def __new__(metacls, cls, bases, class_dict, **kwds):
        class_dict['_ignore_'] = ['_value_', 'value', 'name', '_name_', '_ignore_',
                                  '_valid_member_name_']
        ignore = class_dict['_ignore_']

        # create a default docstring if one has not been provided
        if '__doc__' not in class_dict:
            class_dict['__doc__'] = 'A carrier enumeration.'

        enum_members = dict(class_dict)
        for key in ignore:
            if key in enum_members:
                del enum_members[key]

        enum_class = super().__new__(metacls, cls, bases, class_dict, **kwds)
        members = {}

        for key, value in list(enum_members.items()):
            if not key.startswith('__') and key not in ('mro', ''):
                if callable(value):
                    setattr(enum_class, key, t := metacls._create_func_(enum_class, value, key))
                    members[key] = t

                else:
                    setattr(enum_class, key, t := metacls._create_value_(enum_class, value))
                    members[key] = t
                    t._name_ = key

        enum_class._norepeat_ = list(class_dict.keys())
        enum_class._members_ = members
        return enum_class

    @staticmethod
    def _create_func_(cls, func, key): return cls(CarrierEnumMeta.__modify_function(func, cls, key))

    @staticmethod
    def _create_value_(cls, value): return cls(value)

    @staticmethod
    def __modify_function(func: callable, cls, key: str) -> _FuncArgSpec:
        evals = {}     # Stores evaluators for arg values.
        args = []      # A list for arg names.
        vargs = None   # Defaults to None to represent there are no varargs.
        kwargs = []    # A list for kwarg names.
        vkwargs = None # Defaults to None to represent there are no varkwargs.

        # Deconstruct the signature of the function and populate evals, args, vargs, kwargs, and
        # vkwargs appropriately.
        sig = sgntr(func)
        for name, parameter in sig.parameters.items():
            evals[name] = CarrierEnumMeta.__get_tm(parameter)
            match parameter.kind:
                case parameter.POSITIONAL_ONLY:
                    args.append(name)

                case parameter.POSITIONAL_OR_KEYWORD:
                    args.append(name)
                    kwargs.append(name)

                case parameter.VAR_POSITIONAL:
                    vargs = name

                case parameter.KEYWORD_ONLY:
                    kwargs.append(name)

                case parameter.VAR_KEYWORD:
                    vkwargs = name

        if isinstance(func, staticmethod):
            def bind(self, *_args, **_kwargs):
                return sig.bind(*_args, **_kwargs)

        elif isinstance(func, classmethod):
            def bind(self, *_args, **_kwargs):
                return sig.bind(self.__class__, *_args, **_kwargs)

        else:
            def bind(self, *_args, **_kwargs):
                return sig.bind(self, *_args, **_kwargs)

        @wraps(func)
        def __call__(self, *_args, **_kwargs):
            bound = bind(self, *_args, **_kwargs)
            bound.apply_defaults()
            _args_ = []
            _kwargs_ = {}
            for name in args:
                _args_.append(bound.arguments[name])

            if vargs is not None:
                _args_.extend(bound.arguments[vargs])

            for name in kwargs:
                _kwargs_[name] = bound.arguments[name]

            if vkwargs is not None:
                _kwargs_.update(bound.arguments[vkwargs])

            return cls(_ArgEnum(self.name, _args_, _kwargs_))

        return _FuncArgSpec(key, __call__)


class CarrierEnum(metaclass=CarrierEnumMeta):
    def __new__(cls, value):
        cls_ = super().__new__(cls)
        if type(value) is _FuncArgSpec:
            cls_._value_ = value.name
            cls_._name_ = value.name
            return cls_

        elif type(value) is _ArgEnum:
            cls_._value_ = value.name

            def next_name() -> str:
                cls._members_[value.name]._pos_ += 1
                return f'{value.name}:{cls._members_[value.name]._pos_}'

            cls_._name_ = cls_._valid_member_name_(next_name)
            cls_._members_[cls_._name_] = cls_
            cls_._norepeat_.append(cls_._name_)
            return cls_

        cls_._value_ = value
        return cls_

    def __init__(self, value):
        self._call_ = None
        self._args = None
        if type(value) is _FuncArgSpec:
            self._value_ = self.name
            self._call_ = value.func
            self._pos_ = 0

        elif type(value) is _ArgEnum:
            self._args = value.args
            for _name, value in value.kwargs.items():
                setattr(self, _name, value)

    def __call__(self, *args, **kwargs) -> 'CarrierEnum':
        if self._call_ is None:
            raise TypeError(f'{repr(self.__class__.__name__)} object is not callable')

        return self._call_(self, *args, **kwargs)

    def __getitem__(self, index: int):
        if self._args is None:
            raise TypeError(f'{repr(self.__class__.__name__)} object is not subscriptable')

        return self._args[index]

    @classmethod
    def _valid_member_name_(cls, new_name: str | Callable[[], str]) -> str:
        if callable(new_name):
            while (name := new_name()) in cls._norepeat_: ...
            return name

        elif new_name in cls._norepeat_:
            raise AttributeError(f'Cannot reassign members. Attempted to reassign {new_name}.')

        return new_name

    @property
    def value(self): return self._value_

    @property
    def name(self): return self._name_
