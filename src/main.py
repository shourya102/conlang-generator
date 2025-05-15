from src.language_generator.language import Language
from src.language_generator.lexicon import Lexicon
from src.language_generator.morphology import Morphology
from src.language_generator.name_generator import NameGenerator
from src.language_generator.phonology import Phonology
from src.language_generator.word_generator import WordGenerator

if __name__ == '__main__':
    print("Language Generator")

    PHONOLOGY_PARAMS = {
        'consonants': ['l', 'r', 's', 'h', 'm', 'n', 'th', 'ph', 'v', 'f', 'z'],
        'vowels': ['a', 'e', 'i', 'o', 'u', 'ae', 'ia', 'eo', 'ui'],
        'syllable_structures': ['V', 'CV', 'VC', 'CVC'],
        'onsets': ['l', 'r', 's', 'h', 'm', 'n', 'th', 'ph', 'v', 'f', ''],
        'codas': ['l', 'r', 's', 'h', 'n', 'th', 'ph', ''],
        'illegal_sequences': ['aa', 'ee', 'ii', 'oo', 'uu', 'vv', 'ff', 'ss', 'll', 'rr']
    }

    MORPHOLOGY_PARAMS = {
        'num_roots': 300,
        'num_prefixes': 60,
        'num_suffixes': 80,
        'root_min_syl': 1,
        'root_max_syl': 3,
        'affix_max_syl': 2
    }

    WORDGEN_PARAMS = {
        'prefix_prob': 0.40,
        'suffix_prob': 0.60,
        'max_gen_attempts': 100
    }

    NAMEGEN_PARAMS = {
        'person_min_syl': 2,
        'person_max_syl': 5,
        'place_min_syl': 2,
        'place_max_syl': 4,
        'thing_min_syl': 1,
        'thing_max_syl': 3,
        'person_male_suffixes': ['iel', 'or', 'an', 'ith', 'ar'],
        'person_female_suffixes': ['iel', 'ara', 'ia', 'el', 'una'],
        'person_neutral_suffixes': ['en', 'eth', 'is', 'or'],
        'place_suffixes': ['ar', 'ion', 'os', 'eth', 'ira'],
        'thing_suffixes': ['essence', 'flare', 'song', 'light', 'shade'],
        'person_suffix_prob': 0.90,
        'place_suffix_prob': 0.80,
        'thing_suffix_prob': 0.60,
        'max_attempts': 100
    }

    # phonology = Phonology(config=PHONOLOGY_PARAMS)
    # morphology = Morphology(config=None, phonology=phonology, **MORPHOLOGY_PARAMS)
    # lexicon = Lexicon()
    # wordgen = WordGenerator(phonology=phonology, morphology=morphology, lexicon=lexicon, **WORDGEN_PARAMS)
    # namegen = NameGenerator(phonology=phonology, lexicon=lexicon, name_params=NAMEGEN_PARAMS)
    # language = Language(phonology=phonology, morphology=morphology, lexicon=lexicon, word_generator=wordgen, name_generator=namegen)
    language = Language.load('./language1.json')
    text = language.translate("Hello, how are we doing today? I am happy to see you.")
    language.save('./language1.json')
    print(text)