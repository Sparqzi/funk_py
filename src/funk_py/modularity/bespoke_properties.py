from functools import wraps
from typing import Callable, Any


def decorated(target: str) -> Callable:
    @wraps
    def wrapper(t_func: Callable):
        def new_func(self, func: Callable):
            if self.decorated:
                setattr(self, target, func)

            else:
                t_func(self, func)

        return new_func

    return wrapper


class DecoratorProxy:
    def __init__(self, value: Any, instance, name: str):
        """
        A proxy which allows a value from a class to be manipulated indirectly. An instance of
        ``DecoratorProxy`` can can be called on a value that the user wants to set the original
        value to.

        :param value: The value that the ``DecoratorProxy`` actually should have.
        :param instance: The class instance the ``DecoratorProxy`` is associated with.
        :param name: The name of the variable in ``instance`` which this ``DecoratorProxy`` should
            be linked to.
        """
        object.__setattr__(self, '__value', value)
        object.__setattr__(self, '__instance', instance)
        object.__setattr__(self, '__name', name)

    def __getattribute__(self, item):
        if item not in ['__call__', '__repr__', '__str__']:

            return getattr(object.__getattribute__(self, '__value'), item)

        else:
            return object.__getattribute__(self, item)

    def __call__(self, value: Any):
        setattr(object.__getattribute__(self, '__instance'),
                object.__getattribute__(self, '__name'), value)
        return value

    def __repr__(self):
        return object.__getattribute__(self, '__value').__repr__()

    def __str__(self):
        return object.__getattribute__(self, '__value').__repr__()


class DecoratableProp:
    def __init__(self, also_does: Callable = None):
        """
        A property that will be allowed to be used as a decorator if the containing class instance
        has _decorated set to True.

        :param also_does: Allows side effects and allows inclusion of outside information (in the
            case of a class's method).
        """
        self.also_does = also_does

    def __set_name__(self, owner, name):
        self.pun = name
        self.pn = '\\\t :' + name

    def __get__(self, instance, owner):
        val = getattr(instance, self.pn)
        if hasattr(instance, '_decorated') and instance._decorated is True:
            return DecoratorProxy(val, instance, self.pn)

        else:
            # User either doesn't know they needed to set _decorated to True, or didn't mean to
            # actually utilize this class.
            return val

    def __set__(self, instance, value):
        """
        Sets the value of this property. If this property has ``also_does`` set, it will first call
        ``also_does`` on value. If the result of ``also_does(value)`` is ``None``, then it will
        store ``value`` in the class.

        :param instance: The class instance for which this property is being set.
        :param value: The value to set it to.
        """
        if self.also_does is not None:
            if instance.__class__.__name__ in self.also_does.__qualname__.split('.'):
                # If also_does is a member of the instance's class, make sure to pass it the
                # instance as the first argument, otherwise there may be some issues.
                ox = self.also_does(instance, value)

            else:
                # also_does is not a member of the instance class. No need to be pass the instance.
                ox = self.also_does(value)

            if ox is not None:
                # Only set value to the result of also_does if also_does returned something.
                value = ox

        setattr(instance, self.pn, value)


class SwitchableInputProp:
    def __init__(self, switch: str, default: bool = False):
        self.switch = switch
        self.default = default

    def __set_name__(self, owner, name):
        self.pun = name
        self.pn = '\\\t :' + name

    def __get__(self, instance, owner):
        return getattr(instance, self.pn)

    def __set__(self, instance, value):
        if hasattr(instance, self.switch):
            if getattr(instance, self.switch):
                setattr(instance, self.pn, value)

        elif self.default:
            setattr(instance, self.pn, value)
