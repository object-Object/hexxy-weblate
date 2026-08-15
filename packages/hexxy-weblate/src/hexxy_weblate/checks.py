from __future__ import annotations

from typing import override

from django.utils.html import format_html
from django.utils.translation import gettext, gettext_lazy
from git import TYPE_CHECKING
from weblate.checks.base import TargetCheck
from weblate.utils.html import format_html_join_comma

from hexxy_weblate.utils.patchouli import DEFAULT_MACROS, FormatTree

if TYPE_CHECKING:
    from weblate.checks.models import Check
    from weblate.trans.models import Unit

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
            FormatTree.format(target, macros=DEFAULT_MACROS | self._get_macros(unit))
            return None
        except Exception as e:  # noqa: BLE001
            return str(e)

    @override
    def get_description(self, check_obj: Check) -> str:
        messages = set[str]()
        unit = check_obj.unit
        source = unit.source_string
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

    def _get_macros(self, unit: Unit) -> dict[str, str]:
        flags = unit.all_flags

        if not flags.has_value(PATCHOULI_MACROS_FLAG):
            return {}

        try:
            macros: list[str] = flags.get_value(PATCHOULI_MACROS_FLAG)
        except ValueError:
            return {}

        return dict(macros[pos : pos + 2] for pos in range(0, len(macros), 2))


# moved below PatchouliFormattingCheck to avoid circular imports
from weblate.checks.flags import TYPED_FLAGS, TYPED_FLAGS_ARGS
from weblate.checks.parser import multi_value_flag

TYPED_FLAGS[PATCHOULI_MACROS_FLAG] = gettext_lazy("Patchouli macros")
TYPED_FLAGS_ARGS[PATCHOULI_MACROS_FLAG] = multi_value_flag(str, modulo=2)
