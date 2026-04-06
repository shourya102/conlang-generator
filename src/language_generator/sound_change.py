import copy
import random
import re


class SoundChangeRule:
    def __init__(
        self,
        pattern,
        replacement,
        left_context='',
        right_context='',
        probability=1.0,
        description='',
    ):
        if not pattern:
            raise ValueError('SoundChangeRule requires a non-empty pattern.')
        self.pattern = pattern
        self.replacement = replacement if replacement is not None else ''
        self.left_context = left_context
        self.right_context = right_context
        self.probability = max(0.0, min(1.0, float(probability)))
        self.description = description

    def as_dict(self):
        return {
            'pattern': self.pattern,
            'replacement': self.replacement,
            'left_context': self.left_context,
            'right_context': self.right_context,
            'probability': self.probability,
            'description': self.description,
        }

    def _build_regex(self):
        left = f"(?<={self.left_context})" if self.left_context else ''
        right = f"(?={self.right_context})" if self.right_context else ''
        return re.compile(f"{left}{self.pattern}{right}")

    def apply(self, word):
        if not word:
            return word
        if self.probability < 1.0 and random.random() > self.probability:
            return word
        regex = self._build_regex()
        return regex.sub(self.replacement, word)


class SoundChangeEngine:
    PRESET_RULES = {
        'lenition': [
            {'pattern': 'p', 'replacement': 'f', 'left_context': '[aeiou]', 'right_context': '[aeiou]', 'probability': 0.55},
            {'pattern': 't', 'replacement': 's', 'left_context': '[aeiou]', 'right_context': '[aeiou]', 'probability': 0.48},
            {'pattern': 'k', 'replacement': 'x', 'left_context': '[aeiou]', 'right_context': '[aeiou]', 'probability': 0.44},
        ],
        'archaizing': [
            {'pattern': 'v', 'replacement': 'w', 'probability': 0.72},
            {'pattern': 'f', 'replacement': 'ph', 'probability': 0.35},
            {'pattern': 's', 'replacement': 'th', 'right_context': '[aeiou]', 'probability': 0.30},
        ],
        'vowel_shift': [
            {'pattern': 'ae', 'replacement': 'e', 'probability': 0.85},
            {'pattern': 'ei', 'replacement': 'i', 'probability': 0.68},
            {'pattern': 'au', 'replacement': 'o', 'probability': 0.63},
        ],
    }

    def __init__(self, rules=None):
        self.rules = self._normalize_rules(rules or [])

    @classmethod
    def available_presets(cls):
        return sorted(cls.PRESET_RULES.keys())

    @classmethod
    def preset_rules(cls, preset_name):
        preset = (preset_name or '').lower().strip()
        return copy.deepcopy(cls.PRESET_RULES.get(preset, []))

    def _normalize_rules(self, rules):
        normalized = []
        for rule in rules:
            if isinstance(rule, SoundChangeRule):
                normalized.append(rule)
                continue
            if not isinstance(rule, dict):
                continue
            pattern = rule.get('pattern')
            if not pattern:
                continue
            normalized.append(
                SoundChangeRule(
                    pattern=pattern,
                    replacement=rule.get('replacement', ''),
                    left_context=rule.get('left_context', ''),
                    right_context=rule.get('right_context', ''),
                    probability=rule.get('probability', 1.0),
                    description=rule.get('description', ''),
                )
            )
        return normalized

    def get_config(self):
        return [rule.as_dict() for rule in self.rules]

    def apply_to_word(self, word):
        current = word
        for rule in self.rules:
            current = rule.apply(current)
        return current

    def apply_to_words(self, words):
        return [self.apply_to_word(word) for word in words]

    def apply_to_language_config(self, language_config):
        cfg = copy.deepcopy(language_config)

        morphology_cfg = cfg.get('morphology', {})
        for key in ['roots', 'prefixes', 'suffixes']:
            if key in morphology_cfg and isinstance(morphology_cfg[key], list):
                morphology_cfg[key] = [self.apply_to_word(item) for item in morphology_cfg[key]]

        lexicon_cfg = cfg.get('lexicon', {})
        entries = lexicon_cfg.get('entries', {}) if isinstance(lexicon_cfg, dict) else {}
        if entries:
            remapped = {}
            for old_word, entry in entries.items():
                new_word = self.apply_to_word(old_word)
                candidate = new_word
                dedupe_counter = 1
                while candidate in remapped:
                    dedupe_counter += 1
                    candidate = f"{new_word}{dedupe_counter}"

                new_entry = copy.deepcopy(entry)
                new_entry['word'] = candidate
                if new_entry.get('root'):
                    new_entry['root'] = self.apply_to_word(new_entry['root'])
                if new_entry.get('prefix'):
                    new_entry['prefix'] = self.apply_to_word(new_entry['prefix'])
                if new_entry.get('suffix'):
                    new_entry['suffix'] = self.apply_to_word(new_entry['suffix'])
                remapped[candidate] = new_entry
            lexicon_cfg['entries'] = remapped

        return cfg
