from typing import Callable


class TransformingList:
    def __init__(self, transformer: Callable):
        """
        Handles the boilerplate for a list that will automatically attempt to
        transform new items to the correct type.

        :param transformer: A callable that will be used to transform new
            elements.
        """
        self.transformer = transformer

    def t__init__(self, func):
        def t_init(s, objs=None):
            if objs is not None:
                func(s, [self.transformer(obj) for obj in objs])

            else:
                func(s)

        return t_init

    def t__setitem__(self, func):
        def t_setitem(s, i, obj):
            return func(s, i, self.transformer(obj))

        return t_setitem

    def t__add__(self, func):
        def t_add(s, objs):
            return func(s, [self.transformer(obj) for obj in objs])

        return t_add

    def t__iadd__(self, func):
        def t_iadd(s, objs):
            return func(s, [self.transformer(obj) for obj in objs])

        return t_iadd

    def t__contains__(self, func):
        def t_contains(s, obj):
            return func(s, self.transformer(obj))

        return t_contains

    def tappend(self, func):
        def t_append(s, obj):
            return func(s, self.transformer(obj))

        return t_append

    def textend(self, func):
        def t_extend(s, objs):
            return func(s, [self.transformer(obj) for obj in objs])

        return t_extend

    def tindex(self, func):
        def t_index(s, obj, start, end):
            return func(s, self.transformer(obj), start, end)

        return t_index

    def tcount(self, func):
        def t_count(s, obj):
            return func(s, self.transformer(obj))

        return t_count

    def tinsert(self, func):
        def t_insert(s, i, obj):
            return func(s, i, self.transformer(obj))

        return t_insert

    def tremove(self, func):
        def t_remove(s, obj):
            func(self.transformer(obj))

        return t_remove

    def __call__(self, cls):
        cls.__init__ = self.t__init__(cls.__init__)
        cls.__setitem__ = self.t__setitem__(cls.__setitem__)
        cls.__add__ = self.t__add__(cls.__add__)
        cls.__iadd__ = self.t__iadd__(cls.__iadd__)
        cls.__contains__ = self.t__contains__(cls.__contains__)
        cls.append = self.tappend(cls.append)
        cls.extend = self.textend(cls.extend)
        cls.index = self.tindex(cls.index)
        cls.count = self.tcount(cls.count)
        cls.insert = self.tinsert(cls.insert)
        cls.remove = self.tremove(cls.remove)
        return cls
