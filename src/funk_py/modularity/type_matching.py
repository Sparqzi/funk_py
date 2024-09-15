import inspect
import sys
from types import FunctionType
from typing import (Union, Any, AnyStr, get_args, get_origin, Literal, Tuple, List, Dict, TypeVar,
                    Generic)

if sys.version_info >= (3, 10):
    from types import UnionType

else:
    UnionType = object

from collections.abc import Iterable, Mapping, MutableMapping, Sequence, Callable

from funk_py.modularity.basic_structures import simple_trinomial
from funk_py.modularity.logging import make_logger


T = TypeVar('T')


_WEIRDOS = (None, ..., True, False)

IterableNonString = type('IterableNonString', (Iterable,), {'a': '1'})
_double_list_check = simple_trinomial(lambda x: isinstance(x, list))  # noqa
_double_dict_check = simple_trinomial(lambda x: isinstance(x, dict))  # noqa
_double_tuple_check = simple_trinomial(lambda x: isinstance(x, tuple))  # noqa
_double_func_check = simple_trinomial(lambda x: isinstance(x, FunctionType))  # noqa


def check_iterable_not_string(value: Any) -> bool:
    """Check if a value is iterable, but not a string."""
    return isinstance(value, Iterable) and not (isinstance(value, str) or isinstance(value, bytes))


tm_logger = make_logger('TypeMatcher', 'TYPEMATCHER_LOG_LEVEL', default_level='error', TRACE=5)


