import copy

from src.language_generator.defaults import (
    DEFAULT_GRAMMAR_PARAMS,
    DEFAULT_MORPHOLOGY_PARAMS,
    DEFAULT_NAMEGEN_PARAMS,
    DEFAULT_PHONOLOGY_PARAMS,
    DEFAULT_SOUND_CHANGE_RULES,
    DEFAULT_WORDGEN_PARAMS,
    deep_merge,
)
from src.language_generator.pseudo_real_world import (
    get_pseudo_template_config,
    is_pseudo_template,
    list_pseudo_templates,
    pseudo_template_description,
)


TEMPLATE_LANGUAGES = {
    'balanced': {
        'description': 'General-purpose language with mixed consonant-vowel balance.',
        'phonology': {},
        'morphology': {},
        'word_generator_params': {},
        'name_generator_params': {},
        'grammar': {},
        'sound_change_rules': [],
    },
    'harsh': {
        'description': 'Consonant-heavy template with clipped syllables and dense clusters.',
        'phonology': {
            'vowels': ['a', 'e', 'i', 'o', 'u'],
            'syllable_structures': ['CVC', 'CV', 'CCVC', 'CVCC', 'VC'],
            'structure_weights': {'CVC': 0.42, 'CV': 0.22, 'CCVC': 0.18, 'CVCC': 0.10, 'VC': 0.08},
            'max_consonant_cluster': 3,
            'onsets': [
                'k', 't', 'p', 'g', 'd', 'b', 'r', 's', 'z', 'x', 'v', 'n', 'm',
                'kr', 'gr', 'tr', 'dr', 'st', 'sk', 'sp', 'sr', 'vr', 'zr',
            ],
            'codas': ['k', 't', 'p', 'n', 'm', 'r', 's', 'x', 'st', 'sk', 'rk', 'rt', ''],
            'epenthetic_vowels': ['a'],
            'hiatus_glides': ['h'],
        },
        'grammar': {
            'word_order': 'SOV',
            'adjective_position': 'before',
            'enable_case_marking': True,
            'accusative_suffix': 'k',
            'genitive_suffix': 'r',
        },
        'word_generator_params': {'prefix_prob': 0.10, 'suffix_prob': 0.25},
        'sound_change_rules': [
            {'pattern': 'p', 'replacement': 'f', 'probability': 0.25, 'description': 'partial frication'},
            {'pattern': 'k', 'replacement': 'x', 'probability': 0.20, 'description': 'velar frication'},
        ],
    },
    'lyrical': {
        'description': 'Vowel-forward, flowing template with open syllables and glides.',
        'phonology': {
            'consonants': ['m', 'n', 'l', 'r', 's', 'h', 'v', 'y', 'w', 'f', 'th'],
            'vowels': ['a', 'e', 'i', 'o', 'u', 'ae', 'ia', 'ea', 'oi'],
            'syllable_structures': ['CV', 'V', 'CVV', 'VC'],
            'structure_weights': {'CV': 0.45, 'V': 0.22, 'CVV': 0.22, 'VC': 0.11},
            'onsets': ['m', 'n', 'l', 'r', 's', 'h', 'v', 'y', 'w', 'f', 'th', ''],
            'codas': ['n', 'l', 'r', 's', 'm', 'h', ''],
            'coda_weights': {'': 1.9, 'n': 1.1, 'l': 0.9, 'r': 0.8, 's': 0.8, 'm': 0.6, 'h': 0.5},
            'epenthetic_vowels': ['e', 'a', 'i'],
            'hiatus_glides': ['y', 'w', 'h'],
        },
        'grammar': {'word_order': 'VSO', 'adjective_position': 'after', 'enable_case_marking': False},
        'word_generator_params': {'prefix_prob': 0.08, 'suffix_prob': 0.22},
        'name_generator_params': {'person_suffix_prob': 0.66, 'place_suffix_prob': 0.58},
        'sound_change_rules': [
            {'pattern': 's', 'replacement': 'h', 'left_context': '[aeiou]', 'probability': 0.35, 'description': 'intervocalic softening'},
        ],
    },
    'archaic': {
        'description': 'Older ceremonial register with heavier morphology and conservative codas.',
        'phonology': {
            'consonants': ['p', 't', 'k', 'b', 'd', 'g', 'm', 'n', 'l', 'r', 's', 'f', 'h', 'th', 'ph', 'x'],
            'vowels': ['a', 'e', 'i', 'o', 'u', 'ae', 'oe', 'au'],
            'syllable_structures': ['CV', 'CVC', 'VC', 'CCVC'],
            'structure_weights': {'CV': 0.30, 'CVC': 0.38, 'VC': 0.15, 'CCVC': 0.17},
            'max_consonant_cluster': 3,
            'epenthetic_vowels': ['e', 'a'],
        },
        'morphology': {'num_prefixes': 70, 'num_suffixes': 120, 'affix_max_syl': 2},
        'grammar': {
            'word_order': 'OSV',
            'adjective_position': 'after',
            'enable_case_marking': True,
            'past_prefix': 'ar',
            'future_prefix': 'ul',
        },
        'word_generator_params': {'prefix_prob': 0.22, 'suffix_prob': 0.42},
        'name_generator_params': {'place_suffix_prob': 0.68, 'thing_suffix_prob': 0.34},
        'sound_change_rules': [
            {'pattern': 'w', 'replacement': 'v', 'probability': 1.0, 'description': 'late period w > v'},
            {'pattern': 'th', 'replacement': 't', 'probability': 0.5, 'description': 'partial dental simplification'},
        ],
    },
    'courtly': {
        'description': 'Prestige register with elegant cadence and moderate morphology.',
        'phonology': {
            'consonants': ['p', 't', 'k', 'b', 'd', 'g', 'm', 'n', 'l', 'r', 's', 'f', 'v', 'h', 'y', 'w'],
            'vowels': ['a', 'e', 'i', 'o', 'u', 'ae', 'ei', 'ia', 'io'],
            'syllable_structures': ['CV', 'CVC', 'V', 'CVV'],
            'structure_weights': {'CV': 0.44, 'CVC': 0.25, 'V': 0.14, 'CVV': 0.17},
            'onsets': [
                'p', 't', 'k', 'b', 'd', 'g', 'm', 'n', 'l', 'r', 's', 'f', 'v', 'h', 'y', 'w',
                'pr', 'tr', 'kr', 'pl', 'cl', 'fl', 'gl', '',
            ],
            'coda_weights': {'': 1.55, 'n': 1.20, 'r': 1.00, 'l': 0.95, 's': 0.90, 'm': 0.85, 't': 0.60, 'k': 0.45},
            'epenthetic_vowels': ['e', 'a'],
        },
        'grammar': {'word_order': 'SVO', 'adjective_position': 'after', 'enable_case_marking': True},
        'word_generator_params': {'prefix_prob': 0.12, 'suffix_prob': 0.34},
        'name_generator_params': {
            'person_male_suffixes': ['or', 'ian', 'ius', 'el'],
            'person_female_suffixes': ['a', 'ia', 'ella', 'ine'],
            'person_neutral_suffixes': ['is', 'en', 'or'],
            'person_suffix_prob': 0.72,
            'place_suffixes': ['ia', 'ora', 'um', 'en', 'polis'],
            'place_suffix_prob': 0.62,
        },
        'sound_change_rules': [
            {'pattern': 'k', 'replacement': 'c', 'right_context': '[eiy]', 'probability': 0.55, 'description': 'courtly palatalization'},
        ],
    },
}


