# NameHash Label Inspector

This is additional documentation for maintainers.

## Updating

> **IMPORTANT** Regenerate cache after updating!

```bash
python namehash_common/generate_cache.py
```

### Dependencies

To update dependencies, modify package versions in `pyproject.toml` and run:

```bash
poetry update
```

### Unicode

When a new Unicode version is released, you should update character data by running:

```bash
UNICODE_VERSION=15.1.0 ./download_latest_data.sh
```

Replace `15.1.0` with the latest **official** unicode version (not a draft).
You can also specify an older version.
The script will download:

- list of confusable characters from <https://www.unicode.org/Public/security/latest/> into `inspector_data/inspector/confusables.json`
- latest character data from <https://www.unicode.org/Public/UNIDATA/> into `myunicode/myunicode.json`
- test data for numeric characters from <https://www.unicode.org/Public/UNIDATA/> into `tests/data/unicode_numerics.txt`

You can then inspect and commit the changes with git.

## Tests

Run:

```bash
pytest
```

or without slow tests:

```bash
pytest -m "not slow"
```

## Dictionaries

LabelInspector tokenizes labels using a dictionary. The dictionary is built:

1. All tokens from `inspector_data/words.txt` longer than 3 characters.
2. All tokens from `inspector_data/custom_dictionary.txt`.

Calculation of probabilities is performed using ngram language model.

1. `inspector_data/inspector/bigram_freq.csv` - for bigrams
2. `inspector_data/inspector/unigram_freq.csv` - for unigrams. Counts for tokens from `inspector_data/custom_dictionary.txt`, which are not present in unigrams, are set to value defined in config by `inspector.custom_token_frequency: 500000`.
