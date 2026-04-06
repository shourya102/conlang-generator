import copy


DEFAULT_PHONOLOGY_PARAMS = {
    'consonants': ['p', 't', 'k', 'b', 'd', 'g', 'm', 'n', 'l', 'r', 's', 'f', 'v', 'h', 'x', 'y', 'w'],
    'vowels': ['a', 'e', 'i', 'o', 'u', 'ae', 'oe', 'au', 'ai', 'ei'],
    'syllable_structures': ['CV', 'CVC', 'V', 'VC'],
    'structure_weights': {'CV': 0.48, 'CVC': 0.30, 'V': 0.12, 'VC': 0.10},
    'consonant_weights': {
        'n': 1.30, 'r': 1.25, 'l': 1.20, 's': 1.20, 't': 1.15, 'k': 1.10, 'm': 1.10,
        'p': 1.00, 'd': 1.00, 'g': 0.95, 'b': 0.90, 'f': 0.90, 'v': 0.75,
        'h': 0.80, 'x': 0.55, 'y': 0.65, 'w': 0.60,
    },
    'vowel_weights': {
        'a': 1.35, 'e': 1.25, 'i': 1.10, 'o': 1.00, 'u': 0.95,
        'ae': 0.70, 'oe': 0.45, 'au': 0.70, 'ai': 0.65, 'ei': 0.60,
    },
    'onsets': [
        'p', 't', 'k', 'b', 'd', 'g', 'm', 'n', 'l', 'r', 's', 'f', 'v', 'h', 'y', 'w',
        'st', 'tr', 'pr', 'kr', 'gr', 'cl', 'cr', 'pl', 'bl', 'gl', 'fl', 'sk', 'sm', 'sn', '',
    ],
    'onset_weights': {
        '': 0.35, 'st': 0.85, 'tr': 1.05, 'pr': 0.95, 'kr': 0.90, 'gr': 0.85,
        'cl': 0.80, 'cr': 0.85, 'pl': 0.95, 'bl': 0.70, 'gl': 0.65, 'fl': 0.75,
        'sk': 0.70, 'sm': 0.75, 'sn': 0.65,
    },
    'codas': ['m', 'n', 'l', 'r', 's', 't', 'k', 'x', ''],
    'coda_weights': {
        '': 1.35, 'n': 1.20, 'r': 1.10, 'l': 1.05, 's': 1.00, 'm': 0.95,
        't': 0.90, 'k': 0.70, 'x': 0.40,
    },
    'illegal_sequences': ['pp', 'tt', 'cc', 'bb', 'dd', 'gg', 'hh', 'vv', 'ff', 'aa', 'ee', 'ii', 'oo', 'uu'],
    'boundary_smoothing': True,
    'max_consonant_cluster': 2,
    'epenthetic_vowels': ['a', 'e'],
    'hiatus_glides': ['y', 'w', 'h'],
    'allowed_boundary_clusters': [
        'tr', 'pr', 'kr', 'gr', 'st', 'sp', 'sk', 'sm', 'sn',
        'fr', 'fl', 'br', 'bl', 'dr', 'gl', 'kl', 'pl', 'cl',
    ],
}

DEFAULT_MORPHOLOGY_PARAMS = {
    'num_roots': 420,
    'num_prefixes': 50,
    'num_suffixes': 90,
    'root_min_syl': 1,
    'root_max_syl': 2,
    'affix_max_syl': 1,
}

DEFAULT_WORDGEN_PARAMS = {
    'prefix_prob': 0.14,
    'suffix_prob': 0.30,
    'max_gen_attempts': 120,
    'compact_function_words': True,
    'function_word_pos_tags': [
        'Pronoun',
        'Preposition',
        'Conjunction',
        'Determiner',
        'Interjection',
        'PossessiveMarker',
    ],
    'function_word_meanings': [
        'a', 'an', 'the',
        'and', 'or', 'but', 'if', 'so',
        'in', 'on', 'at', 'to', 'of', 'for', 'by', 'from', 'with', 'without',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'us', 'them',
        'my', 'your', 'his', 'her', 'our', 'their',
        'is', 'are', 'was', 'were',
        'not', 'no', 'yes',
    ],
    'function_word_min_syl': 1,
    'function_word_max_syl': 1,
    'function_word_long_form_chance': 0.15,
    'function_word_allow_affixes': False,
    'function_word_max_chars': 5,
}

DEFAULT_NAMEGEN_PARAMS = {
    'person_min_syl': 2,
    'person_max_syl': 3,
    'place_min_syl': 2,
    'place_max_syl': 4,
    'thing_min_syl': 1,
    'thing_max_syl': 3,
    'person_male_suffixes': ['us', 'or', 'an', 'ius'],
    'person_female_suffixes': ['a', 'ia', 'ina', 'illa'],
    'person_neutral_suffixes': ['is', 'en', 'o', 'um'],
    'place_suffixes': ['ia', 'um', 'os', 'ana', 'polis', 'burg', 'acum'],
    'thing_suffixes': ['ex', 'or', 'mentum', 'io', 'ura'],
    'person_suffix_prob': 0.58,
    'place_suffix_prob': 0.50,
    'thing_suffix_prob': 0.24,
    'max_attempts': 120,
}

DEFAULT_GRAMMAR_PARAMS = {
    'word_order': 'SVO',
    'adjective_position': 'after',
    'adposition_order': 'preposition',
    'adverb_position': 'before',
    'drop_articles': True,
    'drop_redundant_auxiliaries': True,
    'plural_suffix': 'i',
    'accusative_suffix': 'm',
    'genitive_suffix': 'n',
    'past_prefix': 'ta',
    'future_prefix': 'sa',
    'progressive_suffix': 'ri',
    'perfect_suffix': 'na',
    'enable_case_marking': True,
    'case_marking_style': 'suffix',
    'case_mark_pronouns': False,
    'nominative_particle': '',
    'accusative_particle': 'ko',
    'genitive_particle': 'no',
    'enable_subject_agreement': True,
    'agreement_style': 'suffix',
    'agreement_markers': {
        '1sg': 'm',
        '2sg': 't',
        '3sg': '',
        '1pl': 'me',
        '2pl': 'te',
        '3pl': 'n',
    },
    'negation_particle': 'na',
    'negation_position': 'before_verb',
    'replace_lexical_negation': True,
    'question_particle': 'ka',
    'question_particle_position': 'clause_final',
}

DEFAULT_SOUND_CHANGE_RULES = []


def deep_merge(base, overrides):
    result = copy.deepcopy(base)
    if not overrides:
        return result

    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result