class TypeMatcher(Generic[T]):
    G_CHECK = 'Generating check...'
    R_G_CHECK = 'Returning generated check.'

    def _base_eval(self, type_: type) -> callable:
        msg = f'Checking if {{}} is {self._spec_msg}{type_}. Returning result.'

        def t(value: Any) -> bool:
            tm_logger.trace(msg.format(value))
            return isinstance(value, type_)

        return t

    @staticmethod
    def __any_check(value: Any) -> bool: return True

    def __new__(cls, type_: Union[type, tuple, UnionType, None]):
        tm_logger.info(f'Getting a new TypeMatcher for {type_}...')
        if not hasattr(TypeMatcher, '_TypeMatcher__existing_matches'):
            tm_logger.debug('TypeMatcher does not already have an __existing_matches collection. '
                            'Adding one...')
            TypeMatcher.__existing_matches = {}

        if type_ in TypeMatcher.__existing_matches:
            tm_logger.debug(f'TypeMatcher already exists for {type_}.')
            tm_logger.info('Returning existing instance.')
            return TypeMatcher.__existing_matches[type_]

        tm_logger.debug(f'TypeMatcher does not already exist for {type_}. Generating a new '
                        f'instance and adding it to existing matches...')
        TypeMatcher.__existing_matches[type_] = t = super().__new__(cls)
        tm_logger.debug('Initializing instance...')
        t.__true_init(type_)
        tm_logger.info('Returning new instance.')
        return t

    # *DISREGARD python:S1144*
    # This might trigger a warning for python:S1144, that is because some linters do not check the
    # __new__ method properly. This does not violate python:S1144.
    def __true_init(self, type_: Union[type, tuple, UnionType, None]):  # noqa
        """
        This serves as a hidden init so that instances are never re-initialized. This is important
        to prevent eating up too much memory when a user wants MANY instances of ``TypeMatcher``. It
        can also decrease other resource usage.
        """
        self._type = type_
        self._spec_msg = 'an instance of '
        self._p_spec_msg = 'instances of '
        self._function = self._get_new_function(type_)

    def __init__(self, type_: Union[type, tuple, UnionType, None]):
        """
        A ``TypeMatcher`` used to check whether a variable is a specific type. Instances of this
        class are callable, and can be called with a value to return a boolean representing whether
        the value is the type of the ``TypeMatcher``. The class itself can be used as a parametrized
        type hint for plugging into instances of itself.

        .. warning::
          This class makes a distinction between booleans and integers, which is not standard, but
          in several cases is more logical behavior.

        .. note::
          In Python 3.9 and lower, ``TypeMatcher`` cannot handle ellipsis as the parameter when used
          as a parametrized type hint.
        """
        # This exists to ensure correct documentation appears in IDEs.
        pass

    def __call__(self, value: Any) -> bool:
        """Evaluate whether type of value is a match for this TypeMatcher."""
        return self._function(value)

    def _get_new_function(self, type_: Union[type, tuple, None]) -> Callable:
        """A class to represent a runtime type-check."""
        tm_logger.info('Generating a unique function for a new TypeMatcher...')
        tm_logger.debug(f'Type is {type_}.')

        # The origin of a type is essentially used for figuring out if it's one of the parametrized
        # types.
        tm_logger.debug('Getting the origin of the type...')
        origin = get_origin(type_)
        tm_logger.debug(f'Got origin of type. {origin}.')
        if type_ is ... or isinstance(type_, type(...)):
            # Ellipsis is a singleton.
            tm_logger.debug('Type is ellipsis. Returning ellipsis type check.')
            return lambda x: x is ...

        elif origin in (TypeMatcher, StrictTypeMatcher):
            tm_logger.debug('Type is TypeMatcher or StrictTypeMatcher. Returning TypeMatcher type '
                            'check.')
            return self.__type_matcher_check(type_)

        elif origin is Union:
            tm_logger.debug('Type is a union. Generating and returning a union type check.')
            return self.__glorified_union_check(get_args(type_))

        elif origin is Literal:
            tm_logger.debug('Type is a literal. Generating and returning a literal type check.')
            return self.__literal(get_args(type_))

        elif type_ is Any:
            # The simplest case, technically.
            tm_logger.debug('Type is Any. Returning any type check.')
            return self.__any_check

        # Cannot import NoneType, but when used in Union, None becomes NoneType. Therefore, must
        # evaluate type_ against type(None).
        # Since TypeMatcher will recursively generate instances to handle things like Union, this is
        # necessary.
        elif type_ is None or isinstance(type_, type(None)):
            tm_logger.debug('Type is None/NoneType. Returning none type check.')
            return lambda x: x is None

        elif type_ is IterableNonString:
            tm_logger.debug('Type is IterableNonString. Returning iterable non-string type check.')
            return check_iterable_not_string

        elif type_ is AnyStr:
            tm_logger.debug('Type is AnyStr. Returning AnyStr type check.')
            return lambda x: isinstance(x, str) or isinstance(x, bytes)

        elif type_ is callable or origin in (callable, Callable):
            tm_logger.debug('Type is callable. Generating and returning a callable type check.')
            return self.__callable_check(type_)

        elif type(type_) is tuple:
            tm_logger.debug('Type is an actual tuple. Generating and returning a type check based '
                            'on its contents.')
            return self.__glorified_union_check(type_)

        # Don't just test for origin. Also check for subclasses to allow any non-built-in classes
        # to be treated as their base classes would be. The inner-workings of __mapping_check should
        # handle making sure the non-built-in class must be the parent.
        elif (origin in (Dict, dict, Mapping, MutableMapping) or (inspect.isclass(origin)
              and issubclass(origin, (Dict, dict, Mapping, MutableMapping)))):
            tm_logger.debug('Type is dictionary or mapping. Generating and returning a mapping '
                            'type check.')
            return self.__mapping_check(type_)

        # Don't just test for origin. Also check for subclasses to allow any non-built-in classes
        # to be treated as their base classes would be. The inner-workings of __tuple_check should
        # handle making sure the non-built-in class must be the parent.
        elif origin is tuple or (inspect.isclass(origin) and issubclass(origin, tuple)):
            tm_logger.debug('Type is tuple. Generating and returning a tuple type check.')
            return self.__tuple_check(type_)

        # Don't just test for origin. Also check for subclasses to allow any non-built-in classes
        # to be treated as their base classes would be. The inner-workings of __generic_list should
        # handle making sure the non-built-in class must be the parent.
        elif (origin in (list, set, Iterable, Sequence) or (inspect.isclass(origin)
              and issubclass(origin, (list, set, Iterable, Sequence)))):
            tm_logger.debug('Type is an iterable or sequence. Generating and returning appropriate '
                            'type check.')
            return self.__generic_list(type_)

        # If no matches are found before this, it's fairly certain the value is a simple type.
        tm_logger.debug('Type does not appear to be a special type. Generating and returning a '
                        'generic type check.')
        return self.__generic_type(type_)

    def __generic_type(self, type_: type) -> callable:
        """Check if a value matches a generic type."""
        tm_logger.debug('Generating base type check...')
        base_eval = self._base_eval(type_)
        tm_logger.debug('Base type check generated.')

        # Booleans can be mistaken for integers, by default, TypeMatchers should not make this
        # mistake, so a special function with an extra check is used when the target type is
        # integer.
        if type_ is int:
            tm_logger.debug('Type is int. Generating a special check to avoid confusing '
                            'booleans...')
            def type_check(value: Any) -> bool:
                tm_logger.trace(f'Checking if {value} is an instance of int and verifying that it '
                                f'is not a bool. Returning result.')
                return isinstance(value, int) and type(value) is not bool

            tm_logger.debug(TypeMatcher.R_G_CHECK)
            return type_check

        # Not a boolean so nothing fancy needs to happen.
        return base_eval

    @staticmethod
    def __literal(options: tuple) -> callable:
        """Get the function for checking a Literal."""
        tm_logger.debug(TypeMatcher.G_CHECK)
        valid_opts = f'valid options: {options}'
        def type_check(value: Any) -> bool:
            tm_logger.trace('Checking a literal type...')
            tm_logger.trace(valid_opts)
            # need to check for True/False and 1/0
            if value in [0, 1]:
                tm_logger.trace(f'value == {value}, which could mean it is a boolean or an int (or '
                                f'a float). Evaluating more carefully...')
                # if not found in list, then definite False
                if value not in options:
                    tm_logger.trace(f'{value} is not in the literal checker, returning False.')
                    return False

                # otherwise, check to ensure the value is ACTUALLY equal
                tm_logger.trace(f'{value} is in the literal checker. Verifying value actually is a '
                                f'match.')
                for val in options:
                    if val is value:
                        tm_logger.trace('Match found. Returning True.')
                        return True

                tm_logger.trace('Match not found. Returning False.')
                return False

            tm_logger.trace(f'{value} cannot be a boolean. Checking if it is in literal and '
                            f'returning result.')
            return value in options

        tm_logger.debug(TypeMatcher.R_G_CHECK)
        return type_check

    def __generic_list(self, type_: type) -> callable:
        """Check if a value matches a generic sequence."""
        tm_logger.debug(f'Getting the origin of {type_}...')
        type__ = get_origin(type_)
        tm_logger.debug(f'Origin retrieved. {type__}.')
        tm_logger.debug('Generating base type check...')
        base_eval = self._base_eval(type__)
        tm_logger.debug('Base type check generated.')
        tm_logger.debug('Checking if type has args...')
        type_types = get_args(type_)

        if len(type_types):
            tm_logger.debug(f'It does. args = {type_types}')
            tt = type_types[0]
            tm_logger.debug(f'Retrieving a TypeMatcher for {tt}...')
            # When there is an internal type, generate a TypeMatcher for it and a function to use
            # it.
            checker = self.__class__(tt)
            tm_logger.debug('Retrieved TypeMatcher.')

            tm_logger.debug(TypeMatcher.G_CHECK)
            cl_msg = f'Checking if {{}} is {self._spec_msg}{type_}...'
            gb_msg = (f'{{}} is {self._spec_msg}{type__}. Proceeding to check if all elements '
                      f'are instances of {tt}...')
            bb_msg = f'{{}} is not even {self._spec_msg}{type__}. Returning False.'
            b_el_msg = f'{{}} is not {self._spec_msg}{tt}. Returning False.'
            g_msg = f'All elements are {self._p_spec_msg}{tt}. Returning True.'

            def type_check(value: Any) -> bool:
                tm_logger.trace(cl_msg.format(value))
                if base_eval(value):
                    tm_logger.trace(gb_msg.format(value))
                    for v in value:
                        if not checker(v):
                            tm_logger.trace(b_el_msg.format(v))
                            return False

                    tm_logger.trace(g_msg)
                    return True

                tm_logger.trace(bb_msg.format(value))
                return False

            tm_logger.debug(TypeMatcher.R_G_CHECK)
            return type_check

        # When isn't an internal type, it's a very simple check for correct instance.
        tm_logger.debug('It does not.')
        tm_logger.debug(TypeMatcher.R_G_CHECK)
        return base_eval

    @staticmethod
    def __is_callable(value: Any) -> bool:
        tm_logger.trace(f'Checking if {value} is callable and returning result.')
        return callable(value)

    @staticmethod
    def __callable_check(type_: type) -> callable:
        tm_logger.debug('Checking if type has args...')

        if len(type_types := get_args(type_)):
            tm_logger.debug(f'It does. args = {type_types}')
            tm_logger.debug('Retrieving the expected output type...')
            t = type_types[1]
            tm_logger.debug(f'Expected output type is {t}.')

            tm_logger.debug('Generating a checker for the output type...')
            def checker_out(value: Any) -> bool:
                if value is None or isinstance(value, type(None)):
                    tm_logger.trace('Output type of function is None. Checking if expected that as '
                                    'a result...')
                    ans = t is type(None)

                    tm_logger.trace(f"It does{'' if ans else ' not'}.")
                    return ans

                tm_logger.trace('Output type is neither empty nor None. Checking if it is the '
                                'expected type.')
                return t is value or (inspect.isclass(value) and issubclass(value, t))

            tm_logger.debug('Generated output checker.')

            if type_types[0] is ...:
                # If signature is unneeded, that's great. It makes checking easier.
                tm_logger.debug('Any parameters are valid for input...')
                if t is Any:
                    # Even better if return type isn't specified.
                    tm_logger.debug('Any callable type is valid for output...')
                    tm_logger.debug('Returning generic callable check.')
                    return TypeMatcher.__is_callable

                tm_logger.debug(TypeMatcher.G_CHECK)

                def type_check(value: Any) -> bool:
                    tm_logger.trace(f'Checking if {value} is callable and has correct return type '
                                    f'then returning result.')
                    return (callable(value)
                            and checker_out(inspect.signature(value).return_annotation))

                tm_logger.debug(TypeMatcher.R_G_CHECK)
                return type_check

            tm_logger.debug('Specific parameter types are valid for input. Determining parameter '
                            'types...')
            # Aggregate the checkers for parameter types.
            checker_in = []
            for type_arg in type_types[0]:
                checker_in.append(TypeMatcher.__genuine_type_check(type_arg))

            tm_logger.debug('Parameter type checkers have been generated.')
            tm_logger.debug(f'Value: {checker_in}')

            tm_logger.debug(TypeMatcher.G_CHECK)
            t_str = str(type_)
            check_msg1 = f'Checking if {{}} parameters match callable of form {t_str}.'

            def _type_check(value: Any) -> bool:
                tm_logger.trace(check_msg1.format(value))
                if (not callable(value)
                        or len((sig := inspect.signature(value)).parameters) != len(checker_in)):
                    tm_logger.trace(f'{value} is either not callable or does not have the right'
                                    f'number of parameters. Returning False.')
                    return False

                tm_logger.trace(f'{value} is both callable and has the correct number of '
                                f'parameters. Verifying that parameters match.')
                params = [p for _, p in sig.parameters.items()]
                for check, name, p in zip(checker_in, type_types[0], params):
                    if p.kind in (inspect.Parameter.KEYWORD_ONLY, inspect.Parameter.VAR_KEYWORD,
                                  inspect.Parameter.VAR_POSITIONAL):
                        # Keyword-only arguments and var-args/kwargs cannot be represented in
                        # callable type annotations.
                        tm_logger.trace(f'There is a keyword-only, vararg, or varkwarg parameter '
                                        f'in the callable. The callable does not match the '
                                        f'signature {t_str}. Returning False.')
                        return False

                    elif not check(p.annotation):
                        tm_logger.trace(f"A parameter's type did not match the expected type. "
                                        f"Returning False.\n"
                                        f"Parameter Type: {p.annotation}\n"
                                        f"Expected Type: {name}")
                        return False

                tm_logger.trace('Successfully matched. Returning True.')
                return True

            tm_logger.debug('Check generated.')

            tm_logger.debug('Checking if a return type is specified...')
            if type_types[1] is Any:
                # No return type is specified, don't need to check that part.
                tm_logger.debug('Return type is not specified. Returning generated check.')
                return _type_check

            tm_logger.debug('Return type is specified. Generating check...')
            check_msg2 = f'Checking if {{}} matches callable of form {t_str}.'

            def type_check(value: Any) -> bool:
                tm_logger.trace(check_msg2.format(value))
                if not _type_check(value):
                    tm_logger.trace('Input parameters for do not match the correct signature. '
                                    'Returning False.')
                    return False

                tm_logger.trace('Input parameters for value match the correct signature. '
                                'Determining if return type matches and returning result.')
                ans = checker_out(inspect.signature(value).return_annotation)
                tm_logger.trace(f'Returning {ans}.')
                return ans

            tm_logger.debug(TypeMatcher.R_G_CHECK)
            return type_check

        tm_logger.debug('It does not.')
        tm_logger.debug('Returning generic callable check.')
        return TypeMatcher.__is_callable

    @staticmethod
    def __genuine_type_check(type_: type) -> callable:
        if type_ is inspect.Parameter.empty or type_ is Any:
            tm_logger.debug('Type is empty or Any. Using Any check.')
            return TypeMatcher.__any_check

        tm_logger.debug('Type is not empty or Any.')
        tm_logger.debug(TypeMatcher.G_CHECK)

        def type_check(value: Any) -> bool:
            return value is type_ or (inspect.isclass(value) and issubclass(value, type_))

        tm_logger.debug(TypeMatcher.R_G_CHECK)
        return type_check

    def __glorified_union_check(self, type_: tuple) -> callable:
        """Check if a value is in a union."""
        tm_logger.debug('Checking if Any happens to be in type_...')
        if Any in type_:
            tm_logger.debug('Any is one of the specified types. Expression is equivalent to Any. '
                            'Returning any type check.')
            return TypeMatcher.__any_check

        tm_logger.debug(f'Any is not in type_. Creating a check for each type in {type_}...')
        checks = [self.__class__(t) for t in type_]
        tm_logger.debug(TypeMatcher.G_CHECK)

        def type_check(value: Any) -> bool:
            tm_logger.trace(f'Checking if {value} is one of multiple types and returning result.')
            return any(check(value) for check in checks)

        tm_logger.debug(TypeMatcher.R_G_CHECK)
        return type_check

    def __tuple_check(self, type_: type) -> callable:
        """Checks a tuple for matching types if needed."""
        tm_logger.debug('There are args within the given tuple. Retrieving origin...')
        type__ = get_origin(type_)
        tm_logger.debug(f'Origin is {type__}.')
        tm_logger.debug('Generating base type check...')
        base_eval = self._base_eval(type__)
        tm_logger.debug('Base type check generated.')
        if len(type_types := get_args(type_)):
            if repeat := (type_types[-1] is ...):
                type_types = type_types[:-1]

            tm_logger.debug('Getting checkers for all types in args...')
            # Use class of self to ensure TypeMatchers generated match what the user expects.
            checks = [self.__class__(t) for t in type_types]
            tm_logger.debug(f'Checks generated: {checks}')

            if repeat:
                tm_logger.debug('The last value is ellipsis. Types may repeat.')
                tm_logger.debug('Generating and returning a check function for repeating tuple '
                                'type.')
                return self.__get_tuple_check_repeat_function(checks, type__, base_eval)

            tm_logger.debug('The last value is not ellipsis. Types cannot repeat.')
            tm_logger.debug('Generating and returning a check function for non-repeating tuple '
                            'type.')
            return self.__get_tuple_check_args_function(checks, type__, base_eval)

        tm_logger.debug('There are no args within the given tuple.')
        if sys.version_info >= (3, 9):
            # Cover the special case for a zero-length tuple. It is important to note that such a
            # case can only be determined via an equality check. Not valid for Python 3.8.
            if type_ == tuple[()]:
                tm_logger.debug('The given tuple compares equal to tuple[()].')
                tm_logger.debug(TypeMatcher.G_CHECK)

                def type_check(value: Any) -> bool:
                    tm_logger.trace(f'Checking if {value} is a zero-length tuple and returning'
                                    f' result.')
                    return isinstance(value, type__) and len(value) == 0

                tm_logger.debug(TypeMatcher.R_G_CHECK)
                return type_check

        tm_logger.debug(TypeMatcher.R_G_CHECK)
        return base_eval

    @staticmethod
    def __get_tuple_check_repeat_function(checks, type__, base_eval) -> callable:
        """Actually construct the function for a tuple with repeating types."""
        unit = len(checks)
        tm_logger.debug(f'Determined number of values in tuple should be evenly divisible by '
                        f'{unit}.')
        tm_logger.debug(TypeMatcher.G_CHECK)
        # Generate the error messages outside the method being returned to avoid having them as
        # overhead each time the method is called.
        # Do not put the raw parameterized type in the log event below. Python 3.8 does not like
        # it when it encounters type.
        main_msg = f'Checking if {{}} is of type {type__}[{checks}]...'
        t_match_msg = f'Type of value is aligned with {type__}.'
        t_n_match_msg = f'Type of value is not aligned with {type__}. Returning False.'
        b_len_msg = f'The length of the value is not evenly divisible by {unit}. Returning False.'
        p_checks_msg = (f'The length of the value is evenly divisible by {unit}. Checking each '
                        f'segment to make sure it matches the pattern '
                        f'{[t.type for t in checks]}...')
        n_match_msg = (f'Portion of tuple does not match pattern. {{}} does not match '
                       f'{[t.type for t in checks]}. Returning False.')

        def type_check(value: Any) -> bool:
            tm_logger.trace(main_msg.format(value))
            if base_eval(value):
                tm_logger.trace(t_match_msg)
                if len(value) % unit:
                    tm_logger.trace(b_len_msg)
                    return False

                tm_logger.trace(p_checks_msg)
                j = 0
                k = 1
                while j < len(value):
                    if not all(checks[i](value[i + j]) for i in range(unit)):
                        tm_logger.trace(n_match_msg.format(value[j:j + unit]))
                        return False

                    tm_logger.trace(f'Segment {k} matches.')
                    j += unit
                    k += 1

                tm_logger.trace('All segments match. Returning True.')
                return True

            tm_logger.trace(t_n_match_msg)
            return False

        tm_logger.debug(TypeMatcher.R_G_CHECK)
        return type_check

    @staticmethod
    def __get_tuple_check_args_function(checks, type__, base_eval) -> callable:
        """Actually construct the function for a tuple with non-repeating types."""
        tm_logger.debug(TypeMatcher.G_CHECK)
        main_msg = f'Checking if {{}} is of type {type__}[{checks}]...'

        def type_check(value: Any) -> bool:
            tm_logger.trace(main_msg.format(value))
            if base_eval(value) and len(checks) == len(value):
                tm_logger.trace('Value is correct general type and has correct length. Checking if '
                                'all values within match expected types and returning result.')
                return all(checks[i](value[i]) for i in range(len(value)))

            tm_logger.trace('Value is either not the correct general type or is not the correct '
                            'length. Returning False.')
            return False

        tm_logger.debug(TypeMatcher.R_G_CHECK)
        return type_check

    def __mapping_check(self, type_: type) -> callable:
        """Check a mapping for matching types if needed."""
        tm_logger.debug(f'Getting the origin of {type_}...')
        type__ = get_origin(type_)
        tm_logger.debug(f'Origin retrieved. {type__}.')
        tm_logger.debug('Generating base type check...')
        base_eval = self._base_eval(type__)
        tm_logger.debug('Base type check generated.')

        if len(type_types := get_args(type_)):
            tm_logger.debug(f'Type has args: {type_types}')
            # Use class of self to ensure TypeMatchers generated match what the user expects.
            check_key = self.__class__(type_types[0])
            tm_logger.debug(f'Key checker generated: {check_key}')
            # Use class of self to ensure TypeMatchers generated match what the user expects.
            check_val = self.__class__(type_types[1])
            tm_logger.debug(f'Value checker generated: {check_val}')
            tm_logger.debug(TypeMatcher.G_CHECK)
            # Do not put the raw parameterized type in the log event below. Python 3.8 does not like
            # it when it encounters ABCMeta classes.
            main_msg = f'Checking if {{value}} is an instance of {type__}[{type_types}].'
            i_type_msg = (f'Value is an instance of {type__}. Checking if all key-val pairs match '
                          f'the expected typing {check_key}: {check_val}.')
            n_type_msg = f'Value is not {self._spec_msg}{type__}. Returning False.'
            b_pair_msg = (f'Pair {{key}}: {{value}} does not match type {check_key}: {check_val}. '
                          f'Returning False.')

            def type_check(value: Any) -> bool:
                tm_logger.trace(main_msg.format(value=value))
                if base_eval(value):
                    tm_logger.trace(i_type_msg)
                    for key, val in value.items():
                        if not check_key(key) or not check_val(val):
                            tm_logger.trace(b_pair_msg.format(key=key, value=val))
                            return False

                    tm_logger.trace('All pairs match expected type. Returning True.')
                    return True

                tm_logger.trace(n_type_msg)
                return False

            tm_logger.debug(TypeMatcher.R_G_CHECK)
            return type_check

        tm_logger.debug(TypeMatcher.R_G_CHECK)
        return base_eval

    def __type_matcher_check(self, type_: type) -> callable:
        """Check a ``TypeMatcher`` for correct type if needed."""
        tm_logger.debug(f'Getting the origin of {type_}...')
        type__ = get_origin(type_)
        tm_logger.debug(f'Origin retrieved. {type__}.')
        tm_logger.debug('Generating base type check...')
        base_eval = self._base_eval(type__)
        tm_logger.debug('Base type check generated.')

        if len(type_types := get_args(type_)):
            tm_logger.debug(f'Type has args: {type_types}')
            if type__ is StrictTypeMatcher:
                tm_logger.debug('Generating a StrictTypeMatcher for args and returning its '
                                'function.')
                return StrictTypeMatcher(type_types[0])._function # noqa

            tm_logger.debug('Generating a TypeMatcher for args and returning its function.')
            return TypeMatcher(type_types[0])._function

        tm_logger.debug('Type does not have args.')
        tm_logger.debug(TypeMatcher.G_CHECK)

        def type_check(value: Any) -> bool:
            tm_logger.trace(f'Checking if {value} is {self._spec_msg}{type__} and returning '
                            f'result.')
            return base_eval(value)

        tm_logger.debug(TypeMatcher.R_G_CHECK)
        return type_check

    def __repr__(self) -> str: return f'<{self.__class__.__name__}: {repr(self._type)}>'

    # Because of how Typematcher only creates one instance of a matcher for each type, we MUST treat
    # its type as immutable or suffer the consequences.
    @property
    def type(self):
        """What type is the TypeMatcher checking for?"""
        return self._type


