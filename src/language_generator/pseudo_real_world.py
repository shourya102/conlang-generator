import copy
import importlib
import re
from collections import Counter

from src.language_generator.defaults import (
    DEFAULT_GRAMMAR_PARAMS,
    DEFAULT_MORPHOLOGY_PARAMS,
    DEFAULT_NAMEGEN_PARAMS,
    DEFAULT_PHONOLOGY_PARAMS,
    DEFAULT_SOUND_CHANGE_RULES,
    DEFAULT_WORDGEN_PARAMS,
    deep_merge,
)

try:
    top_n_list = importlib.import_module('wordfreq').top_n_list
except ImportError:
    top_n_list = None

try:
    unidecode = importlib.import_module('unidecode').unidecode
except ImportError:
    def unidecode(value):
        return value


VOWEL_TOKENS = {
    'a', 'e', 'i', 'o', 'u',
    'aa', 'ae', 'ai', 'ao', 'au',
    'ea', 'ee', 'ei', 'eo', 'eu',
    'ia', 'ie', 'ii', 'io', 'iu',
    'oa', 'oe', 'oi', 'oo', 'ou',
    'ua', 'ue', 'ui', 'uo', 'uu',
}

CONSONANT_MULTIGRAPHS = {
    'ch', 'sh', 'th', 'ph', 'kh', 'gh', 'ng', 'ny', 'ts', 'dz', 'zh', 'll', 'rr', 'qu', 'sch',
}

TOKEN_PRIORITY = sorted(VOWEL_TOKENS | CONSONANT_MULTIGRAPHS, key=len, reverse=True)


