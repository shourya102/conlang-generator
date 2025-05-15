import random


class Phonology:
    def __init__(self, config=None, **kwargs):
        if config:
            params = config
        elif kwargs:
            params = kwargs
        else:
            raise ValueError("Phonology requires either a 'config' dictionary or keyword arguments.")
        self.consonants = list(set(params.get('consonants', [])))
        self.vowels = list(set(params.get('vowels', [])))
        if not self.consonants or not self.vowels:
            raise ValueError("Phonology requires non-empty 'consonants' and 'vowels' lists.")
        self.syllable_structures = params.get('syllable_structures', ['CV', 'CVC', 'V', 'VC'])
        default_onsets = self.consonants + ['']
        self.onsets = list(set(params.get('onsets', default_onsets)))
        default_codas = self.consonants + ['']
        self.codas = list(set(params.get('codas', default_codas)))
        self.illegal_sequences = params.get('illegal_sequences', [])
        self._validate_rules()
        print("Phonology Initialized:")
        print(f"  Consonants: {len(self.consonants)}, Vowels: {len(self.vowels)}")
        print(f"  Syllable Structures: {', '.join(self.syllable_structures)}")
        print(f"  Onsets: {len(self.onsets)}, Codas: {len(self.codas)}")
        print(f"  Illegal Sequences: {len(self.illegal_sequences)}")

    def _validate_rules(self):
        all_phonemes = set(self.consonants) | set(self.vowels)
        for item_list, name in [(self.onsets, "Onset"), (self.codas, "Coda"),
                                (self.illegal_sequences, "Illegal sequence")]:
            for item in item_list:
                if item and isinstance(item, str) and not all(p in all_phonemes for p in item):
                    pass
                    # print(f"Warning: {name} '{item}' contains characters not defined as phonemes.")

    def get_random_consonant(self):
        return random.choice(self.consonants) if self.consonants else ''

    def get_random_vowel(self):
        return random.choice(self.vowels) if self.vowels else ''

    def get_random_onset(self):
        return random.choice(self.onsets) if self.onsets else ''

    def get_random_coda(self):
        return random.choice(self.codas) if self.codas else ''

    def is_valid_sequence(self, sequence):
        if not self.illegal_sequences:
            return True
        for illegal in self.illegal_sequences:
            if illegal in sequence:
                return False
        return True

    def generate_syllable(self, max_tries=50):
        for _ in range(max_tries):
            structure = random.choice(self.syllable_structures)
            syllable = ""
            onset, nucleus, coda = '', '', ''
            if structure == 'V':
                nucleus = self.get_random_vowel()
            elif structure == 'CV':
                onset = self.get_random_onset()
                while not onset: onset = self.get_random_onset()
                nucleus = self.get_random_vowel()
            elif structure == 'VC':
                nucleus = self.get_random_vowel()
                coda = self.get_random_coda()
                while not coda: coda = self.get_random_coda()
            elif structure == 'CVC':
                onset = self.get_random_onset()
                while not onset: onset = self.get_random_onset()
                nucleus = self.get_random_vowel()
                coda = self.get_random_coda()
                while not coda: coda = self.get_random_coda()
            else:
                print(f"Warning: Unsupported syllable structure '{structure}' encountered.")
                continue
            if not nucleus: continue
            syllable = onset + nucleus + coda
            if self.is_valid_sequence(syllable):
                if syllable:
                    return syllable
        print("Warning: Failed to generate a valid syllable after multiple attempts.")
        return None

    def get_config(self):
        return {
            "consonants": self.consonants,
            "vowels": self.vowels,
            "syllable_structures": self.syllable_structures,
            "onsets": self.onsets,
            "codas": self.codas,
            "illegal_sequences": self.illegal_sequences,
        }
