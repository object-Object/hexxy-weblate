from typing import IO, BinaryIO, TextIO, cast

import json5
from django.utils.translation import gettext_lazy
from translate.storage.base import ParseError
from translate.storage.jsonl10n import BaseJsonUnit, JsonFile
from translation_finder.api import register_discovery
from translation_finder.discovery.base import BaseDiscovery
from weblate.formats.ttkit import JSONFormat, JSONUnit


class Json5Unit(BaseJsonUnit):
    def __str__(self):
        return json5.dumps(
            self.getvalue(),
            separators=(",", ": "),
            indent=4,
            ensure_ascii=False,
        )


class Json5File(JsonFile[Json5Unit]):
    """Largely copied from JsonFile, replacing json with json5"""

    UnitClass = Json5Unit

    def serialize(self, out: IO[bytes]):
        units = self.get_root_node()
        self.serialize_units(units)
        out.write(json5.dumps(units, **self.dump_args).encode(self.encoding))
        out.write(b"\n")

    def parse(self, data: str | bytes | TextIO | BinaryIO):
        text: str | bytes
        if hasattr(data, "name"):
            self.filename = data.name  # type: ignore
        elif not getattr(self, "filename", ""):
            self.filename = ""
        if hasattr(data, "read"):
            # Make type checking happy
            data = cast("BinaryIO", data)

            text = data.read()
            data.close()
        else:
            text = data  # type: ignore

        if isinstance(text, bytes):
            # The JSON files should be UTF-8, but implementations
            # that parse JSON texts MAY ignore the presence of a byte order mark
            # rather than treating it as an error, see RFC7159
            decoded, self.encoding = self.detect_encoding(text)
            if decoded is None:
                raise ParseError(ValueError("Failed to decode JSON5 string."))
            text = decoded
        text = self.preprocess_input(text)
        try:
            self._file = json5.loads(text)
        except ValueError as e:
            raise ParseError(e) from e

        for unit in self._extract_units(self._file, stop=self._filter):
            self.addunit(unit)


class JSON5Unit(JSONUnit):
    pass


class JSON5Format(JSONFormat[Json5File, Json5Unit, JSON5Unit]):
    name = gettext_lazy("JSON5 file")
    format_id = "json5"
    loader = Json5File
    unit_class = JSON5Unit
    autoload = ("*.json5",)
    has_hierarchical_contexts = True

    @staticmethod
    def extension():
        return "json5"


@register_discovery
class JSON5Discovery(BaseDiscovery):
    file_format = "json5"
    mask = "*.json5"
