"""
Elements
========

The elements, based upon the base elements which try to offer the core
functionality of reStructruedText.
"""
import textwrap

from .containers import ListContainer
from .base import Element, Inline, Block
from .utils import check_type


def str_to_inline(text):
    if isinstance(text, str):
        return Span(*Str.from_str(text))
    elif (
        isinstance(text, (list, tuple))
        and len(text) == 1
        and isinstance(text[0], str)
    ):
        return Span(*Str.from_str(text[0]))
    else:
        return text


def str_to_inline_tuple(text):
    if isinstance(text, str):
        return (Span(*Str.from_str(text)),)
    elif (
        isinstance(text, (list, tuple))
        and len(text) == 1
        and isinstance(text[0], str)
    ):
        return (Span(*Str.from_str(text[0])),)
    else:
        return text


def str_to_block(text):
    if isinstance(text, str):
        return Plain(*Str.from_str(text))
    elif (
        isinstance(text, (list, tuple))
        and len(text) == 1
        and isinstance(text[0], str)
    ):
        return Plain(*Str.from_str(text[0]))
    else:
        return text


def str_to_block_tuple(text):
    if isinstance(text, str):
        return (Plain(*Str.from_str(text)),)
    elif (
        isinstance(text, (list, tuple))
        and len(text) == 1
        and isinstance(text[0], str)
    ):
        return (Plain(*Str.from_str(text[0])),)
    else:
        return text


class Document(Element):
    """The document class which elements should usually be part of.

    :param args: Children which are part of the document.
    :type args: `Block<pyposo.base.Block>` | `_Section<pyposo.elements._Section>`
    """

    __slots__ = ["_textwidth"]
    _children = ["content"]
    _main_container = "content"
    _content_seperator = "\n"

    def __init__(self, *args, **kwargs):
        self.textwidth = kwargs.get("textwidth", None)
        self._set_content(args, (_Section, Block))

    @property
    def textwidth(self):
        return self._textwidth

    @textwidth.setter
    def textwidth(self, textwidth):
        textwidth = check_type(textwidth, (int, type(None)))
        self._textwidth = textwidth


class Space(Inline):
    """A simple space.

    """
    __slots__ = []

    @staticmethod
    def dump():
        return " "

    def __repr__(self):
        return self.tag

    def __len__(self):
        return 1


class LineBreak(Inline):
    __slots__ = []

    @staticmethod
    def dump():
        return "\n"

    def __repr__(self):
        return self.tag

    def __len__(self):
        return 0


class Str(Inline):
    """A simple string."""
    __slots__ = ["string"]

    def __init__(self, string):
        self.string = check_type(
            string, str, "Expected a string; got: {type_}."
        )

    def dump(self):
        return self.string

    def _repr_children(self):
        return repr(self.string)

    @classmethod
    def _from_str(cls, string):
        first = True
        for s in string.split():
            if first:
                first = False
            else:
                yield Space()
            yield cls(s)

    @classmethod
    def from_str(cls, string):
        return list(cls._from_str(string))

    def __len__(self):
        return len(self.string)


class Paragraph(Block):
    _children = ["content"]

    def __init__(self, *args):
        self._set_content(args, Inline, converter=str_to_inline)

    @property
    def format_string(self):
        if self.index == 0 or self.index is None:
            return "{content}"
        else:
            return "\n{content}"

    def _render_content(self):
        content = "".join(c.dump() for c in self.content)
        kwargs = {}
        if self.textwidth is not None:
            kwargs["width"] = self.textwidth
        if isinstance(self.parent, (Document, _Section)):
            return textwrap.fill(content, **kwargs)
        else:
            return content


class Plain(Block):
    _children = ["content"]

    def __init__(self, *args):
        self._set_content(args, Inline)

    @property
    def format_string(self):
        return "{content}"


class _DivBlock(Block):
    _children = ["content", "title"]
    _directive = "class"
    _content_indent = 3
    _content_seperator = "\n"
    _leader = ""

    def __init__(self, title, *args):
        title = str_to_inline_tuple(title)

        self._set_title(title, Inline)
        self._set_content(args, (Block, _Section))

    @property
    def format_string(self):
        fs = "{title}"
        if self.content:
            fs = f"{fs}\n\n{{{self.content}}}"

        if self.index == 0:
            fs = f"\n{fs}"

        return fs

    def _render_title(self):
        format_string = ".. {directive}:: {title}"
        title = "".join(t.dump() for t in self.title)
        return format_string.format(directive=self._directive, title=title)

    @property
    def indent(self):
        indent = 0
        parent = self.parent
        while not isinstance(parent, (Document, type(None))):
            indent += getattr(parent, "_content_indent", 0)
            parent = parent.parent
        return indent

    @property
    def content_indent(self):
        return " " * self._content_indent

    @property
    def content_width(self):
        if self.textwidth is None:
            content_width = None
        else:
            content_width = self.textwidth - self.indent
        return content_width

    @property
    def leader(self):
        return self._leader

    def _wrap(self, linenumber, text):
        cw = self.content_width
        kwargs = {"width": cw} if cw is not None else {}
        return textwrap.wrap(
            text,
            replace_whitespace=False,
            initial_indent=self.content_indent,
            subsequent_indent=self.content_indent,
            **kwargs,
        )

    def _render_content(self):
        item = self._content_seperator.join(c.dump() for c in self.content)
        item = item.splitlines()

        item = list(map(lambda i: self._wrap(*i), enumerate(item)))

        item = list("\n".join(i) for i in item)
        content = self._content_seperator.join(item)
        return content


