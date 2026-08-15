# Source: https://github.com/hexdoc-dev/hexdoc/blob/d8cfe270aa297cd769ada21e7919f6566e019f4c/src/hexdoc/patchouli/text.py


# pyright: reportPrivateUsage=false

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from enum import Enum, auto, unique
from typing import Any, Literal, Self, final

logger = logging.getLogger(__name__)


DEFAULT_MACROS = {
    "$(obf)": "$(k)",
    "$(bold)": "$(l)",
    "$(strike)": "$(m)",
    "$(italic)": "$(o)",
    "$(italics)": "$(o)",
    "$(list": "$(li",
    "$(reset)": "$()",
    "$(clear)": "$()",
    "$(2br)": "$(br2)",
    "$(p)": "$(br2)",
    "/$": "$()",
    "<br>": "$(br)",
    "$(nocolor)": "$(0)",
    "$(item)": "$(#b0b)",
    "$(thing)": "$(#490)",
}

_REPLACEMENTS = {
    "br": "\n",
    "playername": "[Playername]",
}

_COLORS = {
    "0": "000",
    "1": "00a",
    "2": "0a0",
    "3": "0aa",
    "4": "a00",
    "5": "a0a",
    "6": "fa0",
    "7": "aaa",
    "8": "555",
    "9": "55f",
    "a": "5f5",
    "b": "5ff",
    "c": "f55",
    "d": "f5f",
    "e": "ff5",
    "f": "fff",
}


# Higgledy piggledy
# Old fuck Alwinfy said,
# "Eschew your typechecks and
# live with a pair,"
#
# Making poor Object do
# Re-re-re-factoring
# Till Winfy took up her
# Classical flair.


@unique
class TryGetEnum(Enum):
    @classmethod
    def get(cls, value: Any):
        try:
            return cls(value)
        except ValueError:
            return None


class CommandStyleType(TryGetEnum):
    """Command styles, like `$(type)`."""

    obfuscated = "k"
    bold = "l"
    strikethrough = "m"
    underline = "n"
    italic = "o"


class FunctionStyleType(TryGetEnum):
    """Function styles, like `$(type:value)`."""

    tooltip = "t"
    cmd_click = "c"


class SpecialStyleType(Enum):
    """Styles with no defined name, like `$(#0080ff)`, or styles which must be handled
    differently than the normal styles, like `$()`."""

    base = auto()
    paragraph = auto()
    color = auto()
    link = "l"


@dataclass(kw_only=True, frozen=True)
class Style:
    type: CommandStyleType | FunctionStyleType | SpecialStyleType

    @staticmethod
    def parse(style_str: str) -> Style | _CloseTag | str:
        # direct text replacements
        if style_str in _REPLACEMENTS:
            return _REPLACEMENTS[style_str]

        # paragraph
        if style := ParagraphStyle.try_parse(style_str):
            return style

        # commands
        if style_type := CommandStyleType.get(style_str):
            return CommandStyle(type=style_type)

        # reset color
        if style_str == "0":
            return _CloseTag(type=SpecialStyleType.color)

        # preset colors
        if style_str in _COLORS:
            return FunctionStyle(type=SpecialStyleType.color, value=_COLORS[style_str])

        # hex colors (#rgb and #rrggbb)
        if style_str.startswith("#") and len(style_str) in [4, 7]:
            return FunctionStyle(type=SpecialStyleType.color, value=style_str[1:])

        # functions
        if ":" in style_str:
            name, value = style_str.split(":", 1)

            # keys
            if name == "k":
                return str(value)

            # links
            if name == SpecialStyleType.link.value:
                return LinkStyle(value=value)

            # all the other functions
            if style_type := FunctionStyleType.get(name):
                return FunctionStyle(type=style_type, value=value)

        # reset
        if style_str == "":
            return _CloseTag(type=SpecialStyleType.base)

        # close functions
        if style_str.startswith("/"):
            # links
            if style_str[1:] == SpecialStyleType.link.value:
                return _CloseTag(type=SpecialStyleType.link)

            # all the other functions
            if style_type := FunctionStyleType.get(style_str[1:]):
                return _CloseTag(type=style_type)

        # oopsies
        raise ValueError(f"Unhandled style: {style_str}")


@dataclass(kw_only=True, frozen=True)
class CommandStyle(Style):
    type: CommandStyleType | Literal[SpecialStyleType.base]


class ParagraphStyleSubtype(Enum):
    paragraph = auto()
    list_item = auto()


