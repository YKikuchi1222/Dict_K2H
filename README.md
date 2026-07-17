# Dict_K2H

Generate an Apple text-replacement plist that maps Japanese dictionary terms to hiragana shortcuts.

This repository is intended to publish the generator script only. Do not publish source dictionary data or generated full-size dictionary outputs unless you have confirmed that their license permits redistribution.

## Recommended Source Database

Recommended input data:

- [LifeScienceDictionaries_J2E](https://pubdictionaries.org/dictionaries/LifeScienceDictionaries_J2E)

Check the source database license before downloading, transforming, or redistributing any data. This repository does not include that source database or generated full-size outputs.

## What The Script Does

`generate_lsd_j2j.py` reads a UTF-8 TSV file with a header and at least two columns:

- column 1: Japanese label or phrase
- column 2: identifier, gloss, or source term

It then:

- groups duplicate labels and preserves their identifiers in the review TSV
- generates hiragana shortcuts with SudachiPy full dictionary
- falls back to pykakasi when SudachiPy cannot provide a reading
- normalizes width and katakana-to-hiragana with jaconv
- expands Greek letters such as `α` to Japanese readings
- applies hard-coded domain corrections for known difficult terms
- applies manual override readings from a seed plist or override TSV
- writes an Apple plist with `phrase` and `shortcut` keys
- writes a full readings TSV for audit
- writes a review TSV for entries whose shortcut still contains CJK or katakana

The script does not call Ollama, OpenAI, or any remote API. The `--overrides-tsv` option only reads a local TSV file. `--llm-overrides` remains available as a backward-compatible alias, but no LLM control is implemented.

## Embedded Correction Tables

The script intentionally publishes small local correction tables:

- `PHRASE_OVERRIDES`: phrase-specific readings
- `READING_REPLACEMENTS`: generated-reading replacements
- `CJK_CHAR_READINGS`: fallback readings for difficult characters

These tables are part of the script, not generated dictionary data.

## Who Assigns Readings?

The first-pass reading assignment is the script's job. It uses SudachiPy, pykakasi, normalization, and local correction tables.

Final correctness is the maintainer's responsibility. Specialized terms can still be wrong, so review `Dict_K2H_review.tsv` and add corrections through `--overrides-tsv` or `--seed-plist`.

## Dependencies

Python 3.10 or newer is recommended. `uv` is the primary setup path for this repository.

Run with `uv`:

```sh
uv run dict-k2h \
  --csv examples/input_sample.tsv \
  --overrides-tsv examples/overrides_sample.tsv \
  --plist examples/output_sample.plist \
  --readings-tsv examples/output_readings.tsv \
  --review-tsv examples/output_review.tsv
```

For plain `pip`, install dependencies from `requirements.txt`:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

`SudachiDict-full` is required because the script creates SudachiPy with `Dictionary(dict="full")`.

## Usage

```sh
python generate_lsd_j2j.py \
  --csv examples/input_sample.tsv \
  --overrides-tsv examples/overrides_sample.tsv \
  --plist examples/output_sample.plist \
  --readings-tsv examples/output_readings.tsv \
  --review-tsv examples/output_review.tsv
```

Default paths are:

- input: `LifeScienceDictionaries_J2E.csv`
- plist output: `Dict_K2H.plist`
- audit TSV output: `Dict_K2H_readings.tsv`
- review TSV output: `Dict_K2H_review.tsv`

The default data/output filenames are ignored by git to avoid accidental publication of source or generated dictionary data.

## Input Example

See `examples/input_sample.tsv`:

```tsv
#label	id
試験管	test tube
試験管	test-tube
移動相	mobile phase
黄色相	yellow phase
α線	alpha ray
DNA	deoxyribonucleic acid
```

Manual reading overrides are optional. See `examples/overrides_sample.tsv`:

```tsv
phrase	shortcut
DNA	でぃーえぬえー
```

## Output Examples

The sample command writes:

- `examples/output_sample.plist`: Apple text replacement entries
- `examples/output_readings.tsv`: all generated readings and identifiers
- `examples/output_review.tsv`: entries that need manual review

The plist is an array of dictionaries:

```xml
<dict>
  <key>phrase</key>
  <string>試験管</string>
  <key>shortcut</key>
  <string>しけんかん</string>
</dict>
```
