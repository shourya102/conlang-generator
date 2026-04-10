import copy
import datetime
import importlib
import json
import os
import re

try:
    nltk = importlib.import_module('nltk')
except ImportError:
    nltk = None

from src.language_generator.core_concepts import CORE_CONCEPTS
from src.language_generator.defaults import (
    DEFAULT_GRAMMAR_PARAMS as BASE_DEFAULT_GRAMMAR_PARAMS,
    DEFAULT_MORPHOLOGY_PARAMS as BASE_DEFAULT_MORPHOLOGY_PARAMS,
    DEFAULT_NAMEGEN_PARAMS as BASE_DEFAULT_NAMEGEN_PARAMS,
    DEFAULT_PHONOLOGY_PARAMS as BASE_DEFAULT_PHONOLOGY_PARAMS,
    DEFAULT_SOUND_CHANGE_RULES as BASE_DEFAULT_SOUND_CHANGE_RULES,
    DEFAULT_WORDGEN_PARAMS as BASE_DEFAULT_WORDGEN_PARAMS,
    deep_merge,
)
from src.language_generator.evaluator import PronounceabilityEvaluator
from src.language_generator.grammar_engine import GrammarEngine
from src.language_generator.lexicon import Lexicon
from src.language_generator.morphology import Morphology
from src.language_generator.name_generator import NameGenerator
from src.language_generator.noun_generator import NounGenerator
from src.language_generator.phonology import Phonology
from src.language_generator.sound_change import SoundChangeEngine
from src.language_generator.templates import get_template_config
from src.language_generator.word_generator import WordGenerator