class StrictTypeMatcher(TypeMatcher, Generic[T]):
    G_CHECK = 'Generating check...'
    R_G_CHECK = 'Returning generated check.'

    def _base_eval(self, type_: type) -> callable:
        msg = f'Checking if {{}} is {self._spec_msg}{type_}. Returning result.'

        def t(value: Any) -> bool:
            tm_logger.trace(msg.format(value))
            return type(value) is type_

        return t

    def __new__(cls, type_: Union[type, tuple, UnionType, None]):
        tm_logger.info(f'Getting a new StrictTypeMatcher for {type_}...')
        if not hasattr(StrictTypeMatcher, '_StrictTypeMatcher__existing_matches'):
            tm_logger.debug('StrictTypeMatcher does not already have an _existing_matches '
                            'collection. Adding one...')
            StrictTypeMatcher.__existing_matches = {}

        if type_ in StrictTypeMatcher.__existing_matches:
            tm_logger.debug(f'StrictTypeMatcher already exists for {type_}.')
            tm_logger.info('Returning existing instance.')
            return StrictTypeMatcher.__existing_matches[type_]

        tm_logger.debug(f'StrictTypeMatcher does not already exist for {type_}. Generating a new '
                        f'instance and adding it to existing matches...')
        # Do not use super below. It messes up instance differentiation between StrictTypeMatcher
        # and TypeMatcher.
        StrictTypeMatcher.__existing_matches[type_] = t = object.__new__(cls)
        tm_logger.debug('Initializing instance...')
        t.__true_init(type_)
        tm_logger.info('Returning new instance.')
        return t

    # *DISREGARD python:S1144*
    # This might trigger a warning for python:S1144, that is because some linters do not check the
    # __new__ method properly. This does not violate python:S1144.
    def __true_init(self, type_: Union[type, tuple, UnionType, None]):  # noqa
        """
        This serves as a hidden init so that instances are never re-initialized. This is important
        to prevent eating up too much memory when a user wants MANY instances of ``TypeMatcher``. It
        can also decrease other resource usage.
        """
        self._type = type_
        self._spec_msg = 'a/an '
        self._p_spec_msg = ''
        self._function = self._get_new_function(type_)

    def __init__(self, type_: Union[type, tuple, UnionType, None]):
        """
        A ``StrictTypeMatcher`` used to check whether a variable is exactly a specific type.
        Instances of this class are callable, and can be called with a value to return a boolean
        representing whether the value is the type of the ``StrictTypeMatcher``. The class itself
        can be used as a parametrized type hint for plugging into instances of itself and
        ``TypeMatcher``.

        .. note::
          In Python 3.9 and lower, ``StrictTypeMatcher`` cannot handle ellipsis as the parameter
          when used as a parametrized type hint.
        """
        # This exists to ensure correct documentation appears in IDEs.
        pass


