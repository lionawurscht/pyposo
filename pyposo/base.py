"""
Base Elements
=============
"""
from contextlib import contextmanager

from .containers import ListContainer


def _create_child_properties(child_name):
    def get_child(self):
        return getattr(self, f"_{child_name}")

    def set_child(self, value):
        child = getattr(self, child_name)
        oktypes = child.oktypes
        value = value.list if isinstance(value, ListContainer) else list(value)
        list_container = ListContainer(
            *value, oktypes=oktypes, parent=self, location=child_name
        )
        setattr(self, f"_{child_name}", list_container)

    def _set_child(self, value, oktypes, converter=None):
        if value is None:
            value = []
        list_container = ListContainer(
            *value,
            oktypes=oktypes,
            parent=self,
            location=child_name,
            converter=converter,
        )
        setattr(self, f"_{child_name}", list_container)

    return get_child, set_child, _set_child


class _MetaElement(type):
    def __new__(mcl, name, bases, attrs):
        slots = list(attrs.get("__slots__", list()))
        if "_children" in attrs:
            for child_name in attrs["_children"]:
                getter, setter, _setter = _create_child_properties(child_name)
                attrs[child_name] = property(getter, setter)
                attrs[f"_set_{child_name}"] = _setter
                slots.append(f"_{child_name}")

        attrs["__slots__"] = slots

        return super().__new__(mcl, name, bases, attrs)


class Element(metaclass=_MetaElement):
    __slots__ = [
        "parent",
        "location",
        "_root_container",
        "_prev_containers",
        "_append_queue",
    ]
    _children = []
    _main_container = None

    @contextmanager
    def create(self, child):
        is_valid_child = not (
            self._main_container is None or child._main_container is None
        )

        if not is_valid_child:
            raise RuntimeError(
                "Only Elements with a set variable for "
                '"_main_container" can be '
                "used as "
                "contaxtmanagers or Children."
            )

        prev_containers = getattr(self, "_prev_containers", [])
        self._prev_containers = prev_containers

        prev_containers.append(getattr(self, self._main_container))

        new_container = getattr(child, child._main_container)

        setattr(self, f"_{self._main_container}", new_container)

        yield child

        setattr(self, f"_{self._main_container}", prev_containers.pop())
        self.append(child)

        append_queue = getattr(self, "_append_queue", {})
        self._append_queue = append_queue

        for object_ in append_queue.get(len(prev_containers), []):
            self.append(object_)

    @contextmanager
    def root(self, index=0):
        new_container = self._prev_containers[index]
        self._prev_containers.append(getattr(self, self._main_container))

        setattr(self, f"_{self._main_container}", new_container)

        yield new_container.parent

        setattr(self, f"_{self._main_container}", self._prev_containers.pop())

    def append_later(self, object_, index=0):
        append_queue = getattr(self, "_append_queue", {})
        self._append_queue = append_queue
        if index < 0:
            index = len(self._prev_containers) + index

        append_queue.setdefault(index, []).append(object_)

    def _repr_children(self):
        if len(self._children) == 1:
            return self._repr_child(self._children[0])
        elif self._children:
            return ", ".join(
                f"{child}={self._repr_child(child)}" for child in self._children
            )
        else:
            return ""

    def _repr_child(self, child):
        child = getattr(self, child)
        return ", ".join(repr(c) for c in child)

    def __repr__(self):
        return "{tag}({children})".format(
            tag=self.tag, children=self._repr_children()
        )

    def _render_child(self, child):
        if hasattr(self, f"_render_{child}"):
            return getattr(self, f"_render_{child}")()
        else:
            return getattr(self, f"_{child}_seperator", "").join(
                c.dump() for c in getattr(self, child)
            )

    def dump(self):
        return self.format_string.format(
            **{child: self._render_child(child) for child in self._children}
        )

    @property
    def format_string(self):
        return "".join(f"{{{c}}}" for c in self._children)

    @property
    def tag(self):
        return type(self).__name__

    @property
    def document(self):
        document = self
        while document is not None and document.tag != "Document":
            document = document.parent
        return document

    @property
    def container(self):
        if self.parent is None:
            return None
        elif self.location is None:
            return self.parent.content
        else:
            return getattr(self.parent, self.location)

    @property
    def index(self):
        # I need the try ... escape because otherwise, __getattr__ will be
        # called resulting in the containers index method being returned
        # instead of this objects index.
        container = self.container
        try:
            index = container.index(self)
        except AttributeError:
            index = None

        return index

    @property
    def textwidth(self):
        return getattr(self.document, "textwidth", None)

    def offset(self, offset):
        own_index = self.container.index(self)
        container = self.container
        sibling_index = own_index + offset
        if sibling_index <= 0 < len(container):
            return container[sibling_index]

    def next(self):
        return self.offset(1)

    def prev(self):
        return self.offset(-1)

    def __getattr__(self, name):
        # Hotfix for the behaviour that elements without a parent report
        # themselves as parents of themselves, may lead to more trouble ...
        if name == 'parent':
            return None

        if self._main_container is not None:
            try:
                return getattr(getattr(self, self._main_container), name)
            except AttributeError:
                pass

        raise AttributeError(f"No attribute: {name!r}")


class Inline(Element):
    __slots__ = []


class Block(Element):
    """
    Base element for all block elements.

    """
    __slots__ = ["_indent"]
    _main_container = "content"
