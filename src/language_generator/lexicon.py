import random


class Lexicon:
    def __init__(self, config=None):
        self.entries = {}
        self.english_to_conlang = {}
        if config and 'entries' in config:
            print('Lexicon initializing from config...')
            loaded_entries = config['entries']
            if isinstance(loaded_entries, dict):
                self.entries = loaded_entries
                self._rebuild_reverse_lookup()
                print(f"Loaded {len(self.entries)} entries from config.")
            else:
                print("Warning: Invalid entries format in config. Expected a dictionary.")
        else:
            print("Lexicon initialized empty")
        print("-" * 20)

    def _rebuild_reverse_lookup(self):
        self.english_to_conlang = {}
        for conlang_word, entry_data in self.entries.items():
            eng_meaning = entry_data.get('english_meaning')
            if eng_meaning:
                if eng_meaning in self.english_to_conlang and self.english_to_conlang[eng_meaning] != conlang_word:
                    print(f"Warning: Duplicate English meaning '{eng_meaning}' for words "
                          f"'{self.english_to_conlang[eng_meaning]}' and '{conlang_word}'.")
                elif eng_meaning not in self.english_to_conlang:
                    self.english_to_conlang[eng_meaning] = conlang_word

    def add_entry(self, entry_data):
        conlang_word = entry_data.get('word')
        eng_meaning = entry_data.get('english_meaning')
        if not conlang_word:
            print("Warning: Cannot add entry without 'word' key.")
            return False
        if conlang_word in self.entries:
            existing_meaning = self.entries[conlang_word].get('english_meaning')
            if existing_meaning == eng_meaning:
                print(f"Entry '{conlang_word}' already exists with the same meaning.")
                return True
            else:
                print(f"Error: Conlang word '{conlang_word}' already exists but with a different meaning "
                      f"('{existing_meaning}' vs '{eng_meaning}'). Cannot add.")
                return False
        if eng_meaning and eng_meaning in self.english_to_conlang:
            existing_conlang_word = self.english_to_conlang[eng_meaning]
            if existing_conlang_word != conlang_word:
                print(f"Error: English meaning '{eng_meaning}' is already translated as '{existing_conlang_word}'. "
                      f"Cannot add new translation '{conlang_word}'.")
                return False
        full_entry = {
            'word': conlang_word,
            'prefix': entry_data.get('prefix', ''),
            'root': entry_data.get('root', ''),
            'suffix': entry_data.get('suffix', ''),
            'english_meaning': eng_meaning,
            'part_of_speech': entry_data.get('part_of_speech', None)
        }
        self.entries[conlang_word] = full_entry
        if eng_meaning:
            self.english_to_conlang[eng_meaning] = conlang_word
        return True

    def find_by_english(self, english_word):
        return self.english_to_conlang.get(english_word, None)

    def get_entry(self, conlang_word):
        return self.entries.get(conlang_word, None)

    def get_size(self):
        return len(self.entries)

    def get_all_words(self):
        return list(self.entries.keys())

    def get_words_by_pos(self, pos_tag):
        return [word for word, data in self.entries.items() if data.get('part_of_speech') == pos_tag]

    def get_random_word(self, pos_tag=None):
        if pos_tag:
            candidates = self.get_words_by_pos(pos_tag)
        else:
            candidates = list(self.entries.keys())
        return random.choice(candidates) if candidates else None

    def assign_part_of_speech(self, conlang_word, pos_tag):
        entry = self.get_entry(conlang_word)
        if entry:
            entry['part_of_speech'] = pos_tag
            return True
        return False

    def get_config(self):
        return {
            "entries": self.entries
        }

    def __str__(self):
        num_to_show = 10
        items = list(self.entries.items())[:num_to_show]
        output = f"Lexicon ({self.get_size()} entries):\n"
        if not items: output += "  (empty)\n"
        for word, data in items:
            morph_str = f"{data.get('prefix', '')}-{data.get('root', '')}-{data.get('suffix', '')}".strip('-')
            meaning_str = data.get('english_meaning', 'N/A')
            pos_str = f" [{data.get('part_of_speech', 'UNK')}]" if data.get('part_of_speech') else ""
            output += f"  - {word:<15} ({morph_str}){pos_str}: {meaning_str}\n"
        if self.get_size() > num_to_show:
            output += f"  ... ({self.get_size() - num_to_show} more entries)\n"
        return output
