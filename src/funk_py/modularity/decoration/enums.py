from collections import namedtuple
from enum import Enum
from functools import wraps
from inspect import signature as sgntr, Parameter
from typing import Type, Callable, Any, Mapping

from funk_py.modularity.type_matching import TypeMatcher as Tm


def converts_enums(func: Callable):
    """A decorator that will automatically convert enums fed to it into their values."""
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
                    if not hasattr(value, '_ignore_me'):
                        setattr(enum_class, key, t := metacls._create_func_(enum_class, value, key))
                        members[key] = t

                elif isinstance(value, classmethod):
                    if not hasattr(value, '_ignore_me'):
                        setattr(enum_class, key,
                                t := metacls._create_func_(enum_class, value, key))
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
        sm = isinstance(func, staticmethod)
        lm = '<lambda>' in func.__qualname__
        if cm := (type(func) is classmethod):
            setattr(cls, func.__name__ + '\\,,', func)
            func = getattr(cls, func.__name__ + '\\,,')
            sig = sgntr(func)

        else:
            sig = sgntr(func)

        first = True
        for name, parameter in sig.parameters.items():
            if first:
                first = False
                if not (sm | cm | lm):
                    continue

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

        if sm | cm | lm:
            def bind(self, *_args, **_kwargs):
                return sig.bind(*_args, **_kwargs), func(*_args, **_kwargs)

        else:
            def bind(self, *_args, **_kwargs):
                return sig.bind(self, *_args, **_kwargs), func(self, *_args, **_kwargs)

        @wraps(func)
        def __call__(self, *_args, **_kwargs):
            bound, result = bind(self, *_args, **_kwargs)
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

            # Check if the function call returned a dictionary, this should be used to update kwargs
            # if available.
            if isinstance(result, Mapping):
                _kwargs_.update(result)

            return cls(_ArgEnum(self.name, _args_, _kwargs_))

        return _FuncArgSpec(key, __call__)


def ignore(func: callable):
    """
    A decorator that can be used on functions inside a ``CarrierEnum`` to denote that they should
    not be used to create instances of the enum.
    """
    func._ignore_me = True
    return func


class CarrierEnum(metaclass=CarrierEnumMeta):
    """
    An *enumeration* type that supports automatic generation of enum members from both values
    and functions. Members can be defined traditionally with values, or dynamically through callable
    functions, which are converted into callable class instances. These instances can then generate
    further enum instances when called with arguments matching the signature of the function.

    Each member of the enum can be a traditional value, a function wrapped to return enum instances,
    or a dynamically generated instance representing function call results.

    When an element is a wrapped function, it need not return a result, as the default result will
    be a container class holding the arguments it is called with; however, if desiring to add extra
    values to these holder classes by doing computations with the inputs, the user may define logic
    inside the method. In the case they do so, the method should return a mapping of names to
    values, otherwise the result of the function will be ignored.

    .. note::

      Holder instances generated by wrapped functions will follow access rules similar to how the
      function signature works. In other words, if the function includes positional-only arguments,
      they will only be accessible by index. If they are positional-or-keyword arguments, they will
      be included both as accessible via index and via attribute. If they are keyword-only
      arguments, they will only be included as attributes on the generated instances.

    .. warning::

      Because type hints are assumed necessary for holder instances, checks will be performed on
      arguments to ensure they match teh expected types.

    Methods defined in the class can be ignored/not turned into elements by using the ``@ignore``
    decorator.

    Attributes:
        *value* (``Any``): The value of the enum member.
        *name* (``str``): The name of the enum member.

    **Usage:**

    Given a class defined as such...

    .. code-block:: python

        class MyEnum(CarrierEnum):
            def __init__(self, value):
                super().__init__(value)
                self.uses = 0

            PI = 3.14159

            POINT4D = lambda w, x, y, z: ...

            @staticmethod
            def POINT2D(x: int, y: int = 0): ...

            @staticmethod
            def POINT3D(x: int, /, y: int, *, z: int): ...

            @classmethod
            def PI_POINT3D(cls, x: int, y: int): return {'z': cls.PI.value}

            def CALC_POINT2D(i_self, x: int):
                i_self.uses += 1
                return {'y': i_self.uses * i_self.gen_random() * x}

            @ignore
            @staticmethod
            def gen_random():
                return 4  # chosen by fair dice roll.
                          # guaranteed to be random.

    Static Member Access Examples:

    .. code-block:: python

        print(MyEnum.PI)    # prints 3.14159
        print(MyEnum.PI())  # raises a TypeError
        print(MyEnum.PI[0]) # raises a TypeError
        print(MyEnum.PI.x)  # raises an AttributeError

    Functional Member Access Examples:

    .. code-block:: python

        # Simple Examples:
        # Default values will be used.
        point1 = MyEnum.POINT2D(42)
        print(point1.x)  # prints 42
        print(point1[0]) # prints 42
        print(point1.y)  # prints 0
        print(point1[1]) # prints 0

        # Filling the signature makes a difference.
        point2 = MyEnum.POINT2D(42, 55)
        print(point2.x)  # prints 42
        print(point2[0]) # prints 42
        print(point2.y)  # prints 55
        print(point2[1]) # prints 55

        # positional, positional-or-keyword, and keyword arguments are treated differently.
        point3 = MyEnum.POINT3D(53, 19, z=93)
        print(point3.x)   # raises an AttributeError
        print(point3[0])  # prints 53
        print(point3.y)   # prints 19
        print(point3[1])  # prints 19
        print(point3.z)   # prints 93
        print(point3[2])  # raises an IndexError

        # More-Complicated Examples:
        # Values returned by executing the wrapped method will be added to kwargs.
        # Class methods are also made to function normally when wrapped.
        point4 = MyEnum.PI_POINT3D(1, 2)
        print(point4.x)  # raises an AttributeError
        print(point4[0]) # prints 1
        print(point4.y)  # prints 2
        print(point4[1]) # prints 2
        print(point4.z)  # prints 3.14159
        print(point4[2]) # raises an IndexError

        # Values returned by executing the wrapped method will be added to kwargs.
        # Instance methods are also made to function normally when wrapped.
        point5 = MyEnum.CALC_POINT2D(14)
        print(point5.x)  # prints 14
        print(point5[0]) # prints 14
        print(point5.y)  # prints 56
        print(point5[1]) # raises an IndexError

        point6 = MyEnum.CALC_POINT2D(14)
        print(point6.x)  # prints 14
        print(point6[0]) # prints 14
        print(point6.y)  # prints 112
        print(point6[1]) # raises an IndexError

        # Lambdas are treated like static methods.
        point7 = MyEnum.POINT4D(5, 6, 7, 8)
        print(point7.w)  # prints 5
        print(point7[0]) # prints 5
        print(point7.x)  # prints 6
        print(point7[1]) # prints 6
        print(point7.y)  # prints 7
        print(point7[2]) # prints 7
        print(point7.z)  # prints 8
        print(point7[3]) # prints 8

        # ignore decorator should keep a function from being interpreted as an attribute.
        print(MyEnum.gen_random()) # prints 4
    """
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
        if not hasattr(self, '_call_') or self._call_ is None:
            raise TypeError(f'{repr(self.__class__.__name__)} object is not callable')

        return self._call_(self, *args, **kwargs)

    def __getitem__(self, index: int):
        if not hasattr(self, '_args') or self._args is None:
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
