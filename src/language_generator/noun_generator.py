class NounGenerator:
    def __init__(self, word_generator, name_generator, lexicon, grammar_engine=None, evaluator=None):
        if word_generator is None:
            raise ValueError('NounGenerator requires a WordGenerator instance.')
        if name_generator is None:
            raise ValueError('NounGenerator requires a NameGenerator instance.')
        if lexicon is None:
            raise ValueError('NounGenerator requires a Lexicon instance.')

        self.word_generator = word_generator
        self.name_generator = name_generator
        self.lexicon = lexicon
        self.grammar_engine = grammar_engine
        self.evaluator = evaluator

    def _apply_noun_inflection(self, noun, number='singular', grammatical_case='core'):
        if not noun:
            return noun
        if self.grammar_engine is None:
            return noun
        return self.grammar_engine.inflect_noun(noun, number=number, grammatical_case=grammatical_case)

    def generate_common_noun(self, english_meaning=None, number='singular', grammatical_case='core'):
        if english_meaning:
            entry = self.word_generator.generate_word_for_meaning(english_meaning.lower(), part_of_speech='Noun')
            if not entry:
                return None
            base = entry.get('word')
        else:
            generated = self.word_generator.generate_name_candidate()
            if not generated:
                return None
            base = generated

        inflected = self._apply_noun_inflection(base, number=number, grammatical_case=grammatical_case)
        if self.evaluator is not None and inflected and not self.evaluator.is_acceptable(inflected):
            return base
        return inflected

    def generate_proper_noun(self, english_prompt, category='person', gender=None):
        category_value = (category or 'person').lower().strip()
        if category_value == 'person':
            generated = self.name_generator.generate_person_name(gender=gender)
        elif category_value == 'place':
            generated = self.name_generator.generate_place_name()
        elif category_value == 'thing':
            generated = self.name_generator.generate_thing_name()
        else:
            generated = self.name_generator.generate_person_name(gender=gender)

        if not generated:
            return None

        entry_data = {
            'word': generated,
            'prefix': '',
            'root': generated,
            'suffix': '',
            'english_meaning': english_prompt,
            'part_of_speech': 'ProperNoun',
        }
        self.lexicon.add_entry(entry_data)
        return generated

    def generate_noun(self, english_meaning=None, noun_type='common', category='person', gender=None,
                      number='singular', grammatical_case='core'):
        noun_type_value = (noun_type or 'common').lower().strip()
        if noun_type_value == 'proper':
            meaning = english_meaning or 'generated-proper-noun'
            return self.generate_proper_noun(meaning, category=category, gender=gender)
        return self.generate_common_noun(
            english_meaning=english_meaning,
            number=number,
            grammatical_case=grammatical_case,
        )
