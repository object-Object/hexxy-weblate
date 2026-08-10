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