class TransformerFilter:
    def __init__(self, input_rules: Dict[type, callable], raise_on_fail: bool = True):
        """
        A filter with rules and methods to transform values put through it based on their type.
        There are two ways to use this class:

        1. An instance of this class can be used as a property in another class. It can be declared
        outside the class, and re-used in multiple classes. When this property is set, the type of
        the value being set will be checked against each type specified in the ``input_rules``, and
        if it matches any of them, the function at that key within ``input_rules`` will be called
        with that value as its sole argument, then will store the result as the property.

        2. An instance of this class can be used as a function itself, being called on a value to
        attempt to transform it in the same way it would as a property.

        .. note::

            In the case that the value received by a ``TransformerFilter`` does not match any type
            in ``input_rules`` it will store or return ``...`` unless ``raise_on_fail`` is set to
            ``True``.

        :param input_rules: A dictionary using types as keys and functions as the values. Each
            function should correspond with its key's type, and should be built to appropriately
            convert that type.
        :type input_rules: Dict[type, callable]
        :param raise_on_fail: Whether the ``TransformerFilter`` should raise an error when
            attempting to set a value to a type it doesn't have a converter for. If ``False``, then
            any invalid types will result in ``...``.
        :type raise_on_fail: bool
        """
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
        """
        This is used to silently generate a new instance of the class when a duplicate of a
        ``TransformerFilter`` exists within a single class. This is necessary since __set__ doesn't
        tell us the name of the ``TransformerFilter`` being set and prevents duplicates from
        overwriting each other.
        """
        new_cls = cls.__new__(cls, [], blank=True)
        new_cls._accept_args(rules, outputs, raise_on_fail)
        return new_cls

    def _accept_args(self, rules: list, outputs: list, raise_on_fail: bool):
        """Used to set the args on an instance that was generated without a call to __init__."""
        self.__rules = rules
        self.__outputs = outputs
        self._default = ...
        self._length = len(rules)
        self._raise_on_fail = raise_on_fail
        self.pun = {}
        self.pn = {}

    def __call__(self, value: Any, *, inst: Any = None) -> Any:
        """
        Check the type of the value and perform a specified transformation on it based on
        predetermined instructions.

        :param value: The value to transform.
        :param inst: The class instance from which the method should be called (if applicable).
        :return: Returns the transformed value if a transformer is found. Should no transformer be
            found, and raise_on_fail is True, will raise a TypeError exception. Otherwise, will
            return ellipsis.
        """
        for i in range(self._length):
            if self.__rules[i](value):
                if type(func := self.__outputs[i]) is tuple:
                    call = func[0]
                    args = (value, *func[1:])
                    # must ensure self parameter is passed in if the function requires it.
                    if (hasattr(inst, call.__name__)
                            and inspect.ismethod(getattr(inst, call.__name__))):
                        return call(inst, *args)

                    return call(*args)

                # must ensure self parameter is passed in if the function requires it.
                if hasattr(inst, func.__name__) and inspect.ismethod(getattr(inst, func.__name__)):
                    return func(inst, value)

                return func(value)

        if self._raise_on_fail:
            raise TypeError(f'{type(value)} is not a valid type for this attribute.')

        return ...

    def __repr__(self) -> str:
        dict_string = ', '.join(f'{repr(rule)}: {repr(out)}'
                                for rule, out
                                in zip(self.__rules, self.__outputs))
        return f"<TransformerFilter{'{'}{dict_string}{'}'}>"

    def __set_name__(self, owner, name):
        if owner in self.pun:
            # In this scenario, there is already a property in this owner. In order to avoid
            # overwriting the current name, we should create a new class instance and assign that
            # instance the owner/name combo we have here.
            new = TransformerFilter.__from_existing(self.__rules, self.__outputs,
                                                    self._raise_on_fail)
            new.__set_name__(owner, name)
            setattr(owner, name, new)

        else:
            # Go ahead and set the public name and the private name. Make sure the private name is
            # impossible to access without directly using getattr().
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
        # inst is the class instance where the instance of TransformerFilter is being set. We want
        # to check if this instance of TransformerFilter already knows it's a member of this class,
        # so we do that here by checking in this instance's private names dictionary for the class.
        # This is needed in case a class using an instance of TransformerFilter is inherited from.
        if inst.__class__ not in self.pn:
            # If this instance of TransformerFilter doesn't know about the class its being called
            # from, we check through the method resolution order of the calling instance to see if a
            # class we recognize is present.
            for c in inst.__class__.mro():
                if c in self.pn:
                    # When we find that class, we get the correct private and public names of
                    # the TransformerFilter from the internal data and put them under the new class
                    # in the TransformerFilter's lookup.
                    self.pn[inst.__class__] = self.pn[c]
                    self.pun[inst.__class__] = self.pun[c]
                    break

        # By now, we should have the correct class in our private and public name lookups even if we
        # didn't before. We can proceed to actually set the value in inst.
        inst.__setattr__(self.pn[inst.__class__], self(value, inst=inst))

    def copy(self) -> 'TransformerFilter':
        """Creates a copy of a ``TransformerFilter``."""
        new = self.__from_existing(self.__rules, self.__outputs, self._raise_on_fail)
        return new


