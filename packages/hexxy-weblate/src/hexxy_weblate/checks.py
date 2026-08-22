from __future__ import annotations

from pathlib import Path
from typing import Any, override

from django.dispatch import receiver
from django.utils.html import format_html
from django.utils.translation import gettext, gettext_lazy
from git import TYPE_CHECKING
from hexdoc.core import I18n, ResourceLocation
from hexdoc.core.properties import LangProps
from hexdoc.patchouli import FormatTree
from hexdoc.patchouli.text import DEFAULT_MACROS
from pydantic import BaseModel, Field
from weblate.checks.base import TargetCheck
from weblate.trans.signals import vcs_post_update
from weblate.utils.html import format_html_join_comma

if TYPE_CHECKING:
    from weblate.checks.models import Check
    from weblate.trans.models import Component, Unit
    from weblate.vcs.base import Repository

PATCHOULI_BOOK_JSON_FLAG = "patchouli-book-json"
PATCHOULI_MACROS_FLAG = "patchouli-macros"


class PatchouliFormattingCheck(TargetCheck):
    check_id = "patchouli-formatting"
    name = gettext_lazy("Patchouli formatting")
    description = gettext_lazy(
        "Patchouli text formatting should be syntactically valid."
    )
    default_disabled = True

    @override
    def check_single(self, source: str, target: str, unit: Unit):  # pyright: ignore[reportIncompatibleMethodOverride]
        try:
            self._format_string(target, unit)
            return None
        except Exception as e:  # noqa: BLE001
            return str(e)

    @override
    def get_description(self, check_obj: Check) -> str:
        messages = set[str]()
        unit: Unit = check_obj.unit
        source: str = unit.source_string
        for target in unit.get_target_plurals():
            if message := self.check_single(source, target, unit):
                messages.add(message)
        if not messages:
            return self.description
        return format_html(
            "{} {}",
            gettext("Failed to parse Patchouli formatting:"),
            format_html_join_comma(
                "<code>{}</code>", ((message,) for message in sorted(messages))
            ),
        )

    def _format_string(self, string: str, unit: Unit):
        return FormatTree.format(
            string,
            book_id=ResourceLocation("patchouli", "example"),
            i18n=I18n(
                lookup={},
                lang="en_us",
                default_i18n=None,
                enabled=False,
                lang_props=LangProps(quiet=True, ignore_errors=True),
            ),
            macros=DEFAULT_MACROS | self._get_macros(unit),
            is_0_black=False,
            pm=FakePluginManager(),  # pyright: ignore[reportArgumentType] # lie
            link_overrides={},
        )

    def _get_macros(self, unit: Unit) -> dict[str, str]:
        flags = unit.all_flags

        macros = {**DEFAULT_MACROS}

        if flags.has_value(PATCHOULI_BOOK_JSON_FLAG):
            try:
                relative_path: Path = flags.get_value(PATCHOULI_BOOK_JSON_FLAG)
                repository: Repository = unit.translation.component.repository
                path = repository.path / relative_path
                if path.is_relative_to(repository.path) and path.is_file():
                    data = path.read_text(encoding="utf-8")
                    macros |= Book.model_validate_json(data).macros
            except ValueError as e:
                raise ValueError(f"Invalid book.json: {e}")

        if flags.has_value(PATCHOULI_MACROS_FLAG):
            try:
                flag_macros: list[str] = flags.get_value(PATCHOULI_MACROS_FLAG)
                macros |= dict(
                    flag_macros[pos : pos + 2] for pos in range(0, len(flag_macros), 2)
                )
            except ValueError:
                pass

        return macros


class Book(BaseModel):
    macros: dict[str, str] = Field(default_factory=dict)


class FakePluginManager:
    def validate_format_tree(self, tree: FormatTree, **kwargs: Any):
        return tree


@receiver(vcs_post_update)
def recheck_patchouli_formatting(
    component: Component,
    changed_files: list[str],
    **kwargs: Any,
):
    flags = component.all_flags

    if not flags.has_value(PATCHOULI_BOOK_JSON_FLAG):
        return

    try:
        path: Path = flags.get_value(PATCHOULI_BOOK_JSON_FLAG)
    except ValueError:
        return

    if str(path) in changed_files:
        component.schedule_update_checks()


def validate_relative_path(path: Path):
    if path.is_absolute():
        raise ValueError("Value must be a plain relative path")

    for value in ["..", "~", "*"]:
        if value in str(path):
            raise ValueError("Value must be a plain relative path")


# moved below PatchouliFormattingCheck to avoid circular imports
from weblate.checks.flags import TYPED_FLAGS, TYPED_FLAGS_ARGS
from weblate.checks.parser import multi_value_flag, single_value_flag

TYPED_FLAGS[PATCHOULI_MACROS_FLAG] = gettext_lazy("Patchouli macros")
TYPED_FLAGS_ARGS[PATCHOULI_MACROS_FLAG] = multi_value_flag(str, modulo=2)

TYPED_FLAGS[PATCHOULI_BOOK_JSON_FLAG] = gettext_lazy("Patchouli book.json path")
TYPED_FLAGS_ARGS[PATCHOULI_BOOK_JSON_FLAG] = single_value_flag(
    Path, validate_relative_path
)
