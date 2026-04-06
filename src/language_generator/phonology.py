import random


def _dedupe_preserve_order(items):
    seen = set()
    ordered = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


class Phonology:
    def __init__(self, config=None, **kwargs):
        if config:
            params = config
        elif kwargs:
            params = kwargs
        else:
            raise ValueError("Phonology requires either a 'config' dictionary or keyword arguments.")

        self.consonants = _dedupe_preserve_order(params.get('consonants', []))
        self.vowels = _dedupe_preserve_order(params.get('vowels', []))
        if not self.consonants or not self.vowels:
            raise ValueError("Phonology requires non-empty 'consonants' and 'vowels' lists.")

        self.consonant_set = set(self.consonants)
        self.vowel_set = set(self.vowels)
        self._sorted_inventory = sorted(self.consonants + self.vowels, key=len, reverse=True)

        self.syllable_structures = params.get('syllable_structures', ['CV', 'CVC', 'V', 'VC'])
        self.structure_weights = params.get('structure_weights', {})
        self.consonant_weights = params.get('consonant_weights', {})
        self.vowel_weights = params.get('vowel_weights', {})

        default_onsets = self.consonants + ['']
        default_codas = self.consonants + ['']
        self.onsets = _dedupe_preserve_order(params.get('onsets', default_onsets))
        self.codas = _dedupe_preserve_order(params.get('codas', default_codas))
        self.onset_weights = params.get('onset_weights', {})
        self.coda_weights = params.get('coda_weights', {})

        self.illegal_sequences = params.get('illegal_sequences', [])

        self.boundary_smoothing = bool(params.get('boundary_smoothing', True))
        self.max_consonant_cluster = int(params.get('max_consonant_cluster', 2))
        self.epenthetic_vowels = _dedupe_preserve_order(
            params.get('epenthetic_vowels', self.vowels[:2] if len(self.vowels) >= 2 else self.vowels)
        )
        default_hiatus_glides = [c for c in ['y', 'w', 'h', 'r', 'l'] if c in self.consonant_set]
        self.hiatus_glides = _dedupe_preserve_order(params.get('hiatus_glides', default_hiatus_glides))
        self.allowed_boundary_clusters = self._build_allowed_boundary_clusters(
            params.get('allowed_boundary_clusters', [])
        )

        self._validate_rules()

        print("Phonology Initialized:")
        print(f"  Consonants: {len(self.consonants)}, Vowels: {len(self.vowels)}")
        print(f"  Syllable Structures: {', '.join(self.syllable_structures)}")
        print(f"  Onsets: {len(self.onsets)}, Codas: {len(self.codas)}")
        print(f"  Illegal Sequences: {len(self.illegal_sequences)}")

    def _build_allowed_boundary_clusters(self, configured_clusters):
        clusters = set()
        for cluster in configured_clusters:
            tokens = self._tokenize(cluster)
            if len(tokens) == 2 and all(t in self.consonant_set for t in tokens):
                clusters.add((tokens[0], tokens[1]))

        for onset in self.onsets:
            tokens = self._tokenize(onset)
            if len(tokens) == 2 and all(t in self.consonant_set for t in tokens):
                clusters.add((tokens[0], tokens[1]))
        return clusters

    def _validate_rules(self):
        for item_list in [self.onsets, self.codas]:
            for item in item_list:
                if not isinstance(item, str):
                    raise TypeError("Onsets, codas, and phoneme lists must contain strings.")

    def _weighted_choice(self, items, weights=None):
        if not items:
            return ''
        if not weights:
            return random.choice(items)

        numeric_weights = []
        for item in items:
            weight = weights.get(item, 1.0)
            try:
                weight = float(weight)
            except (TypeError, ValueError):
                weight = 1.0
            if weight <= 0:
                weight = 0.01
            numeric_weights.append(weight)

        total_weight = sum(numeric_weights)
        if total_weight <= 0:
            return random.choice(items)
        return random.choices(items, weights=numeric_weights, k=1)[0]

    def _tokenize(self, sequence):
        if not sequence:
            return []
        tokens = []
        index = 0
        while index < len(sequence):
            matched = None
            for phoneme in self._sorted_inventory:
                if sequence.startswith(phoneme, index):
                    matched = phoneme
                    break
            if matched:
                tokens.append(matched)
                index += len(matched)
            else:
                tokens.append(sequence[index])
                index += 1
        return tokens

    def _is_vowel_token(self, token):
        return token in self.vowel_set

    def _is_consonant_token(self, token):
        return token in self.consonant_set

    def _count_edge_cluster(self, tokens, from_end=True):
        if not tokens:
            return 0
        cluster_size = 0
        iterable = reversed(tokens) if from_end else tokens
        for token in iterable:
            if self._is_consonant_token(token):
                cluster_size += 1
            else:
                break
        return cluster_size

    def _pick_epenthetic_vowel(self):
        if self.epenthetic_vowels:
            return self._weighted_choice(self.epenthetic_vowels, self.vowel_weights)
        return self.get_random_vowel()

    def _pick_hiatus_glide(self):
        valid_glides = [g for g in self.hiatus_glides if g in self.consonant_set]
        if not valid_glides:
            return ''
        return self._weighted_choice(valid_glides, self.consonant_weights)

    def get_random_consonant(self):
        return self._weighted_choice(self.consonants, self.consonant_weights)

    def get_random_vowel(self):
        return self._weighted_choice(self.vowels, self.vowel_weights)

    def get_random_onset(self):
        return self._weighted_choice(self.onsets, self.onset_weights)

    def get_random_coda(self):
        return self._weighted_choice(self.codas, self.coda_weights)

    def is_valid_sequence(self, sequence):
        if not self.illegal_sequences:
            return True
        for illegal in self.illegal_sequences:
            if illegal in sequence:
                return False
        return True

    def _generate_from_generic_structure(self, structure):
        pieces = []
        for marker in structure:
            if marker == 'C':
                pieces.append(self.get_random_consonant())
            elif marker == 'V':
                pieces.append(self.get_random_vowel())
            else:
                return None
        return "".join(pieces)

    def generate_syllable(self, max_tries=50):
        for _ in range(max_tries):
            structure = self._weighted_choice(self.syllable_structures, self.structure_weights)
            onset, nucleus, coda = '', '', ''

            if structure == 'V':
                nucleus = self.get_random_vowel()
            elif structure == 'CV':
                onset = self.get_random_onset()
                while not onset:
                    onset = self.get_random_onset()
                nucleus = self.get_random_vowel()
            elif structure == 'VC':
                nucleus = self.get_random_vowel()
                coda = self.get_random_coda()
                while not coda:
                    coda = self.get_random_coda()
            elif structure == 'CVC':
                onset = self.get_random_onset()
                while not onset:
                    onset = self.get_random_onset()
                nucleus = self.get_random_vowel()
                coda = self.get_random_coda()
                while not coda:
                    coda = self.get_random_coda()
            else:
                generic = self._generate_from_generic_structure(structure)
                if generic and self.is_valid_sequence(generic):
                    return generic
                continue

            if not nucleus:
                continue

            syllable = onset + nucleus + coda
            if syllable and self.is_valid_sequence(syllable):
                return syllable

        print("Warning: Failed to generate a valid syllable after multiple attempts.")
        return None

    def _join_pair(self, left, right):
        if not left:
            return right or ''
        if not right:
            return left
        if not self.boundary_smoothing:
            return left + right

        left_tokens = self._tokenize(left)
        right_tokens = self._tokenize(right)
        if not left_tokens or not right_tokens:
            return left + right

        if left_tokens[-1] == right_tokens[0]:
            right_tokens = right_tokens[1:]
            if not right_tokens:
                return "".join(left_tokens)

        if self._is_vowel_token(left_tokens[-1]) and self._is_vowel_token(right_tokens[0]):
            if left_tokens[-1] == right_tokens[0]:
                right_tokens = right_tokens[1:]
            else:
                glide = self._pick_hiatus_glide()
                if glide:
                    left_tokens.append(glide)
                elif random.random() < 0.35:
                    right_tokens = right_tokens[1:]

        if right_tokens and self._is_consonant_token(left_tokens[-1]) and self._is_consonant_token(right_tokens[0]):
            boundary_pair = (left_tokens[-1], right_tokens[0])
            if boundary_pair not in self.allowed_boundary_clusters:
                left_cluster = self._count_edge_cluster(left_tokens, from_end=True)
                right_cluster = self._count_edge_cluster(right_tokens, from_end=False)
                if left_cluster + right_cluster > self.max_consonant_cluster or random.random() < 0.55:
                    vowel = self._pick_epenthetic_vowel()
                    if vowel:
                        left_tokens.append(vowel)

        candidate = "".join(left_tokens + right_tokens)
        if self.is_valid_sequence(candidate):
            return candidate

        raw = left + right
        if self.is_valid_sequence(raw):
            return raw

        epenthetic = self._pick_epenthetic_vowel()
        if epenthetic:
            softened = left + epenthetic + right
            if self.is_valid_sequence(softened):
                return softened

        return candidate

    def join_segments(self, *segments):
        cleaned = [segment for segment in segments if segment]
        if not cleaned:
            return ''

        current = cleaned[0]
        for segment in cleaned[1:]:
            current = self._join_pair(current, segment)
        return current

    def generate_word(self, min_syllables=1, max_syllables=2, max_tries=50):
        if min_syllables > max_syllables:
            min_syllables, max_syllables = max_syllables, min_syllables
        min_syllables = max(1, min_syllables)
        max_syllables = max(1, max_syllables)

        for _ in range(max_tries):
            syllable_count = random.randint(min_syllables, max_syllables)
            syllables = []
            valid = True
            for _ in range(syllable_count):
                syllable = self.generate_syllable()
                if not syllable:
                    valid = False
                    break
                syllables.append(syllable)

            if not valid:
                continue

            candidate = self.join_segments(*syllables)
            if candidate and self.is_valid_sequence(candidate):
                return candidate

        return None

    def get_config(self):
        return {
            "consonants": self.consonants,
            "vowels": self.vowels,
            "syllable_structures": self.syllable_structures,
            "structure_weights": self.structure_weights,
            "consonant_weights": self.consonant_weights,
            "vowel_weights": self.vowel_weights,
            "onsets": self.onsets,
            "codas": self.codas,
            "onset_weights": self.onset_weights,
            "coda_weights": self.coda_weights,
            "illegal_sequences": self.illegal_sequences,
            "boundary_smoothing": self.boundary_smoothing,
            "max_consonant_cluster": self.max_consonant_cluster,
            "epenthetic_vowels": self.epenthetic_vowels,
            "hiatus_glides": self.hiatus_glides,
            "allowed_boundary_clusters": ["".join(pair) for pair in sorted(self.allowed_boundary_clusters)],
        }