PSEUDO_REAL_WORLD_PROFILES = {
    'pseudo-english': {
        'display_name': 'English-like (European)',
        'source_language_code': 'en',
        'region': 'european',
        'description': 'Pseudo language influenced by high-frequency English orthographic patterns.',
        'fallback_words': [
            'the', 'and', 'that', 'with', 'from', 'have', 'this', 'there', 'which', 'would',
            'people', 'world', 'light', 'night', 'water', 'stone', 'dream', 'winter', 'summer', 'silver',
        ],
        'grammar': {'word_order': 'SVO', 'adjective_position': 'before', 'enable_case_marking': False},
    },
    'pseudo-spanish': {
        'display_name': 'Spanish-like (European)',
        'source_language_code': 'es',
        'region': 'european',
        'description': 'Pseudo language influenced by common Spanish phonotactics and open syllables.',
        'fallback_words': [
            'de', 'la', 'que', 'el', 'en', 'y', 'los', 'con', 'para', 'una',
            'fuego', 'cielo', 'tierra', 'noche', 'agua', 'viento', 'casa', 'reino', 'luz', 'sombra',
        ],
        'grammar': {'word_order': 'SVO', 'adjective_position': 'after', 'enable_case_marking': False},
    },
    'pseudo-french': {
        'display_name': 'French-like (European)',
        'source_language_code': 'fr',
        'region': 'european',
        'description': 'Pseudo language influenced by frequent French letter combinations and cadence.',
        'fallback_words': [
            'le', 'de', 'et', 'la', 'les', 'des', 'dans', 'une', 'pour', 'avec',
            'lumiere', 'ombre', 'nuit', 'eau', 'terre', 'esprit', 'cour', 'monde', 'ami', 'route',
        ],
        'grammar': {'word_order': 'SVO', 'adjective_position': 'after', 'enable_case_marking': False},
    },
    'pseudo-german': {
        'display_name': 'German-like (European)',
        'source_language_code': 'de',
        'region': 'european',
        'description': 'Pseudo language influenced by German clusters and coda-heavy patterns.',
        'fallback_words': [
            'der', 'die', 'und', 'das', 'ist', 'nicht', 'mit', 'ein', 'den', 'auf',
            'nacht', 'licht', 'wasser', 'stein', 'himmel', 'sturm', 'kraft', 'wort', 'wald', 'reich',
        ],
        'grammar': {'word_order': 'SVO', 'adjective_position': 'before', 'enable_case_marking': True},
    },
    'pseudo-italian': {
        'display_name': 'Italian-like (European)',
        'source_language_code': 'it',
        'region': 'european',
        'description': 'Pseudo language influenced by Italian vowel-forward phonology.',
        'fallback_words': [
            'di', 'che', 'la', 'il', 'e', 'in', 'una', 'per', 'con', 'non',
            'notte', 'luce', 'acqua', 'vento', 'terra', 'cuore', 'strada', 'citta', 'sogno', 'stella',
        ],
        'grammar': {'word_order': 'SVO', 'adjective_position': 'after', 'enable_case_marking': False},
    },
    'pseudo-latin': {
        'display_name': 'Latin-like (European/Classical)',
        'source_language_code': 'la',
        'region': 'european',
        'description': 'Pseudo language influenced by classical Latin morphology and cadence.',
        'fallback_words': [
            'et', 'in', 'non', 'est', 'cum', 'ad', 'per', 'qui', 'quod', 'de',
            'aqua', 'terra', 'caelum', 'noctis', 'lux', 'umbra', 'ventus', 'cor', 'via', 'civitas',
            'rex', 'regina', 'ordo', 'imperium', 'stella', 'somnium', 'spiritus', 'nomen', 'tempus', 'fortis',
        ],
        'grammar': {'word_order': 'SOV', 'adjective_position': 'after', 'enable_case_marking': True},
        'morphology': {'num_prefixes': 60, 'num_suffixes': 130, 'affix_max_syl': 2},
        'name_generator_params': {
            'person_male_suffixes': ['us', 'or', 'ius', 'an'],
            'person_female_suffixes': ['a', 'ia', 'ina', 'illa'],
            'person_neutral_suffixes': ['um', 'is', 'en'],
            'place_suffixes': ['um', 'ia', 'ana', 'orum', 'ium'],
            'person_suffix_prob': 0.76,
            'place_suffix_prob': 0.68,
        },
        'sound_change_rules': [
            {'pattern': 'v', 'replacement': 'u', 'probability': 0.35, 'description': 'classical-like v/u alternation'},
            {'pattern': 'k', 'replacement': 'c', 'probability': 0.65, 'description': 'orthographic c preference'},
        ],
    },
    'pseudo-portuguese': {
        'display_name': 'Portuguese-like (European)',
        'source_language_code': 'pt',
        'region': 'european',
        'description': 'Pseudo language influenced by Portuguese nasalized-looking orthography.',
        'fallback_words': [
            'de', 'que', 'e', 'o', 'do', 'da', 'em', 'um', 'para', 'na',
            'noite', 'luz', 'agua', 'vento', 'terra', 'caminho', 'cidade', 'sombra', 'estrela', 'tempo',
        ],
        'grammar': {'word_order': 'SVO', 'adjective_position': 'after', 'enable_case_marking': False},
    },
    'pseudo-russian': {
        'display_name': 'Russian-like (European/Slavic)',
        'source_language_code': 'ru',
        'region': 'european',
        'description': 'Pseudo language influenced by transliterated Russian consonant clusters.',
        'fallback_words': [
            'i', 'v', 'ne', 'na', 'ya', 'on', 's', 'chto', 'kak', 'eto',
            'noch', 'svet', 'voda', 'zemlya', 'veter', 'serdtse', 'put', 'gorod', 'mir', 'ten',
        ],
        'grammar': {'word_order': 'SVO', 'adjective_position': 'before', 'enable_case_marking': True},
    },
    'pseudo-japanese': {
        'display_name': 'Japanese-like (East Asian)',
        'source_language_code': 'ja',
        'region': 'east-asian',
        'description': 'Pseudo language influenced by transliterated Japanese mora-like rhythms.',
        'fallback_words': [
            'watashi', 'anata', 'kore', 'sore', 'desu', 'aru', 'hito', 'mizu', 'kaze', 'tsuki',
            'yoru', 'hikari', 'kuni', 'kokoro', 'yume', 'hoshi', 'michi', 'yama', 'umi', 'hana',
        ],
        'grammar': {'word_order': 'SOV', 'adjective_position': 'before', 'enable_case_marking': True},
        'morphology': {'num_prefixes': 25, 'num_suffixes': 110},
    },
    'pseudo-korean': {
        'display_name': 'Korean-like (East Asian)',
        'source_language_code': 'ko',
        'region': 'east-asian',
        'description': 'Pseudo language influenced by transliterated Korean syllable patterns.',
        'fallback_words': [
            'na', 'neo', 'geu', 'uri', 'saram', 'mul', 'baram', 'dal', 'bam', 'bit',
            'gil', 'nara', 'maeum', 'kkum', 'haneul', 'ttang', 'sori', 'yeonghon', 'gom', 'seong',
        ],
        'grammar': {'word_order': 'SOV', 'adjective_position': 'before', 'enable_case_marking': True},
        'morphology': {'num_prefixes': 20, 'num_suffixes': 120},
    },
    'pseudo-mandarin': {
        'display_name': 'Mandarin-like (East Asian)',
        'source_language_code': 'zh',
        'region': 'east-asian',
        'description': 'Pseudo language influenced by transliterated Mandarin-like syllable inventories.',
        'fallback_words': [
            'wo', 'ni', 'ta', 'zhe', 'na', 'ren', 'shui', 'feng', 'yue', 'ye',
            'guang', 'an', 'tian', 'di', 'xin', 'meng', 'lu', 'cheng', 'shan', 'hai',
        ],
        'grammar': {'word_order': 'SVO', 'adjective_position': 'before', 'enable_case_marking': False},
        'morphology': {'num_prefixes': 18, 'num_suffixes': 70},
    },
    'pseudo-hindi': {
        'display_name': 'Hindi-like (South Asian)',
        'source_language_code': 'hi',
        'region': 'south-asian',
        'description': 'Pseudo language influenced by transliterated Hindi letter frequency and cadence.',
        'fallback_words': [
            'mai', 'tum', 'yah', 'vah', 'hai', 'nahi', 'jal', 'hawa', 'raat', 'prakash',
            'dharti', 'sapna', 'dil', 'raasta', 'shehar', 'suraj', 'chand', 'geet', 'dost', 'samay',
        ],
        'grammar': {'word_order': 'SOV', 'adjective_position': 'before', 'enable_case_marking': True},
    },
    'pseudo-bengali': {
        'display_name': 'Bengali-like (South Asian)',
        'source_language_code': 'bn',
        'region': 'south-asian',
        'description': 'Pseudo language influenced by transliterated Bengali softness and vowel movement.',
        'fallback_words': [
            'ami', 'tumi', 'eta', 'ota', 'ache', 'na', 'jal', 'batash', 'raat', 'alo',
            'mati', 'shopno', 'hridoy', 'poth', 'shohor', 'surjo', 'chand', 'gaan', 'bondhu', 'somoy',
        ],
        'grammar': {'word_order': 'SOV', 'adjective_position': 'before', 'enable_case_marking': True},
    },
    'pseudo-tamil': {
        'display_name': 'Tamil-like (South Asian)',
        'source_language_code': 'ta',
        'region': 'south-asian',
        'description': 'Pseudo language influenced by transliterated Tamil-like long-vowel tendencies.',
        'fallback_words': [
            'naan', 'nee', 'ivan', 'aval', 'irukku', 'illai', 'tanni', 'kaatru', 'iravu', 'oli',
            'mann', 'kanavu', 'idhayam', 'paadhai', 'nagaram', 'sooriyan', 'nila', 'paattu', 'nanban', 'neram',
        ],
        'grammar': {'word_order': 'SOV', 'adjective_position': 'before', 'enable_case_marking': True},
    },
    'pseudo-urdu': {
        'display_name': 'Urdu-like (South Asian)',
        'source_language_code': 'ur',
        'region': 'south-asian',
        'description': 'Pseudo language influenced by transliterated Urdu-like consonant-vowel flow.',
        'fallback_words': [
            'main', 'tum', 'yeh', 'woh', 'hai', 'nahin', 'pani', 'hawa', 'raat', 'roshni',
            'zameen', 'khwab', 'dil', 'raasta', 'shehar', 'sooraj', 'chaand', 'geet', 'dost', 'waqt',
        ],
        'grammar': {'word_order': 'SOV', 'adjective_position': 'before', 'enable_case_marking': True},
    },
}


