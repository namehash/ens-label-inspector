import json
import regex
import itertools
from pathlib import Path
from argparse import ArgumentParser
from collections import defaultdict

import label_inspector.common.myunicode as myunicode
from label_inspector.common.myunicode.data import MY_UNICODE_DATA
from ens_normalize import ens_normalize, CurableSequence

from label_inspector.common.myunicode.emojis import emoji_char_iterator


PERSON = '🧑'
PEOPLE = '👩👨🧑👦👧👱🧔🧒'
SKIN_TONES = "🏻🏼🏽🏾🏿"
PROFESSION_MODIFIERS = "🎄⚕⚖✈🌾🍳🍼🎓🎤🎨🏫🏭💻💼🔧🔬🚀🚒🦯🦼🦽"
ZWJ_CHAR = "\u200d"

PROFESSION_CANONICAL_EMOJI = regex.compile(fr'{PERSON}{ZWJ_CHAR}({"|".join(PROFESSION_MODIFIERS)})')


def basename_preprocessing(basename: str):
    return basename \
        .replace('man and woman', '') \
        .replace('woman and man', '') \
        .replace('people', '') \
        .replace('woman', '') \
        .replace('women', '') \
        .replace('girl', '') \
        .replace('man', '') \
        .replace('men', '') \
        .replace('boy', '') \
        .replace('person', '') \
        .replace('child', '') \
        .replace('maid', '') \
        .strip()


def person_count(emoji: str) -> int:
    return sum([emoji.count(person) for person in PEOPLE], 0)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-o', required=False, default='',
                        help='filepath for the output JSON, if not specified - no file will be written')
    parser.add_argument('--show_aggregated', action='store_true', help='show emojis aggregated by basename')
    parser.add_argument('--show_with_canonical', action='store_true',
                        help='show emojis aggregated by basename with canonical selected')
    parser.add_argument('--ensure_ascii', action='store_true', help='make json with unicode codes, not explicit emojis')
    args = parser.parse_args()

    emoji_sequences = {
        ens_normalize(emoji): name.lower()
        for emoji, name in MY_UNICODE_DATA['emoji_sequences'].items()
        if ':' in name and 'flag' not in name.lower()
    }

    emoji_zwj_sequences = {
        ens_normalize(emoji): name.lower()
        for emoji, name in MY_UNICODE_DATA['emoji_zwj_sequences'].items()
    }

    # no handshake emoji?
    original_emojis = {}
    for emoji in emoji_char_iterator():
        try:
            original_emojis[ens_normalize(emoji)] = myunicode.emoji_name(emoji).lower()
        except ValueError:  # no name for emoji
            pass
        except CurableSequence:
            pass

    # aggregating emoji zwj sequences by basename
    same_basename = defaultdict(list)

    for seq, name in itertools.chain(original_emojis.items(), emoji_sequences.items(), emoji_zwj_sequences.items()):
        # for seq, name in itertools.chain(emoji_sequences.items()):
        basename = name.split(':')[0] if ':' in name else name
        basename = basename_preprocessing(basename)

        same_basename[basename].append(seq)

    for key in list(same_basename.keys()):
        if len(same_basename[key]) <= 1:
            del same_basename[key]

    if args.show_aggregated:
        print(json.dumps(same_basename, indent=2, ensure_ascii=False))

    # defining canonicals
    confusables: list[(str, list[str])] = []
    for emojis in same_basename.values():
        canonical = None
        emojis = list(emojis)

        # if both man and woman is in the emoji, then it's some kind of combination, no canonical
        if person_count(emojis[0]) <= 1:

            # if profession emojis, then the base emoji is the person connected with profession-specific emoji
            matches = [PROFESSION_CANONICAL_EMOJI.fullmatch(emoji) for emoji in emojis]
            if any(matches):
                canonical = [match.group(0) for match in matches if match][0]

            # if same base emoji, then we can assume it's canonical
            elif all(emoji[0] == emojis[0][0] for emoji in emojis):
                canonical = emojis[0][0]

            # if all base emojis are "person", "man" or "woman", then the canonical is "person"
            # still adding all the person emojis to the confusables themselves
            elif all(person_count(emoji[0]) == 1 for emoji in emojis):
                canonical = PERSON
                emojis.extend(set([emoji[0] for emoji in emojis]))

            if canonical is None:  # for e.g. handshake
                if emojis[0] in original_emojis and len([e for e in emojis if e in original_emojis]) == 1:
                    canonical = emojis[0]

            if canonical is not None:
                emojis.append(canonical)

        confusables.append((canonical, emojis))

    if args.show_with_canonical:
        print(json.dumps(confusables, indent=2, ensure_ascii=False))

    # formatting `confusables` in the `confusables.json` format
    all_confusable_emojis = dict()
    for canonical, confusable in confusables:
        for emoji in confusable:
            # using None as canonical for the canonical emoji (not itself)
            emoji_canonical = canonical if emoji != canonical else None
            if emoji_canonical is None:
                emoji_canonical = emoji

            if emoji not in all_confusable_emojis:
                all_confusable_emojis[emoji] = (emoji_canonical, sorted(set(confusable) - {emoji, emoji_canonical}))

            else:
                prev_canonical, prev_confusables = all_confusable_emojis[emoji]
                new_canonical = PERSON if prev_canonical == PERSON else prev_canonical
                all_confusable_emojis[emoji] = (new_canonical,
                                                sorted(set(prev_confusables + confusable) - {emoji, new_canonical}))

    if args.o:
        output = Path(args.o)
        output.parent.mkdir(exist_ok=True)
        with output.open('w', encoding='utf-8') as f:
            json.dump(all_confusable_emojis, f, indent=2, ensure_ascii=False, sort_keys=True)
