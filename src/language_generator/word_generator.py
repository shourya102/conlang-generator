import random

from src.language_generator.lexicon import Lexicon
from src.language_generator.morphology import Morphology
from src.language_generator.phonology import Phonology


class WordGenerator:
    def __init__(self, phonology, morphology, lexicon,
                 prefix_prob=0.2,
                 suffix_prob=0.4,
                 name_min_syl=2,
                 name_max_syl=4,
                 name_allow_prefix=False,
                 name_allow_suffix=False,
                 max_gen_attempts=50):
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
        self.max_gen_attempts = max_gen_attempts

        print("WordGenerator Initialized.")
        print(f"  Prefix Prob: {self.prefix_prob}, Suffix Prob: {self.suffix_prob}")
        print(f"  Name Syls: {self.name_min_syl}-{self.name_max_syl}")
        print("-" * 20)

    def _generate_morphological_form(self, allow_prefix=True, allow_suffix=True):
        root = self.morphology.get_random_root()
        if not root: return None, None, None
        prefix = self.morphology.get_random_prefix() if allow_prefix and random.random() < self.prefix_prob else ""
        suffix = self.morphology.get_random_suffix() if allow_suffix and random.random() < self.suffix_prob else ""
        prefix = prefix if prefix else ""
        suffix = suffix if suffix else ""
        word = prefix + root + suffix
        if word and self.phonology.is_valid_sequence(word):
            if word != root or (not prefix and not suffix):
                return word, prefix, root, suffix
        return None, None, None, None

    def generate_word_for_meaning(self, english_meaning, part_of_speech=None):
        for attempt in range(self.max_gen_attempts):
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
            if num_syllables <= 0: continue
            name_syllables = []
            valid_name = True
            for _ in range(num_syllables):
                syllable = self.phonology.generate_syllable()
                if syllable is None:
                    valid_name = False
                    break
                name_syllables.append(syllable)
            if valid_name:
                candidate = "".join(name_syllables)
                if candidate and self.phonology.is_valid_sequence(candidate):
                    return candidate
        return None
