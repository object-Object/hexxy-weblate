import pytest
from hexxy_weblate.json5l10n import PKPCPBPJson5NestedFile

TEST_DATA = b"""{
  foo: "0",
  bar: {
    foo: "1",
  },
  baz_: {
    "": "2",
    qux: "3",
    "quux:": {
      foobar: "4",
      "quuux:": {
        "": "5",
      },
    },
  },
  "a.b": {
    c: "6",
  },
}
"""


def test_keys():
    store = PKPCPBPJson5NestedFile()
    store.parse(TEST_DATA)

    assert [unit.getid() for unit in store.units] == [
        ".foo",
        ".bar.foo",
        ".baz_",
        ".baz_qux",
        ".baz_quux:foobar",
        ".baz_quux:quuux:",
        ".a.b.c",
    ]


def test_roundtrip():
    store = PKPCPBPJson5NestedFile()
    store.parse(TEST_DATA)
    assert bytes(store).decode() == TEST_DATA.decode()


@pytest.mark.parametrize(
    ["data", "expected"],
    [
        (
            b'{foo:"bar \\\n  baz"}',
            '{\n  foo: "bar baz",\n}\n',
        ),
        (
            b'{foo:"bar \\\r\n  baz"}',
            '{\n  foo: "bar baz",\n}\n',
        ),
    ],
)
def test_backslash(data: bytes, expected: str):
    store = PKPCPBPJson5NestedFile()
    store.parse(data)
    assert bytes(store).decode() == expected