PSEUDO_TEMPLATE_ALIASES = {
    'english': 'pseudo-english',
    'spanish': 'pseudo-spanish',
    'french': 'pseudo-french',
    'german': 'pseudo-german',
    'italian': 'pseudo-italian',
    'latin': 'pseudo-latin',
    'portuguese': 'pseudo-portuguese',
    'russian': 'pseudo-russian',
    'japanese': 'pseudo-japanese',
    'korean': 'pseudo-korean',
    'mandarin': 'pseudo-mandarin',
    'chinese': 'pseudo-mandarin',
    'hindi': 'pseudo-hindi',
    'bengali': 'pseudo-bengali',
    'tamil': 'pseudo-tamil',
    'urdu': 'pseudo-urdu',
    'english-like': 'pseudo-english',
    'spanish-like': 'pseudo-spanish',
    'french-like': 'pseudo-french',
    'german-like': 'pseudo-german',
    'italian-like': 'pseudo-italian',
    'latin-like': 'pseudo-latin',
    'portuguese-like': 'pseudo-portuguese',
    'russian-like': 'pseudo-russian',
    'japanese-like': 'pseudo-japanese',
    'korean-like': 'pseudo-korean',
    'mandarin-like': 'pseudo-mandarin',
    'hindi-like': 'pseudo-hindi',
    'bengali-like': 'pseudo-bengali',
    'tamil-like': 'pseudo-tamil',
    'urdu-like': 'pseudo-urdu',
}


