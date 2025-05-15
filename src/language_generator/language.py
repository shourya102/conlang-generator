import json
import os

import nltk

from src.language_generator.core_concepts import CORE_CONCEPTS
from src.language_generator.lexicon import Lexicon
from src.language_generator.morphology import Morphology
from src.language_generator.name_generator import NameGenerator
from src.language_generator.phonology import Phonology
from src.language_generator.word_generator import WordGenerator


class Language:
    DEFAULT_PHONOLOGY_PARAMS = {
        'consonants': ['p', 't', 'c', 'b', 'd', 'g', 'm', 'n', 'l', 'r', 's', 'f', 'v', 'h', 'x'],
        'vowels': ['a', 'e', 'i', 'o', 'u', 'ae', 'oe', 'au'],
        'syllable_structures': ['CV', 'CVC', 'V', 'VC'],
        'onsets': ['p', 't', 'c', 'b', 'd', 'g', 'm', 'n', 'l', 'r', 's', 'f', 'v', 'h',
                   'st', 'tr', 'pr', 'cl', 'cr', 'pl', 'bl', 'gl', 'fl', ''],
        'codas': ['m', 'n', 'l', 'r', 's', 't', ''],
        'illegal_sequences': ['pp', 'tt', 'cc', 'bb', 'dd', 'gg', 'hh', 'vv', 'ff',
                              'aa', 'ee', 'ii', 'oo', 'uu', 'sx', 'bx', 'vx', 'hx']
    }
    DEFAULT_MORPHOLOGY_PARAMS = {
        'num_roots': 400, 'num_prefixes': 40, 'num_suffixes': 80,
        'root_min_syl': 1, 'root_max_syl': 2, 'affix_max_syl': 1
    }
    DEFAULT_WORDGEN_PARAMS = {
        'prefix_prob': 0.20, 'suffix_prob': 0.35,
        'max_gen_attempts': 100
    }
    DEFAULT_NAMEGEN_PARAMS = {
        'person_min_syl': 2, 'person_max_syl': 3,
        'place_min_syl': 2, 'place_max_syl': 4,
        'thing_min_syl': 1, 'thing_max_syl': 3,
        'person_male_suffixes': ['us', 'or', 'an', 'ius'],
        'person_female_suffixes': ['a', 'ia', 'ina', 'illa'],
        'person_neutral_suffixes': ['is', 'en', 'o', 'um'],
        'place_suffixes': ['ia', 'um', 'os', 'ana', 'polis', 'burg', 'acum'],
        'thing_suffixes': ['ex', 'or', 'mentum', 'io', 'ura'],
        'person_suffix_prob': 0.75,
        'place_suffix_prob': 0.65,
        'thing_suffix_prob': 0.30,
        'max_attempts': 100
    }

    def __init__(self, phonology=None, morphology=None, lexicon=None,
                 word_generator=None, name_generator=None, bootstrap=True):
        self._ensure_nltk_data()

        self.phonology = phonology if phonology else Phonology(config=self.DEFAULT_PHONOLOGY_PARAMS)
        self.morphology = morphology if morphology else Morphology(
            phonology=self.phonology, config=None, **self.DEFAULT_MORPHOLOGY_PARAMS
        )
        self.lexicon = lexicon if lexicon else Lexicon()
        self.word_generator = word_generator if word_generator else WordGenerator(
            phonology=self.phonology, morphology=self.morphology, lexicon=self.lexicon,
            **self.DEFAULT_WORDGEN_PARAMS
        )
        self.name_generator = name_generator if name_generator else NameGenerator(
            phonology=self.phonology,
            lexicon=self.lexicon,
            name_params=self.DEFAULT_NAMEGEN_PARAMS
        )
        if bootstrap and self.lexicon.get_size() < len(CORE_CONCEPTS) // 2:
            self._bootstrap_lexicon(CORE_CONCEPTS)

    def _ensure_nltk_data(self):
        required_packages = ['punkt', 'averaged_perceptron_tagger']
        try:
            for package in required_packages:
                nltk.data.find(f'tokenizers/{package}' if package == 'punkt' else f'taggers/{package}')
        except LookupError:
            try:
                for package in required_packages:
                    nltk.download(package, quiet=True)
            except Exception as e:
                pass
        except Exception as e:
            pass

    def _map_nltk_tag(self, nltk_tag):
        tag = nltk_tag.upper()
        if tag.startswith('NN'):
            return 'ProperNoun' if tag.endswith('P') or tag.endswith('PS') else 'Noun'
        elif tag.startswith('PRP'):
            return 'Pronoun'
        elif tag.startswith('VB') or tag == 'MD':
            return 'Verb'
        elif tag.startswith('JJ'):
            return 'Adjective'
        elif tag.startswith('RB') or tag == 'WRB':
            return 'Adverb'
        elif tag.startswith('IN'):
            return 'Preposition'
        elif tag == 'CC':
            return 'Conjunction'
        elif tag == 'CD':
            return 'Number'
        elif tag.startswith('DT') or tag == 'PDT' or tag == 'WDT':
            return 'Determiner'
        elif tag.startswith('UH'):
            return 'Interjection'
        elif tag == 'TO':
            return 'Preposition'
        elif tag == 'POS':
            return 'PossessiveMarker'
        elif tag == 'RP':
            return 'Adverb'
        elif tag in ['EX', 'FW']:
            return None
        else:
            return None

    def _bootstrap_lexicon(self, concepts):
        added_count = 0
        failed_count = 0
        for concept, pos_tag in concepts.items():
            if self.lexicon.find_by_english(concept):
                continue
            entry_data = self.word_generator.generate_word_for_meaning(concept, pos_tag)
            if entry_data:
                if self.lexicon.add_entry(entry_data):
                    added_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1

    def translate_single_word(self, english_word, context_pos_tag=None):
        norm_word = english_word.lower()
        conlang_word = self.lexicon.find_by_english(norm_word)
        if conlang_word:
            return conlang_word
        pos_tag = context_pos_tag or CORE_CONCEPTS.get(norm_word, None)
        entry_data = self.word_generator.generate_word_for_meaning(norm_word, pos_tag)
        if entry_data:
            if self.lexicon.add_entry(entry_data):
                return entry_data['word']
            else:
                existing = self.lexicon.find_by_english(norm_word)
                if existing: return existing
                return f"[{norm_word.upper()}_ADD_ERR]"
        else:
            return f"[{norm_word.upper()}_GEN_ERR]"

    def generate_proper_noun(self, english_prompt, category=None, gender=None):
        generated_name = None
        if category == 'person':
            generated_name = self.name_generator.generate_person_name(gender=gender)
        elif category == 'place':
            generated_name = self.name_generator.generate_place_name()
        elif category == 'thing':
            generated_name = self.name_generator.generate_thing_name()
        else:
            generated_name = self.name_generator.generate_person_name(gender=gender)
        if generated_name:
            entry_data = {
                'word': generated_name, 'prefix': '', 'root': generated_name, 'suffix': '',
                'english_meaning': english_prompt, 'part_of_speech': 'ProperNoun'
            }
            if self.lexicon.add_entry(entry_data):
                return generated_name.capitalize()
            else:
                return f"[{english_prompt.upper()}_PN_ADD_ERR]"
        else:
            return f"[{english_prompt.upper()}_PN_GEN_ERR]"

    def translate(self, english_text):
        try:
            tokens = nltk.word_tokenize(english_text)
            tagged_tokens = nltk.pos_tag(tokens)
        except Exception as e:
            return "[NLTK Processing Error]"
        translated_output = []
        previous_token_was_sentence_end = True
        sentence_ending_punctuation = ['.', '?', '!']
        for word, tag in tagged_tokens:
            is_punctuation = tag in ['.', ',', ':', '(', ')', '"', "'", '``', "''", '#', '$'] or (
                    len(word) == 1 and not word.isalnum())
            is_number = (tag == 'CD')
            if is_punctuation or is_number:
                translated_output.append((word, tag, previous_token_was_sentence_end))
                if word in sentence_ending_punctuation:
                    previous_token_was_sentence_end = True
                elif word not in ['(', '"', '``', '#', '$']:
                    previous_token_was_sentence_end = False
                continue
            translated = None
            original_word = word
            lower_word = word.lower()
            simple_pos_tag = self._map_nltk_tag(tag)
            is_nltk_proper_noun_tag = tag.upper().startswith('NNP')
            if is_nltk_proper_noun_tag:
                conlang_name = self.lexicon.find_by_english(original_word)
                if conlang_name:
                    translated = conlang_name
                else:
                    existing_lower = self.lexicon.find_by_english(lower_word)
                    if existing_lower:
                        lower_entry = self.lexicon.get_entry(existing_lower)
                        if lower_entry and lower_entry.get('part_of_speech') != 'ProperNoun':
                            translated = existing_lower
                        else:
                            translated = self.generate_proper_noun(original_word, category='person')
                    else:
                        translated = self.generate_proper_noun(original_word, category='person')
            else:
                translated = self.translate_single_word(lower_word, context_pos_tag=simple_pos_tag)
            translated_output.append((translated, tag, previous_token_was_sentence_end))
            previous_token_was_sentence_end = False
        output_text = ""
        if translated_output:
            for i, (token_str, nltk_tag, was_preceded_by_sentence_end) in enumerate(translated_output):
                current_output_token = token_str
                is_punctuation_or_number = nltk_tag in ['.', ',', ':', '(', ')', '"', "'", '``', "''", '#', '$', 'CD',
                                                        'POS'] or (
                                                   len(str(token_str)) == 1 and not str(token_str).isalnum())
                looks_like_word = token_str and not str(token_str).startswith('[') and not is_punctuation_or_number
                if looks_like_word and was_preceded_by_sentence_end:
                    if current_output_token and len(current_output_token) > 0 and current_output_token[0].isalpha():
                        current_output_token = current_output_token[0].upper() + current_output_token[1:]
                elif looks_like_word and nltk_tag.upper().startswith('NNP'):
                    if current_output_token and len(current_output_token) > 0 and current_output_token[0].isalpha():
                        current_output_token = current_output_token[0].upper() + current_output_token[1:]

                output_text += current_output_token
                if i + 1 < len(translated_output):
                    next_token_str, next_nltk_tag, _ = translated_output[i + 1]
                    if (next_nltk_tag not in ['.', ',', ':', ')', '"', "'", "''", ';', '%',
                                              'POS'] and next_token_str not in ["n't", "'s", "'m", "'re", "'ve", "'d",
                                                                                "'ll"]):
                        if nltk_tag not in ['(', '"', '``', '#', '$']:
                            output_text += " "
        return output_text.strip()

    def get_config(self):
        wordgen_cfg = {
            'prefix_prob': self.word_generator.prefix_prob,
            'suffix_prob': self.word_generator.suffix_prob,
            'max_gen_attempts': self.word_generator.max_gen_attempts
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
            'max_attempts': self.name_generator.max_attempts
        }
        return {
            "phonology": self.phonology.get_config(),
            "morphology": self.morphology.get_config(),
            "lexicon": self.lexicon.get_config(),
            "word_generator_params": wordgen_cfg,
            "name_generator_params": namegen_cfg
        }

    def save(self, filepath):
        try:
            config = self.get_config()
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            return False

    @staticmethod
    def load(filepath):
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            phonology_cfg = config.get('phonology')
            morphology_cfg = config.get('morphology')
            lexicon_cfg = config.get('lexicon')
            wordgen_params = config.get('word_generator_params', Language.DEFAULT_WORDGEN_PARAMS)
            namegen_params = config.get('name_generator_params', Language.DEFAULT_NAMEGEN_PARAMS)
            morphology_gen_params = config.get('morphology', {}).get('params', Language.DEFAULT_MORPHOLOGY_PARAMS)

            if not phonology_cfg or not morphology_cfg or not lexicon_cfg:
                raise ValueError("Invalid config file: Missing core sections.")
            lexicon = Lexicon(config=lexicon_cfg)
            phonology = Phonology(config=phonology_cfg)
            morphology = Morphology(phonology=phonology, config=morphology_cfg)
            word_generator = WordGenerator(
                phonology=phonology, morphology=morphology, lexicon=lexicon,
                prefix_prob=wordgen_params.get('prefix_prob'),
                suffix_prob=wordgen_params.get('suffix_prob'),
                max_gen_attempts=wordgen_params.get('max_gen_attempts')
            )
            name_generator = NameGenerator(
                phonology=phonology, lexicon=lexicon,
                name_params=namegen_params
            )
            language_instance = Language(
                phonology=phonology_cfg,
                morphology=morphology_gen_params,
                word_generator=wordgen_params,
                name_generator=namegen_params,
                lexicon=lexicon,
                bootstrap=False
            )
            language_instance.phonology = phonology
            language_instance.morphology = morphology
            language_instance.lexicon = lexicon
            language_instance.word_generator = word_generator
            language_instance.name_generator = name_generator
            return language_instance
        except Exception as e:
            return None
