import random

consonants = ['a', 'c', 'f', 'fh', 'gch', 'll']
vowels = ['a', 'e', 'ai', 'ua']

syllable_structures = ['CVC', 'CV', 'VC', 'V']


def generate_syllable():
    structure = random.choice(syllable_structures)
    syllable = ""
    for char in structure:
        if char == 'C':
            syllable += random.choice(consonants)
        elif char == 'V':
            syllable += random.choice(vowels)
    return syllable


def generate_word(min_syllables, max_syllables):
    num_syllables = random.randint(min_syllables, max_syllables)
    word = ""
    for _ in range(num_syllables):
        word += generate_syllable()
    return word


def generate_lexicon(lexicon_size):
    lexicon = set()
    while len(lexicon) < lexicon_size:
        new_word = generate_word(1, 4)
        lexicon.add(new_word)
    return sorted(list(lexicon))


def generate_sentence(num_words):
    lexicon = generate_lexicon(100)
    sentence = ""
    for _ in range(num_words):
        word = random.choice(lexicon)
        sentence += word + " "
    return sentence


for _ in range(5):
    print(generate_sentence(10))