def normalize_pseudo_template_name(template_name):
    if not template_name:
        return ''
    key = template_name.strip().lower()
    if key in PSEUDO_REAL_WORLD_PROFILES:
        return key
    return PSEUDO_TEMPLATE_ALIASES.get(key, '')


def is_pseudo_template(template_name):
    return bool(normalize_pseudo_template_name(template_name))


def list_pseudo_templates():
    return sorted(PSEUDO_REAL_WORLD_PROFILES.keys())


def list_pseudo_templates_by_region():
    grouped = {}
    for key, profile in PSEUDO_REAL_WORLD_PROFILES.items():
        region = profile.get('region', 'other')
        grouped.setdefault(region, []).append(key)
    for region in grouped:
        grouped[region] = sorted(grouped[region])
    return grouped


def pseudo_template_description(template_name):
    canonical = normalize_pseudo_template_name(template_name)
    if not canonical:
        return ''
    profile = PSEUDO_REAL_WORLD_PROFILES[canonical]
    region = profile.get('region', 'other').replace('-', ' ')
    return f"{profile.get('description', '')} Region: {region}."


def _normalize_word_candidates(word):
    text = unidecode(str(word)).lower()
    text = text.replace("'", '')
    text = re.sub(r'[^a-z\s-]', ' ', text)
    parts = re.split(r'[\s-]+', text)
    return [part for part in parts if len(part) >= 2]


def _tokenize(word):
    tokens = []
    idx = 0
    while idx < len(word):
        matched = None
        for option in TOKEN_PRIORITY:
            if word.startswith(option, idx):
                matched = option
                break
        if matched:
            tokens.append(matched)
            idx += len(matched)
        else:
            tokens.append(word[idx])
            idx += 1
    return tokens


def _is_vowel(token):
    if not token:
        return False
    if token in VOWEL_TOKENS:
        return True
    return token[0] in 'aeiou'


def _scaled_weights(counter, selected):
    if not selected:
        return {}
    max_value = max(counter.get(token, 1) for token in selected)
    if max_value <= 0:
        return {token: 1.0 for token in selected}
    return {
        token: round(0.25 + 1.75 * (counter.get(token, 1) / max_value), 4)
        for token in selected
    }


