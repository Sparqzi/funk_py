import code
import inspect
from types import FunctionType
from typing import Union, Any, AnyStr, Callable, Mapping, MutableMapping, \
    get_args, get_origin, Sequence, Literal

from collections.abc import Iterable


IterableNonString = type('IterableNonString', (Iterable,), {'a': '1'})


def check_iterable_not_string(value: Any) -> bool:
    """Check if a value is iterable, but not a string."""
    return isinstance(value, Iterable) and type(value) is not str


class TypeMatcher:
    def __new__(cls, type_: Union[type, tuple, None]):
        if not hasattr(TypeMatcher, '_existing_matches'):
            TypeMatcher._existing_matches = {}

        if type_ in TypeMatcher._existing_matches:
            return TypeMatcher._existing_matches[type_]

        TypeMatcher._existing_matches[type_] = t = super().__new__(cls)
        t.__true_init(type_)
        return t

    # *DISREGARD python:S1144*
    # This might trigger a warning for python:S1144, that is because some
    # linters do not check the __new__ method properly. This does not violate
    # python:S1144.
    def __true_init(self, type_: Union[type, tuple, None]): # noqa
        # This serves as a hidden init so that instances are never
        # re-initialized. This is important to prevent eating up too much
        # memory. It can also decrease other resource usage.
        self._type = type_
        self._function = self.__get_new_function(type_)

    def __init__(self, type_: Union[type, tuple, None]):
        """Returns a TypeMatcher used to check a variable."""
        # This exists to ensure correct documentation appears in IDEs.
        pass

    def __call__(self, value: Any) -> bool:
        """Evaluate whether type of value is a match for this TypeMatcher."""
        return self._function(value)

    @staticmethod
    def __get_new_function(type_: Union[type, tuple, None]) -> Callable:
        """A class to represent a runtime type-check."""
        origin = get_origin(type_)
        if type_ is ... or isinstance(type_, type(...)):
            return lambda x: x is ...

        elif origin is Union:
            return TypeMatcher.__glorified_union_check(get_args(type_))

        elif origin is Literal:
            return TypeMatcher.__literal(get_args(type_))

        elif type_ is Any:
            return lambda x: True

        # Cannot import NoneType, but when used in Union, None becomes
        # NoneType. Therefore, must evaluate type_ against type(None)
        elif type_ is None or isinstance(type_, type(None)):
            return lambda x: x is None

        elif type_ is IterableNonString:
            return check_iterable_not_string

        elif type_ is AnyStr:
            return lambda x: isinstance(x, str)

        elif type_ in (str, int, float, bool, complex, object, Callable,
                       bytes):
            return TypeMatcher.__generic_type(type_)

        elif type(type_) is tuple:
            return TypeMatcher.__glorified_union_check(type_)

        elif origin in (list, set, Iterable, Sequence):
            return TypeMatcher.__generic_list(type_)

        elif origin in (dict, Mapping, MutableMapping):
            return TypeMatcher.__mapping_check(type_)

        elif origin is tuple:
            return TypeMatcher.__tuple_check(type_)

        else:
            return TypeMatcher.__generic_type(type_)

    @staticmethod
    def __generic_type(type_: type) -> Callable:
        """Check if a value matches a generic type."""
        def type_check(value: Any) -> bool:
            return type(value) is type_

        return type_check

    @staticmethod
    def __literal(options: tuple) -> Callable:
        """Get the function for checking a Literal."""
        check_list = list(options)

        def type_check(value: Any) -> bool:
            # need to check for True/False and 1/0
            if value in [0, 1]:
                # if not found in list, then definite False
                if value not in check_list:
                    return False

                # otherwise, check to ensure the value is ACTUALLY equal
                for val in check_list:
                    if val is value:
                        return True

                return False

            return value in check_list

        return type_check

    @staticmethod
    def __generic_list(type_: type) -> Callable:
        """Check if a value matches a generic sequence."""
        try:
            type_types = get_args(type_)
            type__ = get_origin(type_)

        except AttributeError:
            type_types = ()

        if len(type_types):
            checker = TypeMatcher(type_types)

            def type_check(value: Any) -> bool:
                if type(value) is type__:
                    for v in value:
                        if not checker(v):
                            return False

                    return True

                return False

        else:
            def type_check(value: Any) -> bool:
                return type(value) is type_

        return type_check

    @staticmethod
    def __glorified_union_check(type_: tuple) -> Callable:
        """Check if a value is in a union."""
        if type_[0] == 'instance':
            inst_check = True
            type_ = type_[1:]

        else:
            inst_check = False

        basic_check_list = [str, int, float, bool, complex, object, Callable]
        hard_check_list = [list, set, dict, Iterable, type(None), tuple, Union,
                           Literal]

        easy_checks = []
        hard_checks = []
        for t in type_:
            if t in basic_check_list:
                easy_checks.append(t)

            elif type(t) is tuple \
                    or t in hard_check_list \
                    or get_origin(t) in hard_check_list:
                hard_checks.append(TypeMatcher(t)._function)

            else:
                easy_checks.append(t)

        return TypeMatcher.__get_glorified_union_check_function(easy_checks,
                                                                hard_checks,
                                                                inst_check)

    @staticmethod
    def __get_glorified_union_check_function(easy_checks: list,
                                             hard_checks: list,
                                             inst_check: bool) -> Callable:
        """Actually construct the function for the __glorified_union_check"""
        if inst_check:
            def type_check(value: Any) -> bool:
                if any(isinstance(value, t) for t in easy_checks) or \
                        any(t(value) for t in hard_checks):
                    return True

                return False

        else:
            def type_check(value: Any) -> bool:
                if type(value) in easy_checks or \
                        any(t(value) for t in hard_checks):
                    return True

                return False

        return type_check

    @staticmethod
    def __tuple_check(type_: type) -> Callable:
        """Checks a tuple for matching types if needed."""
        if len(type_types := get_args(type_)):
            type__ = get_origin(type_)
            if repeat := (type_types[-1] is ...):
                type_types = type_types[:-1]

            checks = [TypeMatcher(t) for t in type_types]

            if repeat:
                return TypeMatcher.__get_tuple_check_repeat_function(checks,
                                                                     type__)

            return TypeMatcher.__get_tuple_check_args_function(checks, type__)

        def type_check(value: Any) -> bool:
            return type(value) is type_

        return type_check

    @staticmethod
    def __get_tuple_check_repeat_function(checks, type__) -> Callable:
        """Actually construct the function for a tuple with repeating types."""
        unit = len(checks)

        def type_check(value: Any) -> bool:
            if type(value) is type__:
                if len(value) % unit:
                    return False

                j = 0
                while j < len(value):
                    if not all(checks[i](value[i + j])
                               for i in range(unit)):
                        return False

                    j += unit

                return True

            return False

        return type_check

    @staticmethod
    def __get_tuple_check_args_function(checks, type__) -> Callable:
        """Actually construct the function for a tuple with non-repeating
        types."""
        def type_check(value: Any) -> bool:
            if type(value) is type__ and len(checks) == len(value):
                return all(checks[i](value[i])
                           for i
                           in range(len(value)))

            return False

        return type_check

    @staticmethod
    def __mapping_check(type_: type) -> Callable:
        """Check a mapping for matching types if needed."""
        if len(type_types := get_args(type_)):
            type__ = get_origin(type_)
            check_key = TypeMatcher(type_types[0])
            check_val = TypeMatcher(type_types[1])
            return TypeMatcher.__get_mapping_check_args_function(check_key,
                                                                 check_val,
                                                                 type__)

        def type_check(value: Any) -> bool:
            return type(value) is type_

        return type_check

    @staticmethod
    def __get_mapping_check_args_function(check_key, check_val, type__) \
            -> Callable:
        """Actually construct the function for a mppaing with args."""
        def type_check(value: Any) -> bool:
            if type(value) is type__:
                for key, val in value.items():
                    if not check_key(key) or not check_val(val):
                        return False

                return True

            return False

        return type_check

    def __repr__(self) -> str:
        return f'<TypeMatcher: {repr(self._type)}>'

    @property
    def type(self):
        """What type is the TypeMatcher checking for?"""
        return self._type


