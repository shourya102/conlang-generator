import random


class NameGenerator:
    DEFAULT_NAME_PARAMS = {
        'person_min_syl': 2,
        'person_max_syl': 3,
        'place_min_syl': 2,
        'place_max_syl': 4,
        'thing_min_syl': 1,
        'thing_max_syl': 3,
        'person_male_suffixes': ['us', 'or', 'an'],
        'person_female_suffixes': ['a', 'ia', 'ina'],
        'person_neutral_suffixes': ['is', 'en', 'o'],
        'place_suffixes': ['ia', 'um', 'os', 'ana', 'polis', 'burg'],
        'thing_suffixes': ['ex', 'or', 'mentum', 'io'],
        'person_suffix_prob': 0.7,
        'place_suffix_prob': 0.6,
        'thing_suffix_prob': 0.3,
        'max_attempts': 100
    }

    def __init__(self, phonology, lexicon, name_params=None):
        if phonology is None: raise ValueError("NameGenerator requires a Phonology instance.")
        if lexicon is None: raise ValueError("NameGenerator requires a Lexicon instance.")
        self.phonology = phonology
        self.lexicon = lexicon
        params = name_params if name_params else self.DEFAULT_NAME_PARAMS
        self.evaluator = params.get('evaluator')
        self.min_pronounceability_score = int(params.get('min_pronounceability_score', 58))
        self.person_min_syl = params.get('person_min_syl', 2)
        self.person_max_syl = params.get('person_max_syl', 3)
        self.place_min_syl = params.get('place_min_syl', 2)
        self.place_max_syl = params.get('place_max_syl', 4)
        self.thing_min_syl = params.get('thing_min_syl', 1)
        self.thing_max_syl = params.get('thing_max_syl', 3)
        self.person_male_suffixes = params.get('person_male_suffixes', [])
        self.person_female_suffixes = params.get('person_female_suffixes', [])
        self.person_neutral_suffixes = params.get('person_neutral_suffixes', [])
        self.place_suffixes = params.get('place_suffixes', [])
        self.thing_suffixes = params.get('thing_suffixes', [])
        self.person_suffix_prob = params.get('person_suffix_prob', 0.7)
        self.place_suffix_prob = params.get('place_suffix_prob', 0.6)
        self.thing_suffix_prob = params.get('thing_suffix_prob', 0.3)
        self.max_attempts = params.get('max_attempts', 100)

    def _is_candidate_acceptable(self, candidate):
        if not candidate:
            return False
        if self.evaluator is None:
            return True
        return self.evaluator.is_acceptable(candidate, min_score=self.min_pronounceability_score)

    def _generate_base_candidate(self, min_syl, max_syl):
        num_syllables = random.randint(min_syl, max_syl)
        if num_syllables <= 0:
            return None

        base = self.phonology.generate_word(
            min_syllables=num_syllables,
            max_syllables=num_syllables,
            max_tries=20,
        )
        if (
            base
            and self.phonology.is_valid_sequence(base)
            and self._is_candidate_acceptable(base)
        ):
            return base
        return None

    def _add_suffix(self, base_name, suffix_list, probability):
        if base_name and suffix_list and random.random() < probability:
            suffix = random.choice(suffix_list)
            candidate = self.phonology.join_segments(base_name, suffix)
            return candidate if candidate else base_name
        return base_name

    def generate_person_name(self, gender=None):
        for _ in range(self.max_attempts):
            base = self._generate_base_candidate(self.person_min_syl, self.person_max_syl)
            if not base: continue
            final_name = base
            if gender == 'male':
                final_name = self._add_suffix(base, self.person_male_suffixes, self.person_suffix_prob)
            elif gender == 'female':
                final_name = self._add_suffix(base, self.person_female_suffixes, self.person_suffix_prob)
            elif gender == 'neutral':
                final_name = self._add_suffix(base, self.person_neutral_suffixes, self.person_suffix_prob)
            elif self.person_neutral_suffixes and random.random() < self.person_suffix_prob / 2:
                final_name = self._add_suffix(base, self.person_neutral_suffixes, 1.0)
            if (
                final_name
                and self._is_candidate_acceptable(final_name)
                and not self.lexicon.get_entry(final_name)
            ):
                return final_name

        return None

    def generate_place_name(self):
        return self._generate_name_tp(self.place_min_syl, self.place_max_syl,
                                      self.place_suffixes, self.place_suffix_prob)

    def generate_thing_name(self):
        return self._generate_name_tp(self.thing_min_syl, self.thing_max_syl,
                                      self.thing_suffixes, self.thing_suffix_prob)

    def _generate_name_tp(self, min_syl, max_syl, suffixes, suffix_prob):
        for _ in range(self.max_attempts):
            base = self._generate_base_candidate(min_syl, max_syl)
            if not base: continue
            final_name = self._add_suffix(base, suffixes, suffix_prob)
            if (
                final_name
                and self._is_candidate_acceptable(final_name)
                and not self.lexicon.get_entry(final_name)
            ):
                return final_name
        return None
