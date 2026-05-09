#!/usr/bin/env python3
"""
Compare local character JSON files against a dump of the moontome.com IndexedDB.

Usage:
    python3 scripts/compare_db.py moonstone_db.json [--auto-fix] [--fix-all]

The dump file is produced by pasting scripts/dump_indexeddb.js into the browser
console while on https://app.moontome.com/Compendium.

--auto-fix   Writes corrected description text back to local files only.
             Safe to run; review the diff afterwards.

--fix-all    Also fixes abilityType inference, oncePerTurn/oncePerGame/pulse,
             range, and arcane outcome card colours in addition to descriptions.
"""

import json
import pathlib
import re
import sys

CHARACTERS_DIR = pathlib.Path(__file__).parent.parent / "characters"

# Colour integer from DB → local colour string
COLOUR_MAP = {
    1: "Green",
    2: "Blue",
    4: "Pink",
}


def normalise_name(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip()).lower()


# Normalise a description string before comparing so cosmetic differences are ignored.
# - collapse whitespace / newlines
# - convert curly/smart quotes to straight equivalents
# - treat standalone 'W' (null-damage symbol in DB) as '{Null}'
_QUOTE_TABLE = str.maketrans({"“": '"', "\"": '"', "‘": "'", "’": "'"})

def normalise_desc(s: str) -> str:
    s = " ".join(s.split())
    s = s.translate(_QUOTE_TABLE)
    s = re.sub(r'\bW\b', '{Null}', s)
    return s


def bool_val(v) -> bool:
    """Treat None and False as equivalent."""
    return bool(v)


def infer_ability_type(db_ab: dict) -> str:
    if db_ab.get("energyCost") is None:
        return "Passive"
    if any(not o.get("catastropheOutcome", False) for o in db_ab.get("arcaneOutcomes", [])):
        return "Arcane"
    return "Active"


def db_colours_for_outcome(db_outcome: dict) -> list[str]:
    """Return local-style colour strings for one non-catastrophe DB outcome."""
    return [
        COLOUR_MAP.get(req["colour"], f"UNKNOWN({req['colour']})")
        for req in db_outcome.get("cardRequirements", [])
    ]


def load_db_models(path: str) -> dict[str, dict]:
    """Return {normalised_name: model} from the IndexedDB dump."""
    raw = json.loads(pathlib.Path(path).read_text())
    models: list[dict] = []
    if isinstance(raw, list):
        models = raw
    else:
        for v in raw.values():
            if isinstance(v, list) and v and isinstance(v[0], dict) and "moonstoneModelId" in v[0]:
                models = v
                break
    return {normalise_name(m["name"]): m for m in models}


def load_local_files() -> dict[str, tuple[pathlib.Path, dict]]:
    """Return {normalised_name: (path, data)} for every character JSON."""
    result: dict[str, tuple[pathlib.Path, dict]] = {}
    for p in sorted(CHARACTERS_DIR.rglob("*.json")):
        try:
            data = json.loads(p.read_text())
        except json.JSONDecodeError:
            print(f"WARN: could not parse {p}")
            continue
        name = data.get("name")
        if name:
            result[normalise_name(name)] = (p, data)
    return result


def diff_abilities(local_abs: list, db_abs: list) -> list[str]:
    diffs: list[str] = []
    db_by_name = {normalise_name(a["name"]): a for a in db_abs}

    for la in local_abs:
        aname = la["name"]
        da = db_by_name.get(normalise_name(aname))
        if da is None:
            diffs.append(f"  ability '{aname}': not found in DB (may be renamed)")
            continue

        # description — DB has it for Passive/Active; null for Arcane
        db_desc = normalise_desc(da.get("description") or "")
        local_desc = normalise_desc(la.get("description") or "")
        if db_desc and db_desc != local_desc:
            diffs.append(f"  ability '{aname}' description mismatch:")
            diffs.append(f"    local: {local_desc!r}")
            diffs.append(f"    db:    {db_desc!r}")

        # abilityType inferred from DB data
        inferred = infer_ability_type(da)
        local_type = la.get("abilityType")
        if local_type != inferred:
            diffs.append(f"  ability '{aname}' abilityType: local={local_type!r}  db-inferred={inferred!r}")

        # scalar flags — energyCost is exact; booleans treat None == False
        dv = da.get("energyCost")
        lv = la.get("energyCost")
        if dv != lv:
            diffs.append(f"  ability '{aname}' energyCost: local={lv!r}  db={dv!r}")
        for field in ("oncePerTurn", "oncePerGame", "pulse"):
            dv = da.get(field)
            lv = la.get(field)
            if bool_val(dv) != bool_val(lv):
                diffs.append(f"  ability '{aname}' {field}: local={lv!r}  db={dv!r}")

        # range (DB: int or null, local: '4"' or '' or null)
        db_range = da.get("range")
        local_range = la.get("range")
        if db_range is not None:
            expected = f'{db_range}"'
            if local_range != expected:
                diffs.append(f"  ability '{aname}' range: local={local_range!r}  db={expected!r}")
        elif local_range not in ("", None):
            diffs.append(f"  ability '{aname}' range: local={local_range!r}  db=null")

        # arcane outcome card colours — only for non-catastrophe outcomes
        db_normal = [o for o in da.get("arcaneOutcomes", []) if not o.get("catastropheOutcome", False)]
        db_cat = [o for o in da.get("arcaneOutcomes", []) if o.get("catastropheOutcome", False)]
        local_normal = [o for o in la.get("arcaneOutcomes", []) if o.get("validCards", [{}])[0].get("colour") != "Catastrophe"]
        local_cat = [o for o in la.get("arcaneOutcomes", []) if o.get("validCards", [{}])[0].get("colour") == "Catastrophe"]

        if len(db_normal) != len(local_normal):
            diffs.append(
                f"  ability '{aname}' non-catastrophe arcaneOutcomes count:"
                f" local={len(local_normal)}  db={len(db_normal)}"
            )
        else:
            for i, (lo, do) in enumerate(zip(local_normal, db_normal)):
                local_colours = [c.get("colour") for c in lo.get("validCards", [])]
                db_colours = db_colours_for_outcome(do)
                if local_colours != db_colours:
                    diffs.append(
                        f"  ability '{aname}' outcome[{i}] card colours:"
                        f" local={local_colours}  db={db_colours}"
                    )

        has_db_cat = len(db_cat) > 0
        has_local_cat = len(local_cat) > 0
        if has_db_cat != has_local_cat:
            diffs.append(
                f"  ability '{aname}' catastrophe outcome:"
                f" local={'yes' if has_local_cat else 'no'}  db={'yes' if has_db_cat else 'no'}"
            )

    # abilities in DB but not locally
    local_names = {normalise_name(a["name"]) for a in local_abs}
    for da in db_abs:
        if normalise_name(da["name"]) not in local_names:
            diffs.append(f"  ability '{da['name'].strip()}': present in DB but missing locally")

    return diffs