def _top_tokens(counter, limit, allow_empty=False):
    ordered = []
    for token, _count in counter.most_common():
        if not allow_empty and token == '':
            continue
        if token not in ordered:
            ordered.append(token)
        if len(ordered) >= limit:
            break
    return ordered


def _load_corpus_words(profile, sample_size):
    words = []
    language_code = profile.get('source_language_code')
    if top_n_list is not None and language_code:
        try:
            words = top_n_list(language_code, sample_size)
        except Exception:
            words = []

    if not words:
        words = profile.get('fallback_words', [])

    normalized = []
    seen = set()
    for word in words:
        for candidate in _normalize_word_candidates(word):
            if candidate not in seen:
                seen.add(candidate)
                normalized.append(candidate)
    return normalized


def _derive_phonology_from_words(words, profile):
    consonant_counts = Counter()
    vowel_counts = Counter()
    onset_counts = Counter({'': 10})
    coda_counts = Counter({'': 10})
    structure_counts = Counter({'CV': 1, 'CVC': 1, 'V': 1, 'VC': 1})

    for word in words:
        tokens = _tokenize(word)
        if not tokens:
            continue

        vowel_positions = [idx for idx, token in enumerate(tokens) if _is_vowel(token)]
        if not vowel_positions:
            continue

        for token in tokens:
            if _is_vowel(token):
                vowel_counts[token] += 1
            else:
                consonant_counts[token] += 1

        first_vowel_idx = vowel_positions[0]
        last_vowel_idx = vowel_positions[-1]

        onset = ''.join(tokens[:first_vowel_idx])
        coda = ''.join(tokens[last_vowel_idx + 1:])

        if len(onset) <= 3:
            onset_counts[onset] += 1
        if len(coda) <= 3:
            coda_counts[coda] += 1

        starts_with_consonant = first_vowel_idx > 0
        ends_with_consonant = last_vowel_idx < len(tokens) - 1
        has_adjacent_vowels = any(_is_vowel(tokens[i]) and _is_vowel(tokens[i + 1]) for i in range(len(tokens) - 1))

        if starts_with_consonant and ends_with_consonant:
            structure = 'CVC'
        elif starts_with_consonant and not ends_with_consonant:
            structure = 'CV'
        elif not starts_with_consonant and ends_with_consonant:
            structure = 'VC'
        else:
            structure = 'V'

        if has_adjacent_vowels and structure in {'CV', 'V'}:
            structure = f"{structure}V"

        structure_counts[structure] += 1

        for idx in range(1, len(tokens)):
            left = tokens[idx - 1]
            right = tokens[idx]
            if _is_vowel(left) and not _is_vowel(right):
                coda_counts[right] += 1
            if not _is_vowel(left) and _is_vowel(right):
                onset_counts[left] += 1

    fallback_phonology = profile.get('fallback_phonology', {})

    consonants = _top_tokens(consonant_counts, limit=18)
    vowels = _top_tokens(vowel_counts, limit=12)

    if len(consonants) < 8:
        consonants = list(dict.fromkeys(consonants + copy.deepcopy(DEFAULT_PHONOLOGY_PARAMS['consonants'])))[:18]
    if len(vowels) < 5:
        vowels = list(dict.fromkeys(vowels + copy.deepcopy(DEFAULT_PHONOLOGY_PARAMS['vowels'])))[:12]

    onsets = _top_tokens(onset_counts, limit=28, allow_empty=True)
    codas = _top_tokens(coda_counts, limit=20, allow_empty=True)

    if '' not in onsets:
        onsets.append('')
    if '' not in codas:
        codas.append('')

    filtered_onsets = []
    for onset in onsets:
        if onset == '':
            filtered_onsets.append(onset)
            continue
        tokenized = _tokenize(onset)
        if all(not _is_vowel(token) for token in tokenized) and len(tokenized) <= 3:
            filtered_onsets.append(onset)

    filtered_codas = []
    for coda in codas:
        if coda == '':
            filtered_codas.append(coda)
            continue
        tokenized = _tokenize(coda)
        if all(not _is_vowel(token) for token in tokenized) and len(tokenized) <= 3:
            filtered_codas.append(coda)

    if not filtered_onsets:
        filtered_onsets = [''] + consonants[:12]
    if not filtered_codas:
        filtered_codas = [''] + consonants[:10]

    structures = _top_tokens(structure_counts, limit=6)
    valid_structures = []
    for structure in structures:
        if structure and all(char in {'C', 'V'} for char in structure):
            valid_structures.append(structure)
    if not valid_structures:
        valid_structures = ['CV', 'CVC', 'V', 'VC']

    onset_weight_map = _scaled_weights(onset_counts, filtered_onsets)
    coda_weight_map = _scaled_weights(coda_counts, filtered_codas)

    max_onset_cluster = max((len(_tokenize(onset)) for onset in filtered_onsets if onset), default=1)
    max_coda_cluster = max((len(_tokenize(coda)) for coda in filtered_codas if coda), default=1)
    max_cluster = min(4, max(2, max(max_onset_cluster, max_coda_cluster)))

    derived = {
        'consonants': consonants,
        'vowels': vowels,
        'syllable_structures': valid_structures,
        'structure_weights': _scaled_weights(structure_counts, valid_structures),
        'consonant_weights': _scaled_weights(consonant_counts, consonants),
        'vowel_weights': _scaled_weights(vowel_counts, vowels),
        'onsets': filtered_onsets,
        'codas': filtered_codas,
        'onset_weights': onset_weight_map,
        'coda_weights': coda_weight_map,
        'boundary_smoothing': True,
        'max_consonant_cluster': max_cluster,
        'epenthetic_vowels': vowels[:2] if len(vowels) >= 2 else vowels,
        'hiatus_glides': [token for token in ['y', 'w', 'h', 'r', 'l'] if token in consonants],
    }

    if fallback_phonology:
        derived = deep_merge(derived, fallback_phonology)

    return derived