@dataclass(kw_only=True, frozen=True)
class ParagraphStyle(Style):
    type: Literal[SpecialStyleType.paragraph] = SpecialStyleType.paragraph
    subtype: ParagraphStyleSubtype

    @classmethod
    def try_parse(cls, style_str: str) -> ParagraphStyle | None:
        if style_str == "br2":
            return cls.paragraph()

        # https://github.com/VazkiiMods/Patchouli/blob/4522fbb3e4/Xplat/src/main/java/vazkii/patchouli/client/book/text/BookTextParser.java#L346-L355
        if re.fullmatch(r"li\d?", style_str):
            level_str = style_str.removeprefix("li")
            level = int(level_str) if level_str.isnumeric() else 1
            return ListItemStyle(level=level)

    @classmethod
    def paragraph(cls):
        return ParagraphStyle(subtype=ParagraphStyleSubtype.paragraph)

    @property
    def macro(self) -> str:
        return f"paragraph_{self.subtype.name}"


@dataclass(kw_only=True, frozen=True)
class ListItemStyle(ParagraphStyle):
    subtype: Literal[ParagraphStyleSubtype.list_item] = ParagraphStyleSubtype.list_item
    level: int


@dataclass(kw_only=True, frozen=True)
class FunctionStyle(Style):
    type: FunctionStyleType | Literal[SpecialStyleType.color]
    value: str


@dataclass(kw_only=True, frozen=True)
class LinkStyle(Style):
    type: Literal[SpecialStyleType.link] = SpecialStyleType.link
    value: str


# intentionally not inheriting from Style, because this is basically an implementation
# detail of the parser and should not be returned or exposed anywhere
@dataclass(kw_only=True, frozen=True)
class _CloseTag:
    type: (
        FunctionStyleType
        | Literal[
            SpecialStyleType.link,
            SpecialStyleType.base,
            SpecialStyleType.color,
        ]
    )


STYLE_REGEX = re.compile(r"\$\(([^)]*)\)")


@final
@dataclass
class FormatTree:
    style: Style
    children: list[FormatTree | str]  # this can't be Self, it breaks Pydantic
    raw: str | None = None

    @classmethod
    def format(cls, string: str, *, macros: dict[str, str]) -> Self:
        for macro, replace in macros.items():
            if macro in replace:
                raise RuntimeError(
                    f"Recursive macro: replacement `{replace}` is matched by key `{macro}`"
                )

        working_string = resolve_macros(string, macros)

        # lex out parsed styles
        text_nodes: list[str] = []
        styles: list[Style | _CloseTag] = []
        text_since_prev_style: list[str] = []
        last_end = 0

        for match in re.finditer(STYLE_REGEX, working_string):
            # get the text between the previous match and here
            leading_text = working_string[last_end : match.start()]
            text_since_prev_style.append(leading_text)
            last_end = match.end()

            match Style.parse(match[1]):
                case str(replacement):
                    # str means "use this instead of the original value"
                    text_since_prev_style.append(replacement)
                case Style() | _CloseTag() as style:
                    # add this style and collect the text since the previous one
                    styles.append(style)
                    text_nodes.append("".join(text_since_prev_style))
                    text_since_prev_style.clear()

        text_nodes.append("".join(text_since_prev_style) + working_string[last_end:])
        first_node = text_nodes.pop(0)

        # parse
        style_stack = [
            FormatTree(CommandStyle(type=SpecialStyleType.base), []),
            FormatTree(ParagraphStyle.paragraph(), [first_node]),
        ]
        for style, text in zip(styles, text_nodes):
            tmp_stylestack: list[Style] = []
            if style.type == SpecialStyleType.base:
                while style_stack[-1].style.type != SpecialStyleType.paragraph:
                    last_node = style_stack.pop()
                    style_stack[-1].children.append(last_node)
            elif any(tree.style.type == style.type for tree in style_stack):
                while len(style_stack) >= 2:
                    last_node = style_stack.pop()
                    style_stack[-1].children.append(last_node)
                    if last_node.style.type == style.type:
                        break
                    tmp_stylestack.append(last_node.style)

            for sty in tmp_stylestack:
                style_stack.append(FormatTree(sty, []))

            if isinstance(style, _CloseTag):
                if text:
                    style_stack[-1].children.append(text)
            else:
                style_stack.append(FormatTree(style, [text] if text else []))

        while len(style_stack) >= 2:
            last_node = style_stack.pop()
            style_stack[-1].children.append(last_node)

        unvalidated_tree = style_stack[0]
        unvalidated_tree.raw = string

        assert isinstance(unvalidated_tree, cls)

        return unvalidated_tree


def resolve_macros(string: str, macros: dict[str, str]) -> str:
    # this could use ahocorasick, but it works fine for now
    old_string = None
    while old_string != string:
        old_string = string
        for macro, replace in macros.items():
            string = string.replace(macro, replace)
    return string
