from typing import Any, Dict, Collection


class ListRefNode:
    class ListRefNodeIter:
        def __init__(self, parent: 'ListRefNode'):
            self.__start = True
            self.__next = parent

        def __iter__(self):
            return self

        def __next__(self):
            if self.__next is None:
                raise StopIteration

            output = self.__next.val
            self.__next = self.__next.next
            return output

    def __init__(self, source_list: list, index: int,
                 prev: 'ListRefNode' = None, next: 'ListRefNode' = None):
        self.source = source_list
        self.index = index
        self.prev = prev
        self.next = next

    @property
    def val(self) -> Any:
        return self.source[self.index]

    @val.setter
    def val(self, value: Any):
        self.source[self.index] = value

    def __iter__(self):
        return ListRefNode.ListRefNodeIter(self)

    def plop_in(self, *, prev: 'ListRefNode' = None,
                next_: 'ListRefNode' = None):
        if prev is not None:
            self.prev = prev
            self.next = prev.next
            prev.next = self.next.prev = self

        elif next_ is not None:
            self.next = next_
            self.prev = next_.prev
            next_.prev = self.prev.next = self

    def drop_out(self):
        if self.next is not None and self.prev is not None:
            self.next.prev = self.prev
            self.prev.next = self.next

    def lower_index(self):
        self.index -= 1
        if self.next is not None:
            self.next.lower_index()

    def __del__(self):
        self.drop_out()
        self.lower_index()
        del self.source[self.index]


class WindowedList:
    def __init__(self, values: Collection):
        self._lookup: Dict[int, ListRefNode] = {}
        self._on = {}
        if len(values):
            self._lookup[0] = ListRefNode(values, 0)
            self._on[0] = True
            for i in range(1, len(values)):
                self._lookup[i] = ListRefNode(values, i, self._lookup[i - 1])
                self._lookup[i - 1].next = self._lookup[i]
                self._on[i] = True

    def __iter__(self):
        for i in range(len(self._on)):
            if self._on[i]:
                return iter(self._lookup[i])

        return iter([])

    def __getitem__(self, index: int):
        return self._lookup[index].val

    def __setitem__(self, index: int, value):
        self._lookup[index].val = value

    def __delitem__(self, index: int):
        worker = self._lookup[index]
        for i in range(index, len(self._lookup) - 1):
            self._lookup[i] = self._lookup[i + 1]
            t = self._on[i] = self._on[i + 1]
            if not t:
                self._lookup[i].lower_index()

        del worker
        del self._lookup[len(self._lookup) - 1]

    def disable_index(self, index: int):
        self._on[index] = False
        self._lookup[index].drop_out()

    def enable_index(self, index: int):
        if not self._on[index]:
            self._on[index] = True
            for i in range(index - 1, -1, -1):
                if self._on[i]:
                    self._lookup[index].plop_in(prev=self._lookup[i])
                    return

            for i in range(index + 1, len(self._lookup)):
                if self._on[i]:
                    self._lookup[index].plop_in(next=self._lookup[i])
                    return