class Language:
    DEFAULT_PHONOLOGY_PARAMS = copy.deepcopy(BASE_DEFAULT_PHONOLOGY_PARAMS)
    DEFAULT_MORPHOLOGY_PARAMS = copy.deepcopy(BASE_DEFAULT_MORPHOLOGY_PARAMS)
    DEFAULT_WORDGEN_PARAMS = copy.deepcopy(BASE_DEFAULT_WORDGEN_PARAMS)
    DEFAULT_NAMEGEN_PARAMS = copy.deepcopy(BASE_DEFAULT_NAMEGEN_PARAMS)
    DEFAULT_GRAMMAR_PARAMS = copy.deepcopy(BASE_DEFAULT_GRAMMAR_PARAMS)
    DEFAULT_SOUND_CHANGE_RULES = copy.deepcopy(BASE_DEFAULT_SOUND_CHANGE_RULES)

    TOKEN_NORMALIZATION_ALIASES = {
        'havnt': "haven't",
        "havn't": "haven't",
        'havent': "haven't",
        'hasnt': "hasn't",
        'hadnt': "hadn't",
        'dont': "don't",
        'doesnt': "doesn't",
        'didnt': "didn't",
        'cant': "can't",
        'wont': "won't",
        'isnt': "isn't",
        'arent': "aren't",
        'wasnt': "wasn't",
        'werent': "weren't",
        'shouldve': "should've",
        'wouldve': "would've",
        'couldve': "could've",
        'mustve': "must've",
        'im': "i'm",
        'youre': "you're",
        'theyre': "they're",
        'ive': "i've",
        'youve': "you've",
        'weve': "we've",
        'theyve': "they've",
    }

    CONTRACTION_SUFFIX_EXPANSIONS = {
        "n't": 'not',
        "'ve": 'have',
        "'re": 'be',
        "'m": 'be',
        "'ll": 'will',
        "'d": 'would',
        "'s": 'be',
    }

    APOSTROPHE_S_CONTRACTION_BASES = {
        'it', 'he', 'she', 'that', 'there', 'what', 'who', 'where', 'when',
        'why', 'how', 'here', 'let', 'i', 'you', 'we', 'they',
    }

    def __init__(
        self,
        phonology=None,
        morphology=None,
        lexicon=None,
        word_generator=None,
        name_generator=None,
        grammar_engine=None,
        noun_generator=None,
        evaluator=None,
        sound_change_engine=None,
        grammar_config=None,
        sound_change_rules=None,
        template_name='balanced',
        style_preset='balanced',
        metadata=None,
        bootstrap=True,
    ):
        self.template_name = (template_name or 'balanced').strip().lower()
        self.style_preset = (style_preset or self.template_name).strip().lower()
        self.metadata = metadata.copy() if isinstance(metadata, dict) else {}

        self.nltk_enabled = bool(nltk)
        self._ensure_nltk_data()

        self.phonology = self._build_phonology(phonology)
        self.lexicon = self._build_lexicon(lexicon)
        self.morphology = self._build_morphology(morphology)

        self.evaluator = self._build_evaluator(evaluator)
        self.word_generator = self._build_word_generator(word_generator)
        self.name_generator = self._build_name_generator(name_generator)

        self.grammar_engine = self._build_grammar_engine(grammar_engine, grammar_config)
        self.noun_generator = self._build_noun_generator(noun_generator)
        self.sound_change_engine = self._build_sound_change_engine(sound_change_engine, sound_change_rules)

        if bootstrap and self.lexicon.get_size() < len(CORE_CONCEPTS) // 2:
            self._bootstrap_lexicon(CORE_CONCEPTS)

        self._repair_lexicon_part_of_speech()

    def _build_phonology(self, phonology):
        if isinstance(phonology, Phonology):
            return phonology
        if isinstance(phonology, dict):
            return Phonology(config=phonology)
        return Phonology(config=copy.deepcopy(self.DEFAULT_PHONOLOGY_PARAMS))

    def _build_lexicon(self, lexicon):
        if isinstance(lexicon, Lexicon):
            return lexicon
        if isinstance(lexicon, dict):
            return Lexicon(config=lexicon)
        return Lexicon()

    def _build_morphology(self, morphology):
        if isinstance(morphology, Morphology):
            return morphology

        if isinstance(morphology, dict):
            if all(key in morphology for key in ('roots', 'prefixes', 'suffixes')):
                return Morphology(phonology=self.phonology, config=morphology)
            return Morphology(phonology=self.phonology, config=None, **morphology)

        return Morphology(
            phonology=self.phonology,
            config=None,
            **copy.deepcopy(self.DEFAULT_MORPHOLOGY_PARAMS),
        )

    def _build_evaluator(self, evaluator):
        if isinstance(evaluator, PronounceabilityEvaluator):
            return evaluator
        if isinstance(evaluator, dict):
            return PronounceabilityEvaluator(
                phonology=self.phonology,
                min_score=evaluator.get('min_score', 58),
            )
        return PronounceabilityEvaluator(phonology=self.phonology, min_score=58)

    def _build_word_generator(self, word_generator):
        if isinstance(word_generator, WordGenerator):
            return word_generator

        params = copy.deepcopy(self.DEFAULT_WORDGEN_PARAMS)
        if isinstance(word_generator, dict):
            params = deep_merge(params, word_generator)

        return WordGenerator(
            phonology=self.phonology,
            morphology=self.morphology,
            lexicon=self.lexicon,
            evaluator=self.evaluator,
            min_pronounceability_score=self.evaluator.min_score,
            **params,
        )

    def _build_name_generator(self, name_generator):
        if isinstance(name_generator, NameGenerator):
            return name_generator

        params = copy.deepcopy(self.DEFAULT_NAMEGEN_PARAMS)
        if isinstance(name_generator, dict):
            params = deep_merge(params, name_generator)
        params['evaluator'] = self.evaluator
        params['min_pronounceability_score'] = self.evaluator.min_score

        return NameGenerator(
            phonology=self.phonology,
            lexicon=self.lexicon,
            name_params=params,
        )

    def _build_grammar_engine(self, grammar_engine, grammar_config):
        if isinstance(grammar_engine, GrammarEngine):
            return grammar_engine

        params = copy.deepcopy(self.DEFAULT_GRAMMAR_PARAMS)
        if isinstance(grammar_engine, dict):
            params = deep_merge(params, grammar_engine)
        if isinstance(grammar_config, dict):
            params = deep_merge(params, grammar_config)

        return GrammarEngine(phonology=self.phonology, config=params)

    def _build_noun_generator(self, noun_generator):
        if isinstance(noun_generator, NounGenerator):
            return noun_generator
        return NounGenerator(
            word_generator=self.word_generator,
            name_generator=self.name_generator,
            lexicon=self.lexicon,
            grammar_engine=self.grammar_engine,
            evaluator=self.evaluator,
        )

    def _build_sound_change_engine(self, sound_change_engine, sound_change_rules):
        if isinstance(sound_change_engine, SoundChangeEngine):
            return sound_change_engine

        rules = []
        if isinstance(sound_change_engine, list):
            rules.extend(sound_change_engine)
        if isinstance(sound_change_rules, list):
            rules.extend(sound_change_rules)

        return SoundChangeEngine(rules=rules)

    @classmethod
    def from_template(cls, template_name='balanced', bootstrap=True, metadata=None):
        template = get_template_config(template_name)
        merged_metadata = metadata.copy() if isinstance(metadata, dict) else {}
        merged_metadata.setdefault('template_description', template.get('description', ''))
        if template.get('region'):
            merged_metadata.setdefault('template_region', template.get('region'))
        if template.get('source_language_code'):
            merged_metadata.setdefault('source_language_code', template.get('source_language_code'))
        if template.get('is_pseudo_real_world') is not None:
            merged_metadata.setdefault('is_pseudo_real_world', bool(template.get('is_pseudo_real_world')))
        if template.get('wordfreq_enabled') is not None:
            merged_metadata.setdefault('wordfreq_enabled', bool(template.get('wordfreq_enabled')))
        return cls(
            phonology=template['phonology'],
            morphology=template['morphology'],
            word_generator=template['word_generator_params'],
            name_generator=template['name_generator_params'],
            grammar_config=template['grammar'],
            sound_change_rules=template['sound_change_rules'],
            template_name=template['template_name'],
            style_preset=template['template_name'],
            metadata=merged_metadata,
            bootstrap=bootstrap,
        )

    @classmethod
    def from_config(cls, config, metadata=None, bootstrap=False):
        if not isinstance(config, dict):
            raise ValueError('Language config must be a dictionary.')

        template_name = config.get('template_name', 'balanced')
        style_preset = config.get('style_preset', template_name)

        phonology_cfg = config.get('phonology', copy.deepcopy(cls.DEFAULT_PHONOLOGY_PARAMS))
        morphology_cfg = config.get('morphology', copy.deepcopy(cls.DEFAULT_MORPHOLOGY_PARAMS))
        lexicon_cfg = config.get('lexicon', {'entries': {}})
        wordgen_params = config.get('word_generator_params', copy.deepcopy(cls.DEFAULT_WORDGEN_PARAMS))
        namegen_params = config.get('name_generator_params', copy.deepcopy(cls.DEFAULT_NAMEGEN_PARAMS))
        grammar_cfg = config.get('grammar', copy.deepcopy(cls.DEFAULT_GRAMMAR_PARAMS))

        sound_rules = config.get('sound_change_rules')
        if sound_rules is None:
            sound_rules = config.get('sound_changes', {}).get('rules', [])

        quality_cfg = config.get('generation_quality', {})
        evaluator = PronounceabilityEvaluator(
            phonology=Phonology(config=phonology_cfg),
            min_score=quality_cfg.get('min_pronounceability_score', 58),
        )

        lexicon = Lexicon(config=lexicon_cfg)
        phonology = evaluator.phonology
        if isinstance(morphology_cfg, dict) and all(k in morphology_cfg for k in ('roots', 'prefixes', 'suffixes')):
            morphology = Morphology(phonology=phonology, config=morphology_cfg)
        else:
            morphology = Morphology(phonology=phonology, config=None, **morphology_cfg)

        wordgen_cfg = deep_merge(copy.deepcopy(cls.DEFAULT_WORDGEN_PARAMS), wordgen_params)
        namegen_cfg = deep_merge(copy.deepcopy(cls.DEFAULT_NAMEGEN_PARAMS), namegen_params)
        namegen_cfg['evaluator'] = evaluator
        namegen_cfg['min_pronounceability_score'] = evaluator.min_score

        word_generator = WordGenerator(
            phonology=phonology,
            morphology=morphology,
            lexicon=lexicon,
            evaluator=evaluator,
            min_pronounceability_score=evaluator.min_score,
            **wordgen_cfg,
        )
        name_generator = NameGenerator(phonology=phonology, lexicon=lexicon, name_params=namegen_cfg)
        grammar_engine = GrammarEngine(phonology=phonology, config=grammar_cfg)
        sound_engine = SoundChangeEngine(rules=sound_rules or [])

        return cls(
            phonology=phonology,
            morphology=morphology,
            lexicon=lexicon,
            word_generator=word_generator,
            name_generator=name_generator,
            grammar_engine=grammar_engine,
            evaluator=evaluator,
            sound_change_engine=sound_engine,
            template_name=template_name,
            style_preset=style_preset,
            metadata=metadata,
            bootstrap=bootstrap,
        )

    def _ensure_nltk_data(self):
        if not self.nltk_enabled:
            return

        required_packages = ['punkt', 'averaged_perceptron_tagger']
        try:
            for package in required_packages:
                path = f'tokenizers/{package}' if package == 'punkt' else f'taggers/{package}'
                nltk.data.find(path)
        except LookupError:
            try:
                for package in required_packages:
                    nltk.download(package, quiet=True)
            except Exception:
                self.nltk_enabled = False
        except Exception:
            self.nltk_enabled = False

    def _normalize_english_token(self, token):
        normalized = str(token or '').strip().lower()
        if not normalized:
            return ''

        normalized = normalized.replace('’', "'").replace('‘', "'").replace('`', "'")
        normalized = re.sub(r"^[^a-z0-9']+|[^a-z0-9']+$", '', normalized)
        if not normalized:
            return ''

        return self.TOKEN_NORMALIZATION_ALIASES.get(normalized, normalized)

    def _english_lookup_forms(self, token):
        normalized = self._normalize_english_token(token)
        if not normalized:
            return []

        forms = [normalized]
        no_apostrophe = normalized.replace("'", '')
        if no_apostrophe and no_apostrophe not in forms:
            forms.append(no_apostrophe)

        for suffix, expansion in self.CONTRACTION_SUFFIX_EXPANSIONS.items():
            if normalized.endswith(suffix) and len(normalized) > len(suffix):
                if suffix == "'s" and not self._is_contraction_like(normalized):
                    continue
                stem = normalized[:-len(suffix)]
                if suffix == "n't":
                    if stem == 'ca':
                        stem = 'can'
                    elif stem == 'wo':
                        stem = 'will'
                if stem and stem not in forms:
                    forms.append(stem)
                if expansion and expansion not in forms:
                    forms.append(expansion)

        return forms

    def _is_contraction_like(self, token):
        normalized = self._normalize_english_token(token)
        if not normalized:
            return False

        if normalized in self.TOKEN_NORMALIZATION_ALIASES.values() and "'" in normalized:
            return True

        if normalized.endswith("n't") and len(normalized) > len("n't"):
            return True

        for suffix in {"'ve", "'re", "'m", "'ll", "'d"}:
            if normalized.endswith(suffix) and len(normalized) > len(suffix):
                return True

        if normalized.endswith("'s") and len(normalized) > len("'s"):
            stem = normalized[:-2]
            if stem in self.APOSTROPHE_S_CONTRACTION_BASES:
                return True

        return False

    def _canonical_part_of_speech(self, english_word, fallback=None):
        for form in self._english_lookup_forms(english_word):
            mapped = CORE_CONCEPTS.get(form)
            if mapped:
                return mapped

        normalized = self._normalize_english_token(english_word)
        if normalized and self._is_contraction_like(normalized):
            return 'Adverb' if normalized.endswith("n't") else 'Verb'

        return fallback

    def _normalize_entry_part_of_speech(self, entry_data):
        if not isinstance(entry_data, dict):
            return entry_data

        english_meaning = entry_data.get('english_meaning', '')
        current_pos = str(entry_data.get('part_of_speech') or '').strip()
        canonical_pos = self._canonical_part_of_speech(english_meaning, fallback=current_pos or None)
        if canonical_pos and canonical_pos != current_pos:
            entry_data['part_of_speech'] = canonical_pos

        return entry_data

    def _repair_lexicon_part_of_speech(self):
        for _conlang_word, entry_data in self.lexicon.entries.items():
            self._normalize_entry_part_of_speech(entry_data)

    def _merge_contraction_tokens(self, tagged_tokens):
        if not tagged_tokens:
            return []

        contraction_suffixes = {"n't", "'s", "'m", "'re", "'ve", "'d", "'ll"}
        merged = []

        for token, tag in tagged_tokens:
            token_text = str(token or '').replace('’', "'").replace('‘', "'").replace('`', "'")
            if merged and token_text in contraction_suffixes:
                previous_token, _previous_tag = merged[-1]
                if previous_token and previous_token[-1:].isalpha():
                    combined = f"{previous_token}{token_text}"
                    combined_tag = self._simple_tag_for_token(combined, is_sentence_start=False)
                    merged[-1] = (combined, combined_tag)
                    continue

            merged.append((token_text, tag))

        return merged

    def _retag_contraction_tokens(self, tagged_tokens):
        if not tagged_tokens:
            return []

        sentence_endings = {'.', '?', '!'}
        retagged = []
        is_sentence_start = True

        for token, tag in tagged_tokens:
            token_text = str(token or '')
            token_tag = tag

            normalized = self._normalize_english_token(token_text)
            if normalized.endswith("n't") and len(normalized) > len("n't"):
                stem = normalized[:-3]
                irregular_map = {
                    'ca': 'can',
                    'wo': 'will',
                    'sha': 'shall',
                    'ai': 'be',
                }
                stem = irregular_map.get(stem, stem)
                if stem:
                    expanded_tokens = [stem, 'not']
                    for expanded in expanded_tokens:
                        expanded_tag = self._simple_tag_for_token(expanded, is_sentence_start=is_sentence_start)
                        retagged.append((expanded, expanded_tag))
                        is_sentence_start = False
                    continue

            if self._is_contraction_like(token_text):
                token_tag = self._simple_tag_for_token(token_text, is_sentence_start=is_sentence_start)

            retagged.append((token_text, token_tag))

            if len(token_text) == 1 and not token_text.isalnum():
                if token_text in sentence_endings:
                    is_sentence_start = True
            else:
                is_sentence_start = False

        return retagged

    def _map_nltk_tag(self, nltk_tag):
        tag = str(nltk_tag).upper()
        if tag.startswith('NN'):
            return 'ProperNoun' if tag.endswith('P') or tag.endswith('PS') else 'Noun'
        if tag.startswith('PRP'):
            return 'Pronoun'
        if tag.startswith('VB') or tag == 'MD':
            return 'Verb'
        if tag.startswith('JJ'):
            return 'Adjective'
        if tag.startswith('RB') or tag == 'WRB':
            return 'Adverb'
        if tag.startswith('IN'):
            return 'Preposition'
        if tag == 'CC':
            return 'Conjunction'
        if tag == 'CD':
            return 'Number'
        if tag.startswith('DT') or tag in {'PDT', 'WDT'}:
            return 'Determiner'
        if tag.startswith('UH'):
            return 'Interjection'
        if tag == 'TO':
            return 'Preposition'
        if tag == 'POS':
            return 'PossessiveMarker'
        if tag == 'RP':
            return 'Adverb'
        if tag in {'EX', 'FW'}:
            return None
        return None

    def _simple_tag_for_token(self, token, is_sentence_start=False):
        if not token:
            return 'NN'

        normalized = self._normalize_english_token(token)

        if token.isdigit():
            return 'CD'

        pos_to_nltk = {
            'Noun': 'NN',
            'Verb': 'VB',
            'Adjective': 'JJ',
            'Adverb': 'RB',
            'Pronoun': 'PRP',
            'Preposition': 'IN',
            'Conjunction': 'CC',
            'Determiner': 'DT',
            'Number': 'CD',
            'ProperNoun': 'NNP',
            'Phrase': 'NN',
        }

        function_word_tags = {
            'a': 'DT',
            'an': 'DT',
            'the': 'DT',
            'this': 'DT',
            'that': 'DT',
            'these': 'DT',
            'those': 'DT',
            'some': 'DT',
            'many': 'DT',
            'few': 'DT',
            'all': 'DT',

            'i': 'PRP',
            'you': 'PRP',
            'he': 'PRP',
            'she': 'PRP',
            'it': 'PRP',
            'we': 'PRP',
            'they': 'PRP',
            'me': 'PRP',
            'him': 'PRP',
            'her': 'PRP',
            'us': 'PRP',
            'them': 'PRP',
            'my': 'PRP$',
            'your': 'PRP$',
            'his': 'PRP$',
            'its': 'PRP$',
            'our': 'PRP$',
            'their': 'PRP$',

            'and': 'CC',
            'or': 'CC',
            'but': 'CC',
            'if': 'CC',
            'because': 'CC',
            'while': 'CC',
            'although': 'CC',
            'so': 'CC',

            'in': 'IN',
            'on': 'IN',
            'at': 'IN',
            'to': 'TO',
            'of': 'IN',
            'for': 'IN',
            'by': 'IN',
            'from': 'IN',
            'with': 'IN',
            'without': 'IN',
            'under': 'IN',
            'over': 'IN',
            'between': 'IN',
            'before': 'IN',
            'after': 'IN',

            'am': 'VB',
            'is': 'VB',
            'are': 'VB',
            'was': 'VB',
            'were': 'VB',
            'be': 'VB',
            'been': 'VB',
            'being': 'VB',
            'do': 'VB',
            'does': 'VB',
            'did': 'VB',
            'have': 'VB',
            'has': 'VB',
            'had': 'VB',
            'will': 'VB',
            'shall': 'VB',
            'would': 'VB',
            'should': 'VB',
            'can': 'VB',
            'could': 'VB',
            'may': 'VB',
            'might': 'VB',
            'must': 'VB',

            "it's": 'VB',
            "i'm": 'VB',
            "you're": 'VB',
            "we're": 'VB',
            "they're": 'VB',
            "he's": 'VB',
            "she's": 'VB',
            "that's": 'VB',
            "there's": 'VB',
            "what's": 'VB',
            "who's": 'VB',
            "can't": 'VB',
            "won't": 'VB',
            "don't": 'VB',
            "doesn't": 'VB',
            "didn't": 'VB',
            "isn't": 'VB',
            "aren't": 'VB',
            "wasn't": 'VB',
            "weren't": 'VB',
            "haven't": 'VB',
            "hasn't": 'VB',
            "hadn't": 'VB',
            "should've": 'VB',
            "would've": 'VB',
            "could've": 'VB',
            "must've": 'VB',
            "i've": 'VB',
            "you've": 'VB',
            "we've": 'VB',
            "they've": 'VB',
            "i'll": 'VB',
            "you'll": 'VB',
            "we'll": 'VB',
            "they'll": 'VB',
            "i'd": 'VB',
            "you'd": 'VB',
            "we'd": 'VB',
            "they'd": 'VB',
            "let's": 'VB',
            "n't": 'RB',
            "'ve": 'VB',
            "'re": 'VB',
            "'m": 'VB',
            "'ll": 'VB',
            "'d": 'VB',
            "'s": 'VB',

            'not': 'RB',
            'never': 'RB',
            'here': 'RB',
            'there': 'RB',
            'now': 'RB',
            'soon': 'RB',
            'always': 'RB',
        }

        lookup_forms = self._english_lookup_forms(token)
        for form in lookup_forms:
            if form in function_word_tags:
                return function_word_tags[form]

        mapped = None
        for form in lookup_forms:
            mapped = CORE_CONCEPTS.get(form)
            if mapped:
                break

        if token[:1].isupper() and normalized not in {'i'} and not self._is_contraction_like(token):
            if mapped in pos_to_nltk and mapped != 'ProperNoun':
                return pos_to_nltk[mapped]

            for form in lookup_forms:
                existing_word = self.lexicon.find_by_english(form)
                if existing_word:
                    existing_entry = self.lexicon.get_entry(existing_word) or {}
                    self._normalize_entry_part_of_speech(existing_entry)
                    existing_pos = str(existing_entry.get('part_of_speech') or '').strip()
                    if existing_pos in pos_to_nltk:
                        return pos_to_nltk[existing_pos]

            return 'NNP'

        if mapped in pos_to_nltk:
            return pos_to_nltk[mapped]

        if normalized.endswith('ly'):
            return 'RB'
        if normalized.endswith(('ing', 'ed')):
            return 'VB'
        if normalized.endswith(('ous', 'al', 'ive', 'ful', 'less')):
            return 'JJ'

        if self._is_contraction_like(token):
            if normalized.endswith("n't"):
                return 'RB'
            return 'VB'

        return 'NN'

    def _tokenize_and_tag(self, english_text):
        normalized_text = str(english_text or '').replace('’', "'").replace('‘', "'").replace('`', "'")

        if self.nltk_enabled and nltk is not None:
            try:
                tokens = nltk.word_tokenize(normalized_text)
                tagged_tokens = nltk.pos_tag(tokens)
                normalized_tagged = [
                    (str(token).replace('’', "'").replace('‘', "'").replace('`', "'"), tag)
                    for token, tag in tagged_tokens
                ]
                merged_tagged = self._merge_contraction_tokens(normalized_tagged)
                return self._retag_contraction_tokens(merged_tagged)
            except Exception:
                self.nltk_enabled = False

        tokens = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)*|\d+|[^\w\s]", normalized_text)
        tagged = []
        sentence_endings = {'.', '?', '!'}
        auxiliary_words = {
            'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'do', 'does', 'did', 'have', 'has', 'had',
            'will', 'shall', 'would', 'should', 'can', 'could', 'may', 'might', 'must',
        }
        base_form_triggers = {
            'to', 'will', 'shall', 'would', 'should', 'can', 'could', 'may', 'might', 'must',
            'do', 'does', 'did',
        }
        participle_triggers = {'have', 'has', 'had'}
        progressive_triggers = {'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
        negation_words = {'not', 'never'}
        non_verb_followers = {
            'a', 'an', 'the', 'this', 'that', 'these', 'those', 'some', 'many', 'few', 'all',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
            'my', 'your', 'his', 'our', 'their',
            'and', 'or', 'but', 'if', 'because', 'while', 'although', 'so',
            'in', 'on', 'at', 'to', 'of', 'for', 'by', 'from', 'with', 'without',
            'under', 'over', 'between', 'before', 'after',
            'not',
        }

        is_sentence_start = True
        pre_previous_word = ''
        previous_word = ''
        previous_tag = ''

        for token in tokens:
            if token.isdigit():
                tag = 'CD'
            elif len(token) == 1 and not token.isalnum():
                tag = token
            else:
                lowered = self._normalize_english_token(token) or token.lower()
                if lowered == 'to':
                    tag = 'TO'
                elif lowered in auxiliary_words:
                    tag = 'VB'
                elif previous_word in base_form_triggers and lowered not in non_verb_followers:
                    tag = 'VB'
                elif previous_word in negation_words and pre_previous_word in base_form_triggers and lowered not in non_verb_followers:
                    tag = 'VB'
                elif previous_word in participle_triggers and lowered not in non_verb_followers:
                    tag = 'VBG' if lowered.endswith('ing') else 'VBN'
                elif previous_word in progressive_triggers and lowered.endswith('ing'):
                    tag = 'VBG'
                elif previous_tag == 'TO' and lowered not in non_verb_followers:
                    tag = 'VB'
                else:
                    tag = self._simple_tag_for_token(token, is_sentence_start=is_sentence_start)

            tagged.append((token, tag))

            if len(token) == 1 and not token.isalnum():
                if token in sentence_endings:
                    is_sentence_start = True
                    pre_previous_word = ''
                    previous_word = ''
                    previous_tag = ''
                else:
                    previous_tag = tag
            else:
                is_sentence_start = False
                if token.isdigit():
                    pre_previous_word = previous_word
                    previous_word = ''
                    previous_tag = 'CD'
                else:
                    pre_previous_word = previous_word
                    previous_word = self._normalize_english_token(token) or token.lower()
                    previous_tag = tag

        merged_tagged = self._merge_contraction_tokens(tagged)
        return self._retag_contraction_tokens(merged_tagged)

    def _looks_like_all_caps(self, token):
        text = str(token or '')
        letters = [char for char in text if char.isalpha()]
        return bool(letters) and all(char.isupper() for char in letters)

    def _match_source_casing(self, translated_token, source_token, capitalize_title=False):
        token = str(translated_token or '')
        source = str(source_token or '')
        if not token or not source:
            return token

        if self._looks_like_all_caps(source):
            return token.upper()

        if capitalize_title and source[:1].isupper() and token[:1].isalpha():
            return token[0].upper() + token[1:]

        return token

    def _is_likely_proper_noun(self, word, tag, is_sentence_start=False):
        tag_value = str(tag or '').upper()
        if not tag_value.startswith('NNP'):
            return False

        lookup_forms = self._english_lookup_forms(word)
        if not lookup_forms:
            return False

        lowered = lookup_forms[0]

        if self._is_contraction_like(word):
            return False

        for form in lookup_forms:
            mapped = CORE_CONCEPTS.get(form)
            if mapped and mapped != 'ProperNoun':
                return False

        for form in lookup_forms:
            existing_word = self.lexicon.find_by_english(form)
            if existing_word:
                existing_entry = self.lexicon.get_entry(existing_word) or {}
                self._normalize_entry_part_of_speech(existing_entry)
                existing_pos = str(existing_entry.get('part_of_speech') or '').strip()
                if existing_pos and existing_pos != 'ProperNoun':
                    return False
                return True

        if lowered in {'the', 'a', 'an', 'and', 'or', 'but', 'if', 'to', 'in', 'on', 'at', 'from', 'with', 'without'}:
            return False

        # Sentence-initial capitalization is ambiguous, but unknown capitalized
        # words are more likely names than grammatical words.
        if is_sentence_start:
            return True

        return True

    def _dictionary_candidate_forms(self, token):
        base = self._normalize_english_token(token) or str(token or '').strip().lower()
        if not base:
            return []

        forms = {base}
        if "'" in base:
            forms.add(base.replace("'", ''))
        frontier = {base}
        suffixes = []
        prefixes = []

        if hasattr(self.grammar_engine, 'get_affix_inventory'):
            try:
                affixes = self.grammar_engine.get_affix_inventory() or {}
                suffixes.extend([str(value).lower() for value in affixes.get('suffixes', []) if value])
                prefixes.extend([str(value).lower() for value in affixes.get('prefixes', []) if value])
            except Exception:
                pass

        if getattr(self.grammar_engine, 'plural_suffix', None):
            suffixes.append(str(self.grammar_engine.plural_suffix).lower())
        if getattr(self.grammar_engine, 'accusative_suffix', None):
            suffixes.append(str(self.grammar_engine.accusative_suffix).lower())
        if getattr(self.grammar_engine, 'genitive_suffix', None):
            suffixes.append(str(self.grammar_engine.genitive_suffix).lower())

        if getattr(self.grammar_engine, 'past_prefix', None):
            prefixes.append(str(self.grammar_engine.past_prefix).lower())
        if getattr(self.grammar_engine, 'future_prefix', None):
            prefixes.append(str(self.grammar_engine.future_prefix).lower())

        suffixes = [value for value in dict.fromkeys(suffixes) if value]
        prefixes = [value for value in dict.fromkeys(prefixes) if value]

        for _ in range(3):
            next_frontier = set()
            for current in frontier:
                for suffix in suffixes:
                    if current.endswith(suffix) and len(current) > len(suffix) + 1:
                        stripped = current[:-len(suffix)]
                        if stripped not in forms:
                            forms.add(stripped)
                            next_frontier.add(stripped)
                for prefix in prefixes:
                    if current.startswith(prefix) and len(current) > len(prefix) + 1:
                        stripped = current[len(prefix):]
                        if stripped not in forms:
                            forms.add(stripped)
                            next_frontier.add(stripped)
            if not next_frontier:
                break
            frontier = next_frontier

        return list(forms)

    def _bootstrap_lexicon(self, concepts):
        for concept, pos_tag in concepts.items():
            normalized = concept.lower()
            if self.lexicon.find_by_english(normalized):
                continue
            entry_data = self.word_generator.generate_word_for_meaning(normalized, pos_tag)
            if entry_data:
                self.lexicon.add_entry(entry_data)

    def translate_single_word(self, english_word, context_pos_tag=None):
        lookup_forms = self._english_lookup_forms(english_word)
        norm_word = lookup_forms[0] if lookup_forms else self._normalize_english_token(english_word) or str(english_word or '').lower()

        for form in lookup_forms or [norm_word]:
            conlang_word = self.lexicon.find_by_english(form)
            if conlang_word:
                existing_entry = self.lexicon.get_entry(conlang_word)
                self._normalize_entry_part_of_speech(existing_entry)
                return conlang_word

        pos_tag = context_pos_tag
        if pos_tag is None:
            for form in lookup_forms or [norm_word]:
                mapped = CORE_CONCEPTS.get(form)
                if mapped is not None:
                    pos_tag = mapped
                    break

        entry_data = self.word_generator.generate_word_for_meaning(norm_word, pos_tag)
        if entry_data:
            if self.lexicon.add_entry(entry_data):
                return entry_data['word']
            for form in lookup_forms or [norm_word]:
                existing = self.lexicon.find_by_english(form)
                if existing:
                    return existing
            return f"[{norm_word.upper()}_ADD_ERR]"
        return f"[{norm_word.upper()}_GEN_ERR]"

    def lookup_dictionary_entry(self, query):
        normalized_query = str(query or '').strip().replace('’', "'").replace('‘', "'").replace('`', "'")
        if not normalized_query:
            return {
                'query': '',
                'found': False,
                'match': None,
                'entry': None,
            }

        cleaned_query = re.sub(r"^[^A-Za-z0-9']+|[^A-Za-z0-9']+$", '', normalized_query)
        normalized_lower = self._normalize_english_token(normalized_query) or normalized_query.lower()
        cleaned_lower = self._normalize_english_token(cleaned_query) if cleaned_query else normalized_lower

        candidate_values = [
            normalized_query,
            cleaned_query,
            normalized_lower,
            cleaned_lower,
            normalized_query.capitalize(),
            cleaned_query.capitalize(),
        ]

        for form in self._dictionary_candidate_forms(cleaned_query or normalized_query):
            candidate_values.extend([form, form.capitalize()])

        candidates = []
        for candidate in candidate_values:
            if candidate and candidate not in candidates:
                candidates.append(candidate)

        for candidate in candidates:
            entry = self.lexicon.get_entry(candidate)
            if entry:
                self._normalize_entry_part_of_speech(entry)
                match_type = 'conlang_word' if candidate.lower() == cleaned_lower else 'inflected_conlang'
                return {
                    'query': normalized_query,
                    'found': True,
                    'match': match_type,
                    'entry': copy.deepcopy(entry),
                }

        english_candidates = []
        for value in [cleaned_lower, normalized_lower]:
            for form in self._english_lookup_forms(value):
                if form and form not in english_candidates:
                    english_candidates.append(form)
            if value and value not in english_candidates:
                english_candidates.append(value)
            if value and value.endswith('ing') and len(value) > 5:
                english_candidates.append(value[:-3])
            if value and value.endswith('ed') and len(value) > 4:
                english_candidates.append(value[:-2])
            if value and value.endswith('es') and len(value) > 4:
                english_candidates.append(value[:-2])
            if value and value.endswith('s') and len(value) > 3:
                english_candidates.append(value[:-1])

        for value in list(english_candidates):
            if not value:
                continue

            if value.endswith("n't") and len(value) > 3:
                stem = value[:-3]
                if stem == 'ca':
                    stem = 'can'
                elif stem == 'wo':
                    stem = 'will'
                if stem:
                    english_candidates.append(stem)
                english_candidates.append('not')

            if value and len(value) > 2 and not value.endswith('s'):
                english_candidates.append(f'{value}s')

        deduped_english_candidates = []
        for value in english_candidates:
            if value and value not in deduped_english_candidates:
                deduped_english_candidates.append(value)
        english_candidates = deduped_english_candidates

        for english_candidate in english_candidates:
            translated_word = self.lexicon.find_by_english(english_candidate)
            if translated_word:
                entry = self.lexicon.get_entry(translated_word)
                if entry:
                    self._normalize_entry_part_of_speech(entry)
                    match_type = 'english_meaning' if english_candidate == cleaned_lower else 'english_lemma'
                    return {
                        'query': normalized_query,
                        'found': True,
                        'match': match_type,
                        'entry': copy.deepcopy(entry),
                    }

        for english_candidate in english_candidates:
            for _conlang_word, entry in self.lexicon.entries.items():
                self._normalize_entry_part_of_speech(entry)
                meaning = str(entry.get('english_meaning') or '').strip().lower()
                if not meaning:
                    continue
                if meaning == english_candidate or meaning.startswith(f'{english_candidate} ') or f' {english_candidate}' in meaning:
                    return {
                        'query': normalized_query,
                        'found': True,
                        'match': 'english_contains',
                        'entry': copy.deepcopy(entry),
                    }

        return {
            'query': normalized_query,
            'found': False,
            'match': None,
            'entry': None,
        }

    def generate_proper_noun(self, english_prompt, category=None, gender=None):
        generated_name = self.noun_generator.generate_proper_noun(
            english_prompt=english_prompt,
            category=category or 'person',
            gender=gender,
        )
        if generated_name:
            return generated_name.capitalize()
        return f"[{english_prompt.upper()}_PN_GEN_ERR]"

    def generate_noun(self, english_meaning=None, noun_type='common', category='person',
                      gender=None, number='singular', grammatical_case='core'):
        return self.noun_generator.generate_noun(
            english_meaning=english_meaning,
            noun_type=noun_type,
            category=category,
            gender=gender,
            number=number,
            grammatical_case=grammatical_case,
        )

    def _reorder_grammar_clause(self, clause, clause_ending=None):
        if not clause:
            return []

        if hasattr(self.grammar_engine, 'transform_clause'):
            try:
                transformed = self.grammar_engine.transform_clause(clause, clause_ending=clause_ending)
                if transformed:
                    return transformed
            except Exception:
                pass

        pairs = [(item['token'], item['simple_pos']) for item in clause]
        reordered_pairs = self.grammar_engine.reorder_clause(pairs)

        remaining = list(clause)
        reordered = []
        for token, simple_pos in reordered_pairs:
            match_index = None
            for idx, item in enumerate(remaining):
                if item['token'] == token and item['simple_pos'] == simple_pos:
                    match_index = idx
                    break
            if match_index is None:
                continue
            reordered.append(remaining.pop(match_index))

        reordered.extend(remaining)
        return reordered

    def _apply_grammar(self, stream):
        if not stream:
            return []

        sentence_endings = {'.', '?', '!'}
        output = []
        clause = []
        for item in stream:
            if item.get('is_punctuation'):
                if clause:
                    punctuation_token = str(item.get('token') or '')
                    clause_ending = punctuation_token if punctuation_token in sentence_endings else None
                    output.extend(self._reorder_grammar_clause(clause, clause_ending=clause_ending))
                    clause = []
                output.append(item)
            else:
                clause.append(item)

        if clause:
            output.extend(self._reorder_grammar_clause(clause, clause_ending=None))

        return output

    def _render_output(self, stream):
        if not stream:
            return ''

        sentence_ending_punctuation = {'.', '?', '!'}
        output_parts = []
        start_of_sentence = True

        for idx, item in enumerate(stream):
            token = item.get('token', '')
            tag = item.get('tag', '')
            is_punctuation = item.get('is_punctuation', False)
            is_proper_noun = bool(item.get('is_proper_noun')) or item.get('simple_pos') == 'ProperNoun'

            if not token:
                continue

            if not is_punctuation and token and token[0].isalpha():
                if start_of_sentence or tag.upper().startswith('NNP') or is_proper_noun:
                    token = token[0].upper() + token[1:]

            if not output_parts:
                output_parts.append(token)
            else:
                prev = output_parts[-1]
                if is_punctuation or token in {"n't", "'s", "'m", "'re", "'ve", "'d", "'ll"}:
                    output_parts[-1] = prev + token
                else:
                    output_parts.append(' ' + token)

            if token in sentence_ending_punctuation:
                start_of_sentence = True
            elif not is_punctuation:
                start_of_sentence = False

        return ''.join(output_parts).strip()

    def _build_translated_stream(self, english_text, use_grammar=False):
        tagged_tokens = self._tokenize_and_tag(english_text)
        translated_stream = []
        sentence_endings = {'.', '?', '!'}
        is_sentence_start = True

        for word, tag in tagged_tokens:
            is_punctuation = tag in ['.', ',', ':', ';', '(', ')', '"', "'", '``', "''", '#', '$'] or (
                len(word) == 1 and not word.isalnum()
            )
            is_number = tag == 'CD'

            if is_punctuation or is_number:
                translated_stream.append({
                    'token': word,
                    'tag': tag,
                    'simple_pos': 'Punctuation' if is_punctuation else 'Number',
                    'is_punctuation': is_punctuation,
                    'is_proper_noun': False,
                    'source_token': word,
                    'source_normalized': word.lower() if word else '',
                })

                if is_punctuation and word in sentence_endings:
                    is_sentence_start = True
                elif not is_punctuation:
                    is_sentence_start = False
                continue

            simple_pos = self._map_nltk_tag(tag) or 'Noun'
            normalized_word = self._normalize_english_token(word) or word.lower()
            is_proper_noun = self._is_likely_proper_noun(word, tag, is_sentence_start=is_sentence_start)

            if is_proper_noun:
                existing_name = None
                for form in self._english_lookup_forms(word):
                    existing_name = self.lexicon.find_by_english(form)
                    if existing_name:
                        break
                if existing_name is None:
                    existing_name = self.lexicon.find_by_english(normalized_word) or self.lexicon.find_by_english(word)
                translated = existing_name if existing_name else self.generate_proper_noun(word, category='person')
                translated = self._match_source_casing(translated, word, capitalize_title=True)
                simple_pos = 'ProperNoun'
            else:
                if str(tag).upper().startswith('NNP') and simple_pos == 'ProperNoun':
                    simple_pos = 'Noun'
                translated = self.translate_single_word(normalized_word, context_pos_tag=simple_pos)
                translated = self._match_source_casing(translated, word, capitalize_title=False)

            translated_stream.append({
                'token': translated,
                'tag': tag,
                'simple_pos': simple_pos,
                'is_punctuation': False,
                'is_proper_noun': is_proper_noun,
                'source_token': word,
                'source_normalized': normalized_word,
            })
            is_sentence_start = False

        if use_grammar:
            translated_stream = self._apply_grammar(translated_stream)

        return translated_stream

    def translate(self, english_text, use_grammar=False):
        translated_stream = self._build_translated_stream(english_text, use_grammar=use_grammar)
        return self._render_output(translated_stream)

    def translate_with_breakdown(self, english_text, use_grammar=False):
        translated_stream = self._build_translated_stream(english_text, use_grammar=use_grammar)
        translated_text = self._render_output(translated_stream)

        breakdown = []
        dictionary_words = {}

        for item in translated_stream:
            source_token = item.get('source_token', item.get('token', ''))
            translated_token = item.get('token', '')
            simple_pos = item.get('simple_pos', '')
            is_punctuation = bool(item.get('is_punctuation'))
            is_number = simple_pos == 'Number'
            is_grammar_particle = simple_pos in {'Particle', 'CaseParticle', 'NegationParticle', 'QuestionParticle'}
            lookup_match = None

            dictionary_entry = None
            if not is_punctuation and not is_number and not is_grammar_particle and translated_token:
                lookup = self.lookup_dictionary_entry(translated_token)
                if lookup.get('found') and lookup.get('entry'):
                    dictionary_entry = lookup['entry']
                    self._normalize_entry_part_of_speech(dictionary_entry)
                    lookup_match = lookup.get('match')

                    dictionary_pos = dictionary_entry.get('part_of_speech', simple_pos) or simple_pos
                    if not bool(item.get('is_proper_noun')) and dictionary_pos == 'ProperNoun':
                        dictionary_pos = self._canonical_part_of_speech(
                            dictionary_entry.get('english_meaning', ''),
                            fallback=simple_pos if simple_pos != 'ProperNoun' else 'Noun',
                        )

                    dictionary_words[dictionary_entry.get('word', translated_token)] = {
                        'word': dictionary_entry.get('word', translated_token),
                        'english_meaning': dictionary_entry.get('english_meaning', ''),
                        'part_of_speech': dictionary_pos,
                        'prefix': dictionary_entry.get('prefix', ''),
                        'root': dictionary_entry.get('root', ''),
                        'suffix': dictionary_entry.get('suffix', ''),
                        'match': lookup_match,
                    }

            if dictionary_entry:
                english_meaning = dictionary_entry.get('english_meaning', '') or item.get('source_normalized', '')
                part_of_speech = dictionary_entry.get('part_of_speech', simple_pos) or simple_pos
                if not bool(item.get('is_proper_noun')) and part_of_speech == 'ProperNoun':
                    part_of_speech = self._canonical_part_of_speech(
                        english_meaning,
                        fallback=simple_pos if simple_pos != 'ProperNoun' else 'Noun',
                    )
                prefix = dictionary_entry.get('prefix', '')
                root = dictionary_entry.get('root', '')
                suffix = dictionary_entry.get('suffix', '')
            else:
                english_meaning = source_token if is_punctuation else item.get('source_normalized', source_token)
                part_of_speech = simple_pos
                prefix = ''
                root = ''
                suffix = ''

            breakdown.append({
                'source_token': source_token,
                'translated_token': translated_token,
                'english_meaning': english_meaning,
                'part_of_speech': part_of_speech,
                'is_punctuation': is_punctuation,
                'is_number': is_number,
                'is_proper_noun': bool(item.get('is_proper_noun')),
                'lookup_match': lookup_match,
                'prefix': prefix,
                'root': root,
                'suffix': suffix,
            })

        return {
            'translated': translated_text,
            'breakdown': breakdown,
            'dictionary': list(dictionary_words.values()),
        }

    def translate_with_grammar(self, english_text):
        return self.translate(english_text, use_grammar=True)

    def apply_sound_changes_to_word(self, word, additional_rules=None):
        if not additional_rules:
            return self.sound_change_engine.apply_to_word(word)

        merged_rules = self.sound_change_engine.get_config() + additional_rules
        temp_engine = SoundChangeEngine(rules=merged_rules)
        return temp_engine.apply_to_word(word)

    def switch_style_preset(self, preset_name, regenerate_lexicon=False, bootstrap=True):
        template = get_template_config(preset_name)

        self.template_name = template['template_name']
        self.style_preset = template['template_name']
        self.metadata['template_description'] = template.get('description', '')
        if template.get('region'):
            self.metadata['template_region'] = template.get('region')
        if template.get('source_language_code'):
            self.metadata['source_language_code'] = template.get('source_language_code')
        if template.get('is_pseudo_real_world') is not None:
            self.metadata['is_pseudo_real_world'] = bool(template.get('is_pseudo_real_world'))
        if template.get('wordfreq_enabled') is not None:
            self.metadata['wordfreq_enabled'] = bool(template.get('wordfreq_enabled'))

        previous_lexicon = self.lexicon

        self.phonology = Phonology(config=template['phonology'])
        self.morphology = Morphology(phonology=self.phonology, config=None, **template['morphology'])
        self.evaluator = PronounceabilityEvaluator(
            phonology=self.phonology,
            min_score=self.evaluator.min_score,
        )

        if regenerate_lexicon:
            self.lexicon = Lexicon()
        else:
            self.lexicon = previous_lexicon

        wordgen_cfg = deep_merge(copy.deepcopy(self.DEFAULT_WORDGEN_PARAMS), template['word_generator_params'])
        namegen_cfg = deep_merge(copy.deepcopy(self.DEFAULT_NAMEGEN_PARAMS), template['name_generator_params'])
        namegen_cfg['evaluator'] = self.evaluator
        namegen_cfg['min_pronounceability_score'] = self.evaluator.min_score

        self.word_generator = WordGenerator(
            phonology=self.phonology,
            morphology=self.morphology,
            lexicon=self.lexicon,
            evaluator=self.evaluator,
            min_pronounceability_score=self.evaluator.min_score,
            **wordgen_cfg,
        )
        self.name_generator = NameGenerator(
            phonology=self.phonology,
            lexicon=self.lexicon,
            name_params=namegen_cfg,
        )
        self.grammar_engine = GrammarEngine(phonology=self.phonology, config=template['grammar'])
        self.noun_generator = NounGenerator(
            word_generator=self.word_generator,
            name_generator=self.name_generator,
            lexicon=self.lexicon,
            grammar_engine=self.grammar_engine,
            evaluator=self.evaluator,
        )
        self.sound_change_engine = SoundChangeEngine(rules=template.get('sound_change_rules', []))

        if regenerate_lexicon and bootstrap:
            self._bootstrap_lexicon(CORE_CONCEPTS)

        self._repair_lexicon_part_of_speech()

        return self.style_preset

    def derive_daughter_language(self, preset_name='lenition', custom_rules=None, metadata=None):
        rules = SoundChangeEngine.preset_rules(preset_name)
        if custom_rules:
            rules.extend(custom_rules)

        if not rules:
            return None

        engine = SoundChangeEngine(rules=rules)
        base_config = self.get_config()
        derived_config = engine.apply_to_language_config(base_config)

        combined_metadata = self.metadata.copy()
        if metadata:
            combined_metadata.update(metadata)
        combined_metadata['derived_from_template'] = self.template_name
        combined_metadata['sound_change_preset'] = preset_name

        return Language.from_config(derived_config, metadata=combined_metadata, bootstrap=False)

    def get_config(self):
        wordgen_cfg = {
            'prefix_prob': self.word_generator.prefix_prob,
            'suffix_prob': self.word_generator.suffix_prob,
            'max_gen_attempts': self.word_generator.max_gen_attempts,
            'compact_function_words': self.word_generator.compact_function_words,
            'function_word_pos_tags': sorted(self.word_generator.function_word_pos_tags),
            'function_word_meanings': sorted(self.word_generator.function_word_meanings),
            'function_word_min_syl': self.word_generator.function_word_min_syl,
            'function_word_max_syl': self.word_generator.function_word_max_syl,
            'function_word_long_form_chance': self.word_generator.function_word_long_form_chance,
            'function_word_allow_affixes': self.word_generator.function_word_allow_affixes,
            'function_word_max_chars': self.word_generator.function_word_max_chars,
        }

        namegen_cfg = {
            'person_min_syl': self.name_generator.person_min_syl,
            'person_max_syl': self.name_generator.person_max_syl,
            'place_min_syl': self.name_generator.place_min_syl,
            'place_max_syl': self.name_generator.place_max_syl,
            'thing_min_syl': self.name_generator.thing_min_syl,
            'thing_max_syl': self.name_generator.thing_max_syl,
            'person_male_suffixes': self.name_generator.person_male_suffixes,
            'person_female_suffixes': self.name_generator.person_female_suffixes,
            'person_neutral_suffixes': self.name_generator.person_neutral_suffixes,
            'place_suffixes': self.name_generator.place_suffixes,
            'thing_suffixes': self.name_generator.thing_suffixes,
            'person_suffix_prob': self.name_generator.person_suffix_prob,
            'place_suffix_prob': self.name_generator.place_suffix_prob,
            'thing_suffix_prob': self.name_generator.thing_suffix_prob,
            'max_attempts': self.name_generator.max_attempts,
        }

        return {
            'template_name': self.template_name,
            'style_preset': self.style_preset,
            'phonology': self.phonology.get_config(),
            'morphology': self.morphology.get_config(),
            'lexicon': self.lexicon.get_config(),
            'word_generator_params': wordgen_cfg,
            'name_generator_params': namegen_cfg,
            'grammar': self.grammar_engine.get_config(),
            'sound_change_rules': self.sound_change_engine.get_config(),
            'generation_quality': {
                'min_pronounceability_score': self.evaluator.min_score,
            },
        }

    def to_package(self, metadata=None):
        package_metadata = {
            'created_at': self.metadata.get('created_at') or datetime.datetime.utcnow().isoformat() + 'Z',
            'updated_at': datetime.datetime.utcnow().isoformat() + 'Z',
            'template_name': self.template_name,
            'style_preset': self.style_preset,
        }
        package_metadata.update(self.metadata)
        if metadata:
            package_metadata.update(metadata)

        return {
            'schema_version': 2,
            'metadata': package_metadata,
            'language': self.get_config(),
        }

    def save(self, filepath, metadata=None):
        try:
            package = self.to_package(metadata=metadata)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as file_handle:
                json.dump(package, file_handle, ensure_ascii=False, indent=4)
            return True
        except Exception:
            return False

    @staticmethod
    def load(filepath):
        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as file_handle:
                raw = json.load(file_handle)

            metadata = {}
            if isinstance(raw, dict) and 'language' in raw and isinstance(raw.get('language'), dict):
                metadata = raw.get('metadata', {}) if isinstance(raw.get('metadata'), dict) else {}
                config = raw['language']
            else:
                config = raw

            if not isinstance(config, dict):
                return None

            if 'phonology' not in config or 'morphology' not in config or 'lexicon' not in config:
                return None

            return Language.from_config(config=config, metadata=metadata, bootstrap=False)
        except Exception:
            return None
