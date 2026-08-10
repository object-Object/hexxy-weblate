import re
from typing import IO, BinaryIO, TextIO, cast

import json5
from translate.storage.base import ParseError, UnitId
from translate.storage.jsonl10n import BaseJsonUnit, FlatUnitId, JsonFile

type JSONValue = JSONDict | JSONList | str | int | float | bool | None
type JSONDict = dict[str, JSONValue]
type JSONList = list[JSONValue]


class Json5Unit(BaseJsonUnit):
    def __str__(self):
        return json5.dumps(
            self.getvalue(),
            separators=(",", ": "),
            indent=2,
            ensure_ascii=False,
        )


class Json5File(JsonFile[Json5Unit]):
    """Largely copied from JsonFile, replacing json with json5"""

    UnitClass = Json5Unit

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.dump_args["indent"] = 2

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


class BasePKPCPBPJson5File(Json5File):
    # replace `\<LF>       foobar` with `\<LF>foobar`
    _newline_pattern = re.compile(r"\\\n\s*")

    def preprocess_input(self, text: str):
        return self._newline_pattern.sub("\\\n", text)


class PKPCPBPJson5Unit(Json5Unit):
    IdClass = FlatUnitId


class PKPCPBPJson5File(BasePKPCPBPJson5File):
    UnitClass = PKPCPBPJson5Unit

    def _extract_units(
        self,
        data,
        stop=None,
        prev=None,
        name_node=None,
        name_last_node=None,
        last_node=None,
    ):
        return super()._extract_units(
            self._flatten_inner(data, "") if isinstance(data, dict) else data,
            stop,
            prev,
            name_node,
            name_last_node,
            last_node,
        )

    # https://github.com/hexdoc-dev/hexdoc/blob/e37c5d449995dd1f84b43079b91dfcca78a6fdde/src/hexdoc/utils/deserialize/json.py#L35
    def _flatten_inner(self, obj: JSONDict, prefix: str) -> dict[str, str]:
        out: dict[str, str] = {}

        for key_stub, value in obj.items():
            if not prefix:
                key = key_stub
            elif not key_stub:
                key = prefix
            elif prefix[-1] in MERGE_CHARS:
                key = prefix + key_stub
            else:
                key = f"{prefix}.{key_stub}"

            match value:
                case dict():
                    self._update_disallow_duplicates(
                        out, self._flatten_inner(value, key)
                    )
                case str():
                    self._update_disallow_duplicates(out, {key: value})
                case _:
                    raise ParseError(
                        f"File is not a valid PKPCPBP JSON5 file: expected dict or string, got {type(value)}"
                    )

        return out

    def _update_disallow_duplicates[T](self, base: dict[str, T], new: dict[str, T]):
        for key, value in new.items():
            if key in base:
                raise ParseError(
                    ValueError(f"Duplicate key {key}\nold=`{base[key]}`\nnew=`{value}`")
                )
            base[key] = value


class PKPCPBPJson5NestedUnitId(UnitId):
    def __str__(self) -> str:
        parts = [""]
        part = None
        for element, key in self.parts:
            if element != "key":
                raise ValueError(f"Unsupported element: {element}")
            if part:
                part += key
            else:
                part = key
            if part and part[-1] not in MERGE_CHARS:
                parts.append(part)
                part = None
        if part:
            parts.append(part)
        return self.KEY_SEPARATOR.join(parts)

    def __eq__(self, other: object):
        return isinstance(other, PKPCPBPJson5NestedUnitId) and str(self) == str(other)


class PKPCPBPJson5NestedUnit(Json5Unit):
    IdClass = PKPCPBPJson5NestedUnitId


class PKPCPBPJson5NestedFile(BasePKPCPBPJson5File):
    UnitClass = PKPCPBPJson5NestedUnit


# https://github.com/gamma-delta/PKPCPBP/blob/786194a590f/src/main/java/at/petrak/pkpcpbp/filters/JsonUtil.java
MERGE_CHARS = ":_-/"