def list_builtin_templates():
    return sorted(TEMPLATE_LANGUAGES.keys())


def list_templates(include_pseudo=True):
    builtins = list_builtin_templates()
    if not include_pseudo:
        return builtins
    return builtins + list_pseudo_templates()


def template_description(template_name):
    if is_pseudo_template(template_name):
        return pseudo_template_description(template_name)

    entry = TEMPLATE_LANGUAGES.get(template_name)
    if not entry:
        return ''
    return entry.get('description', '')


def get_template_config(template_name='balanced'):
    name = (template_name or 'balanced').lower().strip()
    if is_pseudo_template(name):
        return get_pseudo_template_config(name)

    if name not in TEMPLATE_LANGUAGES:
        raise ValueError(f"Unknown template '{template_name}'. Available templates: {', '.join(list_templates())}")

    template = TEMPLATE_LANGUAGES[name]
    return {
        'template_name': name,
        'phonology': deep_merge(DEFAULT_PHONOLOGY_PARAMS, template.get('phonology', {})),
        'morphology': deep_merge(DEFAULT_MORPHOLOGY_PARAMS, template.get('morphology', {})),
        'word_generator_params': deep_merge(DEFAULT_WORDGEN_PARAMS, template.get('word_generator_params', {})),
        'name_generator_params': deep_merge(DEFAULT_NAMEGEN_PARAMS, template.get('name_generator_params', {})),
        'grammar': deep_merge(DEFAULT_GRAMMAR_PARAMS, template.get('grammar', {})),
        'sound_change_rules': copy.deepcopy(template.get('sound_change_rules', DEFAULT_SOUND_CHANGE_RULES)),
        'description': template.get('description', ''),
    }
