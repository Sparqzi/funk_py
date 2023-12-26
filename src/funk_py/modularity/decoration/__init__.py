from typing import Callable

from transforming_list import TransformingList


def transforming(transformer: Callable):
    return TransformingList(transformer)