def apply_fixes(local_data: dict, db_model: dict, fix_all: bool = False) -> bool:
    """Mutate local_data in-place. Returns True if changed.

    Always fixes: description text (Passive/Active only).
    With fix_all: also fixes abilityType, boolean flags, range, card colours.
    """
    changed = False
    db_by_name = {normalise_name(a["name"]): a for a in db_model.get("abilities", [])}

    for la in local_data.get("abilities", []):
        da = db_by_name.get(normalise_name(la["name"]))
        if da is None:
            continue

        db_desc = normalise_desc(da.get("description") or "")
        local_desc = normalise_desc(la.get("description") or "")
        if db_desc and db_desc != local_desc:
            # Store the DB version verbatim (whitespace collapsed, quotes as-is from DB)
            la["description"] = " ".join((da.get("description") or "").split())
            changed = True

        if not fix_all:
            continue

        inferred = infer_ability_type(da)
        if la.get("abilityType") != inferred:
            la["abilityType"] = inferred
            changed = True

        for field in ("oncePerTurn", "oncePerGame", "pulse"):
            if field in da and bool_val(la.get(field)) != bool_val(da[field]):
                la[field] = da[field]
                changed = True

        db_range = da.get("range")
        if db_range is not None:
            expected = f'{db_range}"'
            if la.get("range") != expected:
                la["range"] = expected
                changed = True

        db_normal = [o for o in da.get("arcaneOutcomes", []) if not o.get("catastropheOutcome", False)]
        local_normal = [o for o in la.get("arcaneOutcomes", []) if o.get("validCards", [{}])[0].get("colour") != "Catastrophe"]
        if len(db_normal) == len(local_normal):
            for lo, do in zip(local_normal, db_normal):
                db_colours = db_colours_for_outcome(do)
                local_cards = lo.get("validCards", [])
                if len(local_cards) == len(db_colours):
                    for card, colour in zip(local_cards, db_colours):
                        if card.get("colour") != colour:
                            card["colour"] = colour
                            changed = True

    return changed


def main() -> None:
    args = sys.argv[1:]
    auto_fix = "--auto-fix" in args or "--fix-all" in args
    fix_all = "--fix-all" in args
    db_paths = [a for a in args if not a.startswith("--")]

    if not db_paths:
        print("Usage: compare_db.py <moonstone_db.json> [--auto-fix | --fix-all]")
        sys.exit(1)

    db_models = load_db_models(db_paths[0])
    local_files = load_local_files()

    print(f"DB models: {len(db_models)}   Local files: {len(local_files)}\n")

    total_diffs = 0
    for norm_name, (path, local_data) in sorted(local_files.items(), key=lambda x: x[1][1].get("id", 0)):
        db_model = db_models.get(norm_name)
        if db_model is None:
            print(f"  {local_data.get('name','?')} — not found in DB dump (check name spelling)")
            continue

        diffs = diff_abilities(
            local_data.get("abilities", []),
            db_model.get("abilities", []),
        )

        if diffs:
            total_diffs += len(diffs)
            cid = local_data.get("id", "?")
            print(f"[{cid:>3}] {local_data.get('name','?')}  ({path.relative_to(CHARACTERS_DIR.parent)})")
            for d in diffs:
                print(d)
            print()

            if auto_fix:
                fixed = apply_fixes(local_data, db_model, fix_all=fix_all)
                if fixed:
                    path.write_text(json.dumps(local_data, indent=2, ensure_ascii=False) + "\n")
                    print(f"  -> auto-fixed and saved\n")

    if total_diffs == 0:
        print("No differences found.")
    else:
        print(f"Total: {total_diffs} difference(s) across {len(local_files)} files.")
        if not auto_fix:
            print("Re-run with --auto-fix to fix descriptions, or --fix-all to also fix types/flags/colours.")


if __name__ == "__main__":
    main()