DOUBLE_FAILED_RECURSION_MSG = \
    ('During the process of checking whether two {%s}s were equal, the recursion limit was '
     'exceeded. An attempt was made to compare the {%s}s in a different way, since it was '
     'assumed the {%s} or something inside was self-containing. Unfortunately, it seems there '
     'were just too many nested objects.')
UNKNOWN_RECURSION_MSG = ('Encountered a value which exhibits recursion, but is not a known '
                         'recursive type. Failed to handle recursion.')


def _rec_lists_checker(recursion_points1, recursion_points2):
    _rec_tester = simple_trinomial(lambda x, y: recursion_points1[y] is x,
                                   lambda x, y: recursion_points2[y] is x)

    # If you're not familiar with walrus operators, I advise you read up on them...
    def rec_lists_check(v1, v2, func_if_missing):
        found = False
        for ji in range(len(recursion_points1)):
            if (ti := _rec_tester(v1, v2, ji)) is True:
                found = True
                break

            elif ti is False:
                return False

        if not found:
            recursion_points1.append(v1)
            recursion_points2.append(v2)
            return func_if_missing

        return True

    def point_check(v1, v2):
        # ... is the "continue to next" result of functions here.
        t1 = _double_tuple_check(v1, v2) if (t := _double_list_check(v1, v2)) is ... else t
        if t1 is True:
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
    """
    This checks whether two objects are *definitely*, *definitely not*, or *possibly* the same.

    :return: ``False`` if the objects are *definitely not* the same.

        ``True`` if the objects are *definitely* the same.

        ``...`` if the objects are *possibly* the same.
    """
    # In the case that either object is None, Ellipsis, or a boolean, we can determine pass or fail
    # immediately. There is no chance of returning an inconclusive result in this scenario.
    if obj1 in _WEIRDOS or obj2 in _WEIRDOS:
        return obj1 is obj2

    # We do not necessarily want to return the result of obj1 is obj2, since if it is False, they
    # may still be lists which are equal.
    if obj1 is obj2:
        return True

    # Ellipsis is used here to represent that the test was inconclusive. We did not prove they were
    # equal, but we also didn't prove they were unequal.
    return ...


