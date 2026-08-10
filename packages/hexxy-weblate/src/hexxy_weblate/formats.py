from django.utils.translation import gettext_lazy
from translation_finder.api import register_discovery
from translation_finder.discovery.base import BaseDiscovery
from weblate.formats.ttkit import JSONFormat, JSONUnit

from hexxy_weblate.json5l10n import (
    Json5File,
    Json5Unit,
    PKPCPBPJson5File,
    PKPCPBPJson5NestedFile,
)


class JSON5Format(JSONFormat[Json5File, Json5Unit, JSONUnit]):
    name = gettext_lazy("JSON5 file")
    format_id = "json5"
    loader = Json5File
    autoload = ("*.json5",)
    has_hierarchical_contexts = True

    @staticmethod
    def extension():
        return "json5"


@register_discovery
class JSON5Discovery(BaseDiscovery):
    file_format = "json5"
    mask = "*.json5"


class PKPCPBPJSON5Format(JSON5Format):
    name = gettext_lazy("PKPCPBP JSON5 flattened file")
    format_id = "pkpcpbp-json5"
    loader = PKPCPBPJson5File
    autoload = ("*.flatten.json5",)
    has_hierarchical_contexts = False


@register_discovery
class PKPCPBPJSON5Discovery(BaseDiscovery):
    file_format = "pkpcpbp-json5"
    mask = "*.flatten.json5"


class PKPCPBPJSON5NestedFormat(JSON5Format):
    name = gettext_lazy("PKPCPBP JSON5 nested structure file")
    format_id = "pkpcpbp-json5-nested"
    loader = PKPCPBPJson5NestedFile
    autoload = ()


@register_discovery
class PKPCPBPJSON5NestedDiscovery(BaseDiscovery):
    file_format = "pkpcpbp-json5-nested"
    mask = "*.flatten.json5"
