import random

from src.language_generator.phonology import Phonology


class Morphology:
    def __init__(self, phonology, config=None, **kwargs):
        if not isinstance(phonology, Phonology):
            raise TypeError("The 'phonology' argument must be an instance of the Phonology class.")
        self.phonology = phonology
        if config and 'roots' in config and 'prefixes' in config and 'suffixes' in config:
            print("Morphology initializing using config...")
            self.roots = config.get('roots', [])
            self.prefixes = config.get('prefixes', [])
            self.suffixes = config.get('suffixes', [])
            if not self.roots: print("Warning: No roots loaded from config.")
        elif kwargs:
            print("Morphology initializing by generating new morphemes...")
            gen_params = {
                'num_roots': kwargs.get('num_roots', 100),
                'num_prefixes': kwargs.get('num_prefixes', 20),
                'num_suffixes': kwargs.get('num_suffixes', 20),
                'root_min_syl': kwargs.get('root_min_syl', 1),
                'root_max_syl': kwargs.get('root_max_syl', 2),
                'affix_max_syl': kwargs.get('affix_max_syl', 1),
            }
            self.roots = self._generate_morpheme_set(
                gen_params['num_roots'],
                gen_params['root_min_syl'],
                gen_params['root_max_syl'],
                "root"
            )
            self.prefixes = self._generate_morpheme_set(
                gen_params['num_prefixes'],
                1,
                gen_params['affix_max_syl'],
                "prefix"
            )
            self.suffixes = self._generate_morpheme_set(
                gen_params['num_suffixes'],
                1,
                gen_params['affix_max_syl'],
                "suffix"
            )
        else:
            raise ValueError("Morphology requires either a 'config' dictionary with morpheme lists "
                             "or keyword arguments for generation (e.g., num_roots).")
        print(f"  Roots: {len(self.roots)}, Prefixes: {len(self.prefixes)}, Suffixes: {len(self.suffixes)}")

    def _generate_morpheme_set(self, count, min_syl, max_syl, morpheme_type, max_tries_mult=5):
        morphemes = set()
        max_attempts = count * max_tries_mult
        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            num_syllables = random.randint(min_syl, max_syl)
            if num_syllables <= 0: continue
            morpheme_syllables = []
            valid_morpheme = True
            for _ in range(num_syllables):
                syllable = self.phonology.generate_syllable()
                if not syllable:
                    valid_morpheme = False
                    break
                morpheme_syllables.append(syllable)
            if valid_morpheme:
                morpheme = "".join(morpheme_syllables)
                if morpheme and self.phonology.is_valid_sequence(morpheme):
                    morphemes.add(morpheme)
        if len(morphemes) < count:
            print(
                f"Warning: Only generated {len(morphemes)} unique {morpheme_type}s "
                f"out of desired {count} (attempts: {attempts}).")
        return list(morphemes)

    def get_random_root(self):
        return random.choice(self.roots) if self.roots else None

    def get_random_prefix(self):
        return random.choice(self.prefixes) if self.prefixes else None

    def get_random_suffix(self):
        return random.choice(self.suffixes) if self.suffixes else None

    def get_config(self):
        return {
            "roots": self.roots,
            "prefixes": self.prefixes,
            "suffixes": self.suffixes,
        }