def get_pseudo_template_config(template_name, sample_size=2000):
    canonical = normalize_pseudo_template_name(template_name)
    if not canonical:
        available = ', '.join(list_pseudo_templates())
        raise ValueError(f"Unknown pseudo template '{template_name}'. Available pseudo templates: {available}")

    profile = PSEUDO_REAL_WORLD_PROFILES[canonical]
    corpus_words = _load_corpus_words(profile, sample_size=sample_size)

    derived_phonology = _derive_phonology_from_words(corpus_words, profile)
    phonology = deep_merge(copy.deepcopy(DEFAULT_PHONOLOGY_PARAMS), derived_phonology)
    phonology = deep_merge(phonology, profile.get('phonology', {}))

    morphology = deep_merge(copy.deepcopy(DEFAULT_MORPHOLOGY_PARAMS), profile.get('morphology', {}))
    wordgen = deep_merge(copy.deepcopy(DEFAULT_WORDGEN_PARAMS), profile.get('word_generator_params', {}))
    namegen = deep_merge(copy.deepcopy(DEFAULT_NAMEGEN_PARAMS), profile.get('name_generator_params', {}))
    grammar = deep_merge(copy.deepcopy(DEFAULT_GRAMMAR_PARAMS), profile.get('grammar', {}))
    sound_rules = copy.deepcopy(profile.get('sound_change_rules', DEFAULT_SOUND_CHANGE_RULES))

    return {
        'template_name': canonical,
        'phonology': phonology,
        'morphology': morphology,
        'word_generator_params': wordgen,
        'name_generator_params': namegen,
        'grammar': grammar,
        'sound_change_rules': sound_rules,
        'description': profile.get('description', ''),
        'source_language_code': profile.get('source_language_code', ''),
        'region': profile.get('region', 'other'),
        'is_pseudo_real_world': True,
        'wordfreq_enabled': top_n_list is not None,
    }
