from typing import Callable

from transforming_list import TransformingList
from init_modifiers import _dictable, _listable, _class_init


def transforming(transformer: Callable):
    """
    Turns a class into a list that will automatically attempt to
    transform new items to the correct type when they are appended or used to
    extend the list.

    :param transformer: A callable that will be used to transform new elements.
    """
    return TransformingList(transformer)


dictable = _dictable
listable = _listable
class_init = _class_init
