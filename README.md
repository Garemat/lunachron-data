# moonstone-companion-data

Data repository for the [moonstone-companion](https://github.com/Garemat/moonstone-companion) app. Character, upgrade, and campaign card JSON files are aggregated into a versioned `compendium.json` release artifact consumed by the app at build time.

Character portrait images are bundled as a separate `character_images.zip` artifact and are an optional download within the app. Head/portrait icons for all 133 characters are included.

Soon to be hosted by DB backend
---

## Local Development

**Prerequisites**

- Python 3.8+
- Node.js 20+ and npm

**Setup**

```bash
git clone https://github.com/Garemat/moonstone-companion-data.git
cd moonstone-companion-data
npm install        # installs Prettier, husky, lint-staged and wires up pre-commit hooks
```

**Validate your changes**

```bash
python3 scripts/aggregate.py     # builds build/compendium.json from source files
python3 scripts/lint_data.py     # validates structure, share codes, and faction data
```

Both steps run automatically as a pre-commit hook — you don't need to run them manually before committing.

**Testing against a local app build**

Symlink the `build/` folder to the app's assets directory so the app picks up your local compendium at build time without downloading a release:

```bash
ln -sf $(pwd)/build/compendium.json \
  ../moonstone-companion/app/src/main/assets/compendium.json
```

---

## Contributing

1. Create a branch from `main`
2. Make your changes to the relevant JSON files
3. Run `npm install` if you haven't already — this wires up the pre-commit hooks
4. Commit your changes — the hooks will auto-format JSON with Prettier and validate the full dataset before the commit completes
5. Open a PR against `main` and fill in the PR template

**Share codes are auto-generated — do not edit them manually.** Run `python3 scripts/generate_share_codes.py` if you add a new item or change its faction, then commit the updated file. The lint step will catch any mismatches.

**JSON formatting is enforced by Prettier.** Run `npx prettier --write "**/*.json"` to fix formatting, or let the pre-commit hook do it automatically on staged files.

---

## Share Code Format

Every compendium item has a stable 5-character `shareCode` field used for troupe sharing, import/export, and multiplayer sync.

| Position | Meaning | Values |
|----------|---------|--------|
| 1 | Type | `A` = Character, `B` = Campaign card, `C` = Upgrade card |
| 2 | Faction | `A`–`D` single faction, `E`–`J` dual faction, `K` = all four |
| 3–5 | ID | 3-digit decimal ID, each digit encoded `A`=0 … `J`=9 |

**Faction codes**

| Code | Factions |
|------|----------|
| `A` | Commonwealth |
| `B` | Dominion |
| `C` | Leshavult |
| `D` | Shades |
| `E` | Commonwealth + Dominion |
| `F` | Commonwealth + Leshavult |
| `G` | Commonwealth + Shades |
| `H` | Dominion + Leshavult |
| `I` | Dominion + Shades |
| `J` | Leshavult + Shades |
| `K` | All four factions |

**Examples**

| Item | ID | Factions | Share Code |
|------|----|----------|------------|
| Baron Von Fancyhat | 1 | Commonwealth | `AAAAB` |
| Boris | 64 | Commonwealth + Leshavult | `AFAGE` |
| Nordic Tattoos | 34 | Commonwealth + Shades | `CGADE` |
| Birthright | 1 | Commonwealth + Dominion | `BEAAB` |

---

## Campaign JSON

```json
{
  "id": 1,
  "name": "Card Name",
  "version": 2,
  "factions": ["COMMONWEALTH"],
  "tags": [],
  "timing": "Play during the Activation Step, before or after any action.",
  "description": "Rules text.",
  "shareCode": "BEAAB",
  "imageName": "card_name"
}
```

## Upgrade JSON

```json
{
  "id": 1,
  "name": "Upgrade Name",
  "version": 1,
  "factions": ["COMMONWEALTH"],
  "allowedKeywords": [],
  "restrictedKeywords": [],
  "extraDescription": "This character gains the Pirate keyword.",
  "abilities": [],
  "shareCode": "CAAAB",
  "imageName": "upgrade_name"
}
```

## Character JSON Template

Each character lives in `characters/{faction}/{id}_{name}.json`. All fields are required unless noted.

```json
{
  "id": 0,
  "name": "Character Name",
  "version": 1,
  "factions": ["COMMONWEALTH"],
  "health": 8,
  "energyTrack": [1, 3, 6],
  "keywords": ["Human"],
  "melee": 3,
  "meleeRange": 1,
  "arcane": 3,
  "evade": 0,
  "baseSize": "30mm",
  "imageName": "character_name",
  "shareCode": "AAAAA",
  "slicingDamageBuff": 0,
  "piercingDamageBuff": 0,
  "impactDamageBuff": 0,
  "dealsMagicalDamage": false,
  "allDamageMitigation": 0,
  "piercingDamageMitigation": 0,
  "impactDamageMitigation": 0,
  "slicingDamageMitigation": 0,
  "magicalDamageMitigation": 0,
  "summonsCharacterIds": [],
  "isUnselectableInTroupe": false,
  "signatureMove": {
    "name": "Sig Move Name",
    "upgradeFor": "High Guard",
    "possibleDamageTypes": ["Slicing"],
    "highGuard": { "deal": "2", "isFollowUp": false },
    "fallingSwing": { "deal": "1", "isFollowUp": false },
    "thrust": { "deal": "2", "isFollowUp": false },
    "sweepingCut": { "deal": "Null", "isFollowUp": false },
    "risingAttack": { "deal": "1", "isFollowUp": true },
    "lowGuard": { "deal": "Null", "isFollowUp": false },
    "extraText": "Any rules text that applies during the melee round (not at End Step).",
    "endStepEffect": "Any End Step Effect text, or empty string if none."
  },
  "abilities": [
    {
      "name": "Passive Ability Name",
      "description": "Full rules text.",
      "abilityType": "Passive",
      "oncePerTurn": false,
      "oncePerGame": false,
      "arcaneOutcomes": []
    },
    {
      "name": "Active Ability Name",
      "description": "Full rules text.",
      "abilityType": "Active",
      "energyCost": 2,
      "range": "6\"",
      "pulse": false,
      "oncePerTurn": false,
      "oncePerGame": false,
      "arcaneOutcomes": []
    },
    {
      "name": "Arcane Ability Name",
      "description": "Any general rules text not tied to a specific card outcome (or empty string).",
      "abilityType": "Arcane",
      "energyCost": 2,
      "range": "8\"",
      "pulse": false,
      "oncePerTurn": false,
      "oncePerGame": false,
      "arcaneOutcomes": [
        {
          "text": "Effect when a matching card is flipped.",
          "validCards": [{ "colour": "Pink", "value": "X" }]
        },
        {
          "text": "Effect for a fixed-value outcome.",
          "validCards": [
            { "colour": "Green", "value": "2" },
            { "colour": "Blue", "value": "2" },
            { "colour": "Pink", "value": "2" }
          ]
        },
        {
          "text": "This character suffers 3 Wds.",
          "validCards": [{ "colour": "Catastrophe", "value": "X" }]
        }
      ]
    }
  ]
}
```

### Field Notes

| Field | Notes |
|-------|-------|
| `factions` | `"COMMONWEALTH"`, `"DOMINION"`, `"LESHAVULT"`, `"SHADES"`. Multiple for dual-faction. |
| `energyTrack` | Starting energy positions, e.g. `[1, 3, 6]`. Use `[999]` for characters that can never gain energy (Thralls, Echo). |
| `meleeRange` | Numeric inches only, e.g. `1` for 1", `2` for 2". |
| `imageName` | Snake_case name without ID prefix or extension, e.g. `"old_polly"`. |
| `slicingDamageBuff` | Net passive bonus to Slicing melee damage output. `null` for null values. |
| `dealsMagicalDamage` | `true` only if base melee attacks are Magical. |
| `allDamageMitigation` | Use when a passive reduces ALL damage types. Individual fields cover specific types. |
| `summonsCharacterIds` | IDs of characters this model can place/summon via abilities. |
| `isUnselectableInTroupe` | `true` for Thralls and summoned-only characters. |
| `signatureMove` | `null` for characters with no signature move (Thralls, summoned creatures). |
| `deal` | `"Null"` (string) = Ø, `"0"` = zero damage, `"1"`–`"4"` = damage value. |
| `isFollowUp` | `true` = amber circle in PDF table (follow-up hit). |
| `possibleDamageTypes` | `[]` if sig deals no damage or damage type is unspecified. Multiple entries allowed e.g. `["Slicing", "Magical"]`. |
| `abilityType` | `"Passive"`, `"Active"`, or `"Arcane"`. Active and Arcane both require `energyCost`, `range`, `pulse`. |
| `validCards` colours | `"Green"`, `"Blue"`, `"Pink"`, `"Catastrophe"`. |
| `validCards` value | `"X"` for variable-value outcomes; `"1"`, `"2"`, `"3"` etc. for fixed-value outcomes (any colour at that value). |
| `transformsInto` | ID of the character this model transforms into (currently unique to Anya). |
| `shareCode` | Auto-generated — run `python3 scripts/generate_share_codes.py` after adding or changing a character's faction. |

---

# License & Attribution

This project uses assets from Goblin King Games' publicly available store and website. These assets are provided for non-commercial use only and must remain free to use. Please credit Goblin King Games when using these assets.
