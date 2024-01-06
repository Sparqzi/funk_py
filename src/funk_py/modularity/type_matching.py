import inspect
from types import FunctionType
from typing import Union, Any, AnyStr, Callable, Mapping, MutableMapping, \
    get_args, get_origin, Sequence, Literal, Tuple, List

from collections.abc import Iterable

from funk_py.modularity.basic_structures import simple_trinomial


IterableNonString = type('IterableNonString', (Iterable,), {'a': '1'})
_double_list_check = simple_trinomial(lambda x: isinstance(x, list))  # noqa
_double_dict_check = simple_trinomial(lambda x: isinstance(x, dict))  # noqa
_double_tuple_check = simple_trinomial(lambda x: isinstance(x, tuple))  # noqa
_double_func_check = simple_trinomial(lambda x: isinstance(x, FunctionType))  # noqa


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


DOUBLE_FAILED_RECURSION_MSG = \
    ('During the process of checking whether two {%s}s were equal, the'
     ' recursion limit was exceeded. An attempt was made to compare the {%s}s'
     ' in a different way, since it was assumed the {%s} or something inside'
     ' was self-containing. Unfortunately, it seems there were just too many'
     ' nested objects.')
UNKNOWN_RECURSION_MSG = ('Encountered a value which exhibits recursion, but is'
                         ' not a known recursive type. Failed to handle'
                         ' recursion.')


def rec_lists_checker(recursion_points1, recursion_points2):
    _rec_tester = simple_trinomial(lambda x, y: recursion_points1[y] is x,
                                   lambda x, y: recursion_points2[y] is x)

    # If you're not familiar with walrus operators, I advise you read up on
    # them...
    def rec_lists_check(v1, v2, func_if_missing):
        found = False
        for ji in range(len(recursion_points1)):
            if ti := _rec_tester(v1, v2, ji):
                found = True
                break

            elif ti is False:
                return False

        if not found:
            recursion_points1.append(v1)
            recursion_points2.append(v2)
            return func_if_missing

    def point_check(v1, v2):
        # ... is the "continue to next" result of functions here.
        t1 = _double_tuple_check(v1, v2) \
            if (t := _double_list_check(v1, v2)) is ... \
            else t

        if t1:
            t2 = rec_lists_check(v1, v2, _recursive_check_list_equality)

        elif t1 is ... and (t1 := _double_dict_check(v1, v2)):
            t2 = rec_lists_check(v1, v2, _recursive_check_dict_equality)

        elif t1 is ... and (t1 := _double_func_check(v1, v2)):
            t2 = rec_lists_check(v1, v2, _recursive_check_function_equality)

        elif t1 is False:
            return False

        else:
            return ...

        return t2

    return point_check


def _check_is_equality(obj1: Any, obj2: Any):
    if obj1 is None or obj2 is None or obj1 is ... or obj2 is ...:
        return obj1 is obj2

    t1, t2 = type(obj1), type(obj2)
    if t1 is bool or t2 is bool:
        return obj1 is obj2

    return ...


def _get_simple_argument_data(func: FunctionType) \
        -> Tuple[int, int, int, bool, bool]:
    signature = inspect.signature(func)
    arg_count = len(signature.parameters)
    pos_only_count = kw_only_count = 0
    var_arg = var_kwarg = False

    for name, parameter in signature.parameters.items():
        if parameter.kind is parameter.POSITIONAL_ONLY:
            pos_only_count += 1

        elif parameter.kind is parameter.KEYWORD_ONLY:
            kw_only_count += 1

        elif parameter.kind is parameter.VAR_POSITIONAL:
            var_arg = True

        elif parameter.kind is parameter.VAR_KEYWORD:
            var_kwarg = True

    return arg_count, pos_only_count, kw_only_count, var_arg, var_kwarg


def _get_argument_data(func: FunctionType) \
        -> Tuple[int, int, int, bool, bool, List[str], list, dict]:
    signature = inspect.signature(func)
    arg_count = len(signature.parameters)
    pos_only_count = kw_only_count = 0
    pos_defaults = []
    kw_defaults = {}
    var_arg = var_kwarg = False
    kw_names = []

    for name, parameter in signature.parameters.items():
        if parameter.kind is parameter.POSITIONAL_ONLY:
            pos_only_count += 1
            if parameter.default is not parameter.empty:
                pos_defaults.append(parameter.default)

        elif (parameter.kind is parameter.POSITIONAL_OR_KEYWORD
                and parameter.default is not parameter.empty):
            pos_defaults.append(parameter.default)

        elif parameter.kind is parameter.KEYWORD_ONLY:
            kw_only_count += 1
            kw_names.append(name)
            if parameter.default is not parameter.empty:
                kw_defaults[name] = parameter.default

        elif parameter.kind is parameter.VAR_POSITIONAL:
            var_arg = True

        elif parameter.kind is parameter.VAR_KEYWORD:
            var_kwarg = True

    return (arg_count, pos_only_count, kw_only_count, var_arg, var_kwarg,
            kw_names, pos_defaults, kw_defaults)


