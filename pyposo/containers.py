"""
The container class which harbors an Elements children.
"""
from collections import abc
from .utils import check_type


def attach(element, parent, location):
    if not isinstance(element, (int, str, bool)):
        element.parent = parent
        element.location = location
    else:
        print(element, 'has no parent')
    return element


class ListContainer(abc.MutableSequence):
    __slots__ = ['parent', 'oktypes', 'list', 'location', 'converter']

    def __init__(self, *elements, oktypes=object, parent=None, location=None,
                 converter=None):
        self.oktypes = oktypes
        self.parent = parent
        self.location = location
        self.converter = converter

        self.list = list()

        self.extend(elements)

    def __getitem__(self, index):
        if isinstance(index, int):
            return attach(self.list[index], self.parent, self.location)
        else:
            partial_list = self.list.__getitem__(index)
            new_list_container = ListContainer(
                *partial_list,
                oktypes=self.oktypes,
                parent=self.parent,
                location=self.location,
                converter=self.converter,
            )
            return new_list_container

    def __setitem__(self, index, value):
        value = self._check_value(value)
        self.list[index] = value

    def insert(self, index, value):
        value = self._check_value(value)
        self.list.insert(index, value)

    def _check_value(self, value):
        if self.converter is not None:
            value = self.converter(value)
        value = check_type(value, self.oktypes)
        return value

    def __delitem__(self, index):
        del self.list[index]

    def __len__(self):
        return len(self.list)

    def __repr__(self):
        return '{name}({content})'.format(
            name=type(self).__name__,
            content=', '.join(repr(c) for c in self),
        )