class _Wrapped(Inline):
    _children = ["content"]
    _head = ""
    _tail = None
    _main_container = "content"

    def __init__(self, *args):
        args = str_to_inline_tuple(args)
        self._set_content(args, Inline)

    def _render_content(self):
        head = self._head
        tail = head if self._tail is None else self._tail
        return "{head}{content}{tail}".format(
            head=head,
            content="".join(c.dump() for c in self.content),
            tail=tail,
        )


class Span(Inline):
    _children = ["content"]

    def __init__(self, *args):
        args = str_to_inline_tuple(args)
        self._set_content(args, Inline)


class Emph(_Wrapped):
    _head = "*"


class Strong(_Wrapped):
    _head = "**"


class _Section(Element):
    """
    Base class for :class:`Title` and sections/subsections ..
    """
    _children = ["title", "content"]
    _header_char = "="
    _overline = False
    _inset = False
    _content_seperator = "\n"
    _main_container = "content"

    def __init__(self, title, *args):
        title = str_to_inline_tuple(title)

        self._set_title(title, Inline)
        self._set_content(args, Block)

    def _render_title(self):
        format_string = "{overline}{title}\n{underline}\n"

        title = "".join(c.dump() for c in self.title)
        if self._inset:
            title = f" {title} "

        return format_string.format(
            overline=(
                "{}\n".format(self._header_char * len(title))
                if self._overline
                else ""
            ),
            title=title,
            underline=self._header_char * len(title),
        )

    @property
    def format_string(self):
        if self.content:
            fs = "{title}{content}\n"
        else:
            fs = "{title}"

        if not (self.index == 0 or self.index is None):
            fs = f"\n{fs}"

        return fs


class Title(_Section):
    _overline = True
    _inset = True


class Section(_Section):
    pass


class Subsection(_Section):
    _header_char = "-"


class Subsubsection(_Section):
    _header_char = "~"


class _ListItem(Element):
    _children = ["content"]
    _content_seperator = "\n"
    _content_indent = 2
    _main_container = "content"
    _leader = "- "

    def __init__(self, *args):
        self._set_content(args, Block, converter=str_to_block)

    @property
    def indent(self):
        indent = 0
        parent = self.parent
        while not isinstance(parent, (Document, type(None))):
            indent += getattr(parent, "_content_indent", 0)
            parent = parent.parent
        return indent

    @property
    def content_indent(self):
        return " " * self._content_indent

    @property
    def leader(self):
        return self._leader

    @property
    def content_width(self):
        if self.textwidth is None:
            content_width = None
        else:
            content_width = self.textwidth - self.indent
        return content_width

    def _wrap(self, linenumber, text):
        cw = self.content_width
        kwargs = {"width": cw} if cw is not None else {}
        return textwrap.wrap(
            text,
            replace_whitespace=False,
            initial_indent=(
                self.leader if linenumber == 0 else self.content_indent
            ),
            subsequent_indent=self.content_indent,
            **kwargs,
        )

    def _render_content(self):
        item = self._content_seperator.join(c.dump() for c in self.content)
        item = item.splitlines()

        item = list(map(lambda i: self._wrap(*i), enumerate(item)))

        item = list("\n".join(i) for i in item)
        content = self._content_seperator.join(item)
        return content


class _List(Block):
    __slots__ = []
    _children = ["content"]
    _content_seperator = "\n"

    def __init__(self, *args):
        self._set_content(args, _ListItem)

    @property
    def format_string(self):
        return "\n{content}\n"

    def _render_content(self):
        children = list(c.dump() for c in self.content)
        return self._content_seperator.join(children)


class ListItem(_ListItem):
    pass


class BulletList(_List):
    def __init__(self, *args):
        self._set_content(args, ListItem)


class EnumeratedListItem(_ListItem):
    @property
    def _content_indent(self):
        return len(self.container) // 10 + 3

    @property
    def leader(self):
        return "{}.{:{align}}".format(
            self.index + 1,
            "",
            align=self._content_indent - (self.index + 1) // 10 - 2,
        )


class EnumeratedList(_List):
    def __init__(self, *args):
        self._set_content(args, EnumeratedListItem)


class FieldListItem(_ListItem):
    _children = ["term", "content"]
    _max_content_indent = 7
    _fallback_content_indent = 3
    _main_container = "content"

    def __init__(self, term, *args):
        term = str_to_inline_tuple(term)
        args = str_to_block_tuple(args)
        self._set_term(term, Inline)
        self._set_content(args, Block)

    def _set_term(self, term):
        term = check_type(term, Inline)
        self._term = ListContainer(
            term, oktypes=Inline, parent=self, location="term"
        )

    @property
    def leader(self):
        return ":{}: ".format("".join(c.dump() for c in self.term))

    @property
    def format_string(self):
        return "{content}"

    @property
    def _content_indent(self):
        if len(self.leader) > self._max_content_indent:
            return self._fallback_content_indent
        else:
            return len(self.leader)


class FieldList(_List):
    _children = ["content"]

    def __init__(self, *args):
        self._set_content(args, FieldListItem)
