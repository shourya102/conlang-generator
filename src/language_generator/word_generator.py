import random

from src.language_generator.lexicon import Lexicon
from src.language_generator.morphology import Morphology
from src.language_generator.phonology import Phonology


DEFAULT_FUNCTION_WORD_POS_TAGS = {
    'pronoun',
    'preposition',
    'conjunction',
    'determiner',
    'interjection',
    'possessivemarker',
}

DEFAULT_FUNCTION_WORD_MEANINGS = {
    'a', 'an', 'the',
    'and', 'or', 'but', 'if', 'so',
    'in', 'on', 'at', 'to', 'of', 'for', 'by', 'from', 'with', 'without',
    'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'us', 'them',
    'my', 'your', 'his', 'her', 'our', 'their',
    'is', 'are', 'was', 'were',
    'not', 'no', 'yes',
}


class WordGenerator:
    def __init__(self, phonology, morphology, lexicon,
                 prefix_prob=0.2,
                 suffix_prob=0.4,
                 name_min_syl=2,
                 name_max_syl=4,
                 name_allow_prefix=False,
                 name_allow_suffix=False,
                 evaluator=None,
                 min_pronounceability_score=58,
                 max_gen_attempts=50,
                 compact_function_words=True,
                 function_word_pos_tags=None,
                 function_word_meanings=None,
                 function_word_min_syl=1,
                 function_word_max_syl=1,
                 function_word_long_form_chance=0.15,
                 function_word_allow_affixes=False,
                 function_word_max_chars=5):
        if not isinstance(phonology, Phonology): raise TypeError("Warning: Phonology required.")
        if not isinstance(morphology, Morphology): raise TypeError("Warning: Morphology required.")
        if not isinstance(lexicon, Lexicon): raise TypeError("Warning: Lexicon required.")
        self.phonology = phonology
        self.morphology = morphology
        self.lexicon = lexicon
        self.prefix_prob = prefix_prob
        self.suffix_prob = suffix_prob
        self.name_min_syl = name_min_syl
        self.name_max_syl = name_max_syl
        self.name_allow_prefix = name_allow_prefix
        self.name_allow_suffix = name_allow_suffix
        self.evaluator = evaluator
        self.min_pronounceability_score = int(min_pronounceability_score)
        self.max_gen_attempts = max_gen_attempts
        self.compact_function_words = bool(compact_function_words)

        raw_pos_tags = function_word_pos_tags if function_word_pos_tags is not None else DEFAULT_FUNCTION_WORD_POS_TAGS
        self.function_word_pos_tags = {
            str(tag).strip().lower()
            for tag in raw_pos_tags
            if str(tag).strip()
        }
        if not self.function_word_pos_tags:
            self.function_word_pos_tags = set(DEFAULT_FUNCTION_WORD_POS_TAGS)

        raw_meanings = function_word_meanings if function_word_meanings is not None else DEFAULT_FUNCTION_WORD_MEANINGS
        self.function_word_meanings = {
            str(meaning).strip().lower()
            for meaning in raw_meanings
            if str(meaning).strip()
        }
        if not self.function_word_meanings:
            self.function_word_meanings = set(DEFAULT_FUNCTION_WORD_MEANINGS)

        self.function_word_min_syl = max(1, int(function_word_min_syl))
        self.function_word_max_syl = max(self.function_word_min_syl, int(function_word_max_syl))
        self.function_word_long_form_chance = max(0.0, min(1.0, float(function_word_long_form_chance)))
        self.function_word_allow_affixes = bool(function_word_allow_affixes)
        self.function_word_max_chars = max(1, int(function_word_max_chars))

        print("WordGenerator Initialized.")
        print(f"  Prefix Prob: {self.prefix_prob}, Suffix Prob: {self.suffix_prob}")
        print(f"  Name Syls: {self.name_min_syl}-{self.name_max_syl}")
        print(f"  Compact Function Words: {self.compact_function_words}")
        print("-" * 20)

    def _is_candidate_acceptable(self, candidate):
        if not candidate:
            return False
        if self.evaluator is None:
            return True
        return self.evaluator.is_acceptable(candidate, min_score=self.min_pronounceability_score)

    def _generate_morphological_form(self, allow_prefix=True, allow_suffix=True):
        root = self.morphology.get_random_root()
        if not root:
            return None, None, None, None
        prefix = self.morphology.get_random_prefix() if allow_prefix and random.random() < self.prefix_prob else ""
        suffix = self.morphology.get_random_suffix() if allow_suffix and random.random() < self.suffix_prob else ""
        prefix = prefix if prefix else ""
        suffix = suffix if suffix else ""
        word = self.phonology.join_segments(prefix, root, suffix)
        if word and self.phonology.is_valid_sequence(word) and self._is_candidate_acceptable(word):
            return word, prefix, root, suffix
        return None, None, None, None

    def _is_function_word_target(self, english_meaning, part_of_speech):
        if not self.compact_function_words:
            return False

        pos_key = str(part_of_speech or '').strip().lower()
        if pos_key and pos_key in self.function_word_pos_tags:
            return True

        meaning_key = str(english_meaning or '').strip().lower()
        return bool(meaning_key and meaning_key in self.function_word_meanings)

    def _generate_compact_function_form(self):
        for _ in range(self.max_gen_attempts):
            max_syllables = self.function_word_max_syl
            if random.random() < self.function_word_long_form_chance:
                max_syllables += 1

            root = self.phonology.generate_word(
                min_syllables=self.function_word_min_syl,
                max_syllables=max_syllables,
                max_tries=20,
            )
            if not root:
                continue

            prefix = ''
            suffix = ''
            if self.function_word_allow_affixes:
                if random.random() < (self.prefix_prob * 0.25):
                    prefix = self.morphology.get_random_prefix() or ''
                if random.random() < (self.suffix_prob * 0.25):
                    suffix = self.morphology.get_random_suffix() or ''

            word = self.phonology.join_segments(prefix, root, suffix)
            if not word:
                continue
            if len(word) > self.function_word_max_chars:
                continue
            if self.phonology.is_valid_sequence(word) and self._is_candidate_acceptable(word):
                return word, prefix, root, suffix

        return None, None, None, None

    def generate_word_for_meaning(self, english_meaning, part_of_speech=None):
        is_function_word = self._is_function_word_target(english_meaning, part_of_speech)

        for attempt in range(self.max_gen_attempts):
            if is_function_word:
                potential_word, prefix, root, suffix = self._generate_compact_function_form()
                if not potential_word:
                    potential_word, prefix, root, suffix = self._generate_morphological_form(
                        allow_prefix=False,
                        allow_suffix=False,
                    )
            else:
                potential_word, prefix, root, suffix = self._generate_morphological_form()

            if potential_word:
                existing_entry = self.lexicon.get_entry(potential_word)
                if existing_entry:
                    if existing_entry.get('english_meaning') != english_meaning:
                        # print(f"Debug: Word '{potential_word}' exists with different meaning. Retrying.")
                        continue
                    else:
                        continue
                else:
                    existing_translation = self.lexicon.find_by_english(english_meaning)
                    if existing_translation and existing_translation != potential_word:
                        print(
                            f"Error: Meaning '{english_meaning}' already exists as '{existing_translation}'. Cannot generate '{potential_word}'.")
                        return None
                    return {
                        'word': potential_word,
                        'prefix': prefix,
                        'root': root,
                        'suffix': suffix,
                        'english_meaning': english_meaning,
                        'part_of_speech': part_of_speech
                    }
        print(
            f"Warning: Failed to generate unique word for meaning '{english_meaning}' after {self.max_gen_attempts} attempts.")
        return None

    def generate_name_candidate(self):
        for _ in range(self.max_gen_attempts):
            num_syllables = random.randint(self.name_min_syl, self.name_max_syl)
            if num_syllables <= 0:
                continue
            candidate = self.phonology.generate_word(
                min_syllables=num_syllables,
                max_syllables=num_syllables,
                max_tries=20,
            )
            if (
                candidate
                and self.phonology.is_valid_sequence(candidate)
                and self._is_candidate_acceptable(candidate)
            ):
                return candidate
        return None