class TransformerFilter:
    def __init__(self,
                 input_rules: Union[dict, list],
                 raise_on_fail: bool = True):
        """A filter with rules and methods to transform values put through it
        based on their type."""
        self.__rules = []
        self.__outputs = []
        for type_, func in input_rules.items():
            self.__rules.append(TypeMatcher(type_))
            self.__outputs.append(func)

        self._default = ...
        self._length = len(self.__rules)
        self._raise_on_fail = raise_on_fail
        self.pun = {}
        self.pn = {}

    @classmethod
    def __from_existing(cls, rules: list, outputs: list,
                        raise_on_fail: bool):
        new_cls = cls.__new__(cls, [], blank=True)
        new_cls._accept_args(rules, outputs, raise_on_fail)
        return new_cls

    def _accept_args(self, rules: list, outputs: list, raise_on_fail: bool):
        """
        Used to set the args on an instance that was generated
        without a call to __init__.
        """
        self.__rules = rules
        self.__outputs = outputs
        self._default = ...
        self._length = len(rules)
        self._raise_on_fail = raise_on_fail
        self.pun = {}
        self.pn = {}

    def __call__(self, value: Any, *, inst: Any = None) -> Any:
        """Check the type of the value and perform a specified transformation
        on it based on predetermined instructions.

        :param value: The value to transform.
        :param inst: The class instance from which the method should be called
            (if applicable).
        :return: Returns the transformed value if a transformer is found.
            Should no transformer be found, and raise_on_fail is True, will
            raise a TypeError exception. Otherwise, will return ellipsis.
        """
        for i in range(self._length):
            if self.__rules[i](value):
                if type(func := self.__outputs[i]) is tuple:
                    call = func[0]
                    args = (value, *func[1:])
                    # must ensure self parameter is passed in if the function
                    # requires it.
                    if hasattr(inst, call.__name__) \
                            and inspect.ismethod(getattr(inst, call.__name__)):
                        return call(inst, *args)

                    return call(*args)

                # must ensure self parameter is passed in if the function
                # requires it.
                if hasattr(inst, func.__name__) \
                        and inspect.ismethod(getattr(inst, func.__name__)):
                    return func(inst, value)

                return func(value)

        if self._raise_on_fail:
            raise TypeError(f"{type(value)} is not a valid type for this"
                            f" attribute.")

        return ...

    def __repr__(self) -> str:
        dict_string = ', '.join(f"{repr(rule)}: {repr(out)}"
                                for rule, out
                                in zip(self.__rules, self.__outputs))
        return f"<TransformerFilter{'{'}{dict_string}{'}'}>"

    def __set_name__(self, owner, name):
        if owner in self.pun:
            # In this scenario, there is already a property in this owner. In
            # order to avoid overwriting the current name, we should create
            # a new class instance and assign that instance the owner/name
            # combo we have here.
            new = TransformerFilter.__from_existing(self.__rules,
                                                    self.__outputs,
                                                    self._raise_on_fail)
            new.__set_name__(owner, name)
            setattr(owner, name, new)

        else:
            # Go ahead and set the public name and the
            self.pun[owner] = name
            self.pn[owner] = '_    \\' + name

    def __get__(self, inst, owner):
        if inst.__class__ not in self.pn:
            for c in inst.__class__.mro():
                if c in self.pn:
                    self.pn[inst.__class__] = self.pn[c]
                    self.pun[inst.__class__] = self.pun[c]
                    break

        if hasattr(inst, self.pn[owner]):
            return getattr(inst, self.pn[owner])

        else:
            return ...

    def __set__(self, inst, value):
        if inst.__class__ not in self.pn:
            for c in inst.__class__.mro():
                if c in self.pn:
                    self.pn[inst.__class__] = self.pn[c]
                    self.pun[inst.__class__] = self.pun[c]
                    break

        inst.__setattr__(self.pn[inst.__class__], self(value, inst=inst))

    def copy(self) -> 'TransformerFilter':
        new = self.__from_existing(self.__rules, self.__outputs,
                                   self._raise_on_fail)
        return new


def hash_function(func: FunctionType):
    _code = func.__code__
    _hash = _code.co_nlocals
    _hash += _code.co_argcount
    _hash += _code.co_kwonlyargcount
    _hash += _code.co_posonlyargcount
    return _hash


def _get_kw_only_names(code_: code) -> set:
    if (t := code_.co_kwonlyargcount) > 0:
        return set(code_.co_names[-t:])

    return set()


def check_function_equality(func: FunctionType, o_func: FunctionType):
    _code = func.__code__
    p1 = _code.co_code
    p2 = _code.co_consts
    p3 = _code.co_argcount
    p4 = _code.co_kwonlyargcount
    p5 = _get_kw_only_names(_code)
    p6 = _code.co_nlocals
    p7 = _code.co_posonlyargcount
    if not callable(o_func):
        return False

    o_code = o_func.__code__
    return (o_code.co_code == p1 and o_code.co_consts == p2
            and o_code.co_argcount == p3 and o_code.co_kwonlyargcount == p4
            and _get_kw_only_names(o_code) == p5 and o_code.co_nlocals == p6
            and o_code.co_posonlyargcount == p7)