def hash_function(func: FunctionType):
    """
    This can *hash* a function insofar as its static image at the time of
    hashing. Since functions are technically mutable, it is heavily advised
    that use of this is avoided unless a function is truly going to be treated
    as immutable. This means:
        1 - **No attributes may be set on a function** after hashing.

        2 - The function **should not use *global* variables** that are
        **changed after hashing**.

        3 - The function should have **no internal constants which change**.

    This may or may not be used on decorated functions, depending on how the
    decorator works. lru_cache, for instance would break the hash, but something
    like @wraps will not necessarily break it.
    """
    return hash(sum(_get_simple_argument_data(func)))


def check_function_equality(func1: FunctionType, func2: Any):
    """
    Checks for equality of two functions. This equality is not standard
    equality, but is closer to how a human would interpret similarity of
    functions. It is intended to be location-agnostic as far as is possible,
    and is tested for functions nested within other functions, static methods in
    classes, and decorated functions. Keep in mind if the decorator for a
    function does not use *@wrapped*, it may not work as intended. **BEWARE:
    This does not care about the names of positional arguments at all.**
    """
    args1 = _get_argument_data(func1)
    args2 = _get_argument_data(func2)

    _code = func1.__code__
    o_code = func2.__code__

    return (o_code.co_code == _code.co_code
            and check_list_equality(o_code.co_consts, _code.co_consts)
            and o_code.co_nlocals == _code.co_nlocals
            and all(args1[i] == args2[i] for i in range(6))
            and check_list_equality(args1[6], args2[6])
            and check_dict_equality(args1[7], args2[7]))


def _recursive_check_function_equality(func1: FunctionType, func2: FunctionType,
                                       recursion_points1: list,
                                       recursion_points2: list):
    """
    *check_function_equality*, but for use when a likely self-containing object
    is contained within the constant pool or is a default value.
    """
    args1 = _get_argument_data(func1)
    args2 = _get_argument_data(func2)

    _code = func1.__code__
    o_code = func2.__code__
    return (o_code.co_code == _code.co_code
            and check_list_equality(o_code.co_consts, _code.co_consts)
            and o_code.co_nlocals == _code.co_nlocals
            and all(args1[i] == args2[i] for i in range(6))
            and _recursive_check_list_equality(args1[6], args2[6],
                                               recursion_points1,
                                               recursion_points2)
            and _recursive_check_dict_equality(args1[7], args2[7],
                                               recursion_points1,
                                               recursion_points2))


def check_list_equality(list1: Union[list, tuple], list2: Union[list, tuple]):
    try:
        return list1 == list2

    except RecursionError:
        try:
            return _recursive_check_list_equality(list1, list2, [], [])

        except RecursionError as e:
            fill = 'list' if type(list1) is list else 'tuple'
            raise RecursionError(DOUBLE_FAILED_RECURSION_MSG.format(fill), e)


def _recursive_check_list_equality(list1: Union[list, tuple],
                                   list2: Union[list, tuple],
                                   recursion_points1: list,
                                   recursion_points2: list,
                                   rec_lists_check: Callable = None):
    if rec_lists_check is None:
        rec_lists_check = rec_lists_checker(recursion_points1, recursion_points2)

    # If we get here, we shouldn't need to check list lengths or tuple.
    for i in range(len(list1)):
        val1 = list1[i]
        val2 = list2[i]
        try:
            if not (_check_is_equality(val1, val2)) or val1 != val2:
                return False

        except RecursionError as e:
            t1 = rec_lists_check(val1, val2)
            if ((t1 and not t1(val1, val2, recursion_points1,
                               recursion_points2, rec_lists_check))
                    or t1 is False):
                return False

            else:
                raise RecursionError(UNKNOWN_RECURSION_MSG, e)

    return True


def check_dict_equality(dict1: dict, dict2: dict):
    try:
        return dict1 == dict2

    except RecursionError:
        try:
            return _recursive_check_dict_equality(dict1, dict2, [], [])

        except RecursionError as e:
            raise RecursionError(DOUBLE_FAILED_RECURSION_MSG.format('dict'), e)


def _recursive_check_dict_equality(dict1: dict, dict2: dict,
                                   recursion_points1: list,
                                   recursion_points2: list,
                                   rec_lists_check: Callable = None):
    if rec_lists_check is None:
        rec_lists_check = rec_lists_checker(recursion_points1, recursion_points2)

    keys1 = list(dict1.keys())

    # If we get here, we shouldn't need to check dict lengths.
    for key in keys1:
        if key not in dict2:
            return False

        val1 = dict1[key]
        val2 = dict2[key]

        try:
            if not (_check_is_equality(val1, val2)) or val1 != val2:
                return False

        except RecursionError as e:
            t1 = rec_lists_check(val1, val2)
            if ((t1 and not t1(val1, val2, recursion_points1,
                               recursion_points2, rec_lists_check))
                    or t1 is False):
                return False

            else:
                raise RecursionError(UNKNOWN_RECURSION_MSG, e)

    return True


def thoroughly_check_equality(val1: Any, val2: Any):
    if t1 := _check_is_equality(val1, val2):
        return True

    elif t1 is ... and (t1 := _double_list_check):
        return check_list_equality(val1, val2)

    elif t1 is ... and (t1 := _double_tuple_check):
        return check_list_equality(val1, val2)

    elif t1 is ... and (t1 := _double_dict_check):
        return check_dict_equality(val1, val2)

    elif t1 is ... and (t1 := _double_func_check):
        return check_list_equality(val1, val2)

    elif t1 is False:
        return False

    return val1 == val2