def _get_simple_argument_data(func: FunctionType) -> Tuple[int, int, int, bool, bool]:
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

    return (arg_count, pos_only_count, kw_only_count, var_arg, var_kwarg, kw_names, pos_defaults,
            kw_defaults)


def hash_function(func: FunctionType):
    """
    This can *hash* a function insofar as its static image at the time of hashing. Since functions
    are technically mutable, it is heavily advised that use of this is avoided unless a function
    is truly going to be treated as immutable. This means:

    1. **No attributes may be set on a function** after hashing.
    2. The function **should not use *global* variables** that are **changed after hashing**.
    3. The function should have **no internal constants which change**.

    This should not be used on decorated functions.
    """
    return hash(sum(_get_simple_argument_data(func)))


def check_function_equality(func1: FunctionType, func2: Any):
    """
    Checks for equality of two functions. This equality is not standard equality, but is closer to
    how a human would interpret similarity of functions. It is intended to be location-agnostic
    as far as is possible, and is tested for functions nested within other functions and static
    methods in classes.

    .. warning::
        Decorated functions will generally fail to compare equal.
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
    ``check_function_equality``, but for use when a likely self-containing object is contained
    within the constant pool or is a default value.
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


def _true_key_match(key1: Any, obj2: dict):
    for key2 in obj2.keys():
        if key2 == key1:
            if key2 is not key1:
                return False

            return True


def _strict_has_no_issues(obj1, obj2):
    # We should always have two same type objects when this is called, do not worry about making
    # sure they are the same type. Only check the type of one object.
    if isinstance(obj1, dict):
        for k1, v1 in obj1.items():
            if k1 == 0 or k1 == 1:
                if (k1 not in obj2 or not _true_key_match(k1, obj2)
                        or ((v1 == 0 or v1 == 1) and obj2[k1] is not v1)):
                    return False

            elif (v1 == 0 or v1 == 1) and obj2[k1] is not v1:
                return False

            if isinstance(v1, list) or isinstance(v1, dict) or isinstance(v1, tuple):
                for k2, v2 in obj2.items():
                    if k2 == k1:
                        if not _strict_has_no_issues(v1, v2):
                            return False

                        break

    elif isinstance(obj1, list) or isinstance(obj1, tuple):
        for i in range(len(obj1)):
            v1, v2 = obj1[i], obj2[i]
            if (v1 == 0 or v1 == 1) and v1 is not v2:
                return False

            if ((isinstance(v1, list) or isinstance(v1, dict) or isinstance(v1, tuple))
                    and not _strict_has_no_issues(v1, v2)):
                return False

    elif type(obj1) is bool or type(obj2) is bool:
        return obj1 is obj2

    return True


def check_list_equality(list1: Union[list, tuple], list2: Union[list, tuple]):
    """Checks for list equality regardless of whether the lists are recursive or not."""
    try:
        return list1 == list2

    except RecursionError:
        try:
            return _recursive_check_list_equality(list1, list2, [list1], [list2])

        except RecursionError as e:
            fill = 'list' if type(list1) is list else 'tuple'
            raise RecursionError(DOUBLE_FAILED_RECURSION_MSG.format(fill), e)


def strict_check_list_equality(list1: Union[list, tuple], list2: Union[list, tuple]):
    """
    Checks for list equality regardless of whether the lists are recursive or not. Also makes the
    distinction of ``True is not 1`` and ``False is not 0``.
    """
    try:
        ans = list1 == list2
        if not ans:
            # Fail as fast as possible. If they aren't equal, they aren't equal.
            return False

        # At this point, we know the lists should at least be similar, but since this is a strict
        # check, we want to make sure that dicts containing False or True as a key or value don't
        # get compared to dicts with 0 or 1 as a key or value, respectively. As well, we should
        # confirm that lists which contain False or True do not get compared to lists that contain 0
        # or 1 respectively.
        return _strict_has_no_issues(list1, list2)

    except RecursionError:
        try:
            return _recursive_check_list_equality(list1, list2, [list1], [list2],
                                                  strict=True)

        except RecursionError as e:
            fill = 'list' if type(list1) is list else 'tuple'
            raise RecursionError(DOUBLE_FAILED_RECURSION_MSG.format(fill), e)


def _recursive_check_list_equality(list1: Union[list, tuple], list2: Union[list, tuple],
                                   recursion_points1: list, recursion_points2: list,
                                   rec_lists_check: Callable = None, strict: bool = False):
    if rec_lists_check is None:
        rec_lists_check = _rec_lists_checker(recursion_points1, recursion_points2)

    # If we get here, we shouldn't need to check list lengths or tuple lengths.
    for i in range(len(list1)):
        val1 = list1[i]
        val2 = list2[i]
        try:
            if strict:
                if val1 != val2 or not _strict_has_no_issues(val1, val2):
                    return False

            elif val1 is not val2 and val1 != val2:
                return False

        except RecursionError as e:
            t1 = rec_lists_check(val1, val2)
            if ((t1 is not True and t1
                 and not t1(val1, val2, recursion_points1, recursion_points2,
                            rec_lists_check, strict=strict)) or t1 is False):
                return False

            elif t1 is ...:
                raise RecursionError(UNKNOWN_RECURSION_MSG, e)

    return True


def check_dict_equality(dict1: dict, dict2: dict):
    """
    Checks for dictionary equality regardless of whether the dictionaries are recursive or not.
    """
    try:
        return dict1 == dict2

    except RecursionError:
        try:
            return _recursive_check_dict_equality(dict1, dict2, [dict1], [dict2])

        except RecursionError as e:
            raise RecursionError(DOUBLE_FAILED_RECURSION_MSG.format('dict'), e)


def strict_check_dict_equality(dict1: dict, dict2: dict):
    """
    Checks for dictionary equality regardless of whether the dictionaries are recursive or not. Also
    makes the distinction of ``True is not 1`` and ``False is not 0``.
    """
    try:
        ans = dict1 == dict2
        if not ans:
            # Fail as fast as possible. If they aren't equal, they aren't equal.
            return False

        # At this point, we know the dicts should at least be similar, but since this is a strict
        # check, we want to make sure that dicts containing False or True as a key or value don't
        # get compared to dicts with 0 or 1 as a key or value, respectively. As well, we should
        # confirm that lists which contain False or True do not get compared to lists that contain 0
        # or 1 respectively.
        return _strict_has_no_issues(dict1, dict2)

    except RecursionError:
        try:
            return _recursive_check_dict_equality(dict1, dict2, [dict1], [dict2], strict=True)

        except RecursionError as e:
            raise RecursionError(DOUBLE_FAILED_RECURSION_MSG.format('dict'), e)


def _recursive_check_dict_equality(dict1: dict, dict2: dict, recursion_points1: list,
                                   recursion_points2: list, rec_lists_check: Callable = None,
                                   strict: bool = False):
    if rec_lists_check is None:
        rec_lists_check = _rec_lists_checker(recursion_points1, recursion_points2)

    keys1 = list(dict1.keys())

    # If we get here, we shouldn't need to check dict lengths.
    for key in keys1:
        if key not in dict2:
            return False

        val1 = dict1[key]
        val2 = dict2[key]

        try:
            if strict:
                if val1 != val2 or not _strict_has_no_issues(val1, val2):
                    return False

            elif val1 is not val2 and val1 != val2:
                return False

        except RecursionError as e:
            t1 = rec_lists_check(val1, val2)
            if ((t1 is not True
                 and t1
                 and not t1(val1, val2, recursion_points1, recursion_points2, rec_lists_check,
                            strict=strict))
                    or t1 is False):
                return False

            elif t1 is ...:
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
