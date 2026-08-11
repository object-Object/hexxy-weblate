import csv
import re
from collections.abc import Iterable
from importlib import resources

from typer import Typer
from weblate_language_data.aliases import ALIASES
from weblate_language_data.languages import LANGUAGES

app = Typer(pretty_exceptions_show_locals=False)

note_pattern = re.compile(r"\[[^\]]+\]")


@app.command()
def minecraft_languages():
    """Generates a Weblate language alias string for all Minecraft languages."""
    csv_file = resources.files("hexxy_weblate_scripts") / "minecraft_languages.csv"
    with csv_file.open("r") as f:
        reader = csv.reader(
            [
                note_pattern.sub("", line)
                for line in f.readlines()
                if not line.startswith("#")
            ][1:],
            delimiter="\t",
        )

    weblate_codes = dict[str, str]()
    for minecraft_code, weblate_code in iter_codes(reader):
        if duplicate_code := weblate_codes.get(weblate_code):
            print(
                f"Duplicate code: {weblate_code} ({minecraft_code}, {duplicate_code})"
            )
        else:
            weblate_codes[weblate_code] = minecraft_code

    print()
    print(
        ",".join(
            sorted(
                f"{minecraft_code}:{weblate_code}"
                for weblate_code, minecraft_code in weblate_codes.items()
            )
        )
    )


def iter_codes(reader: Iterable[list[str]]):
    for language, minecraft_code, code in reader:
        if minecraft_code in IGNORED_MINECRAFT_CODES:
            continue

        if weblate_code_lower := try_get_code(minecraft_code, code):
            weblate_code, weblate_name = WEBLATE_LANGUAGES[weblate_code_lower.lower()]
            if language != weblate_name:
                print(
                    f"{language} ({minecraft_code})\t->\t{weblate_name} ({weblate_code})"
                )
            yield minecraft_code, weblate_code
            continue

        print(f"FAILED: {language} ({minecraft_code=}, {code=})")


def try_get_code(minecraft_code: str, code: str):
    minecraft_code = normalize_code(minecraft_code)
    code = normalize_code(code)

    if weblate_code := try_get_single_code(minecraft_code):
        return weblate_code

    if weblate_code := try_get_single_code(code):
        return weblate_code

    for part in code.split("_"):
        if weblate_code := try_get_single_code(part):
            return weblate_code


def try_get_single_code(code: str):
    if code in WEBLATE_LANGUAGES:
        return code

    if weblate_code := CUSTOM_ALIASES.get(code):
        return weblate_code


def normalize_code(code: str):
    return code.lower().replace("-", "_")


CUSTOM_ALIASES = {
    "en_pt": "en@pirate",  # Pirate English
    "zlm_arab": "ms_Arab",  # Malay (Jawi)
    "ms_my": "ms",
    "sr_cs": "sr_Latn",
    "sr_sp": "sr_Cyrl",
} | ALIASES


IGNORED_MINECRAFT_CODES = {
    "brb",
    "en_ud",
    "enp",
    "enws",
    "esan",
    "go_fr",
    "lol_us",
    "fra_de",
    "hal_ua",
    "hn_no",
    "pls",
    "qcb_es",
    "qid",
    "rpr",
    "tzo_mx",
}

WEBLATE_LANGUAGES = {code.lower(): (code, name) for code, name, _, _ in LANGUAGES}


if __name__ == "__main__":
    app()
