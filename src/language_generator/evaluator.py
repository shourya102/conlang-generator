import re


class PronounceabilityEvaluator:
    def __init__(self, phonology=None, min_score=58):
        self.phonology = phonology
        self.min_score = int(min_score)

    def _tokenize(self, word):
        if not word:
            return []
        if self.phonology is not None and hasattr(self.phonology, '_tokenize'):
            try:
                return self.phonology._tokenize(word)
            except Exception:
                pass
        return list(word)

    def _is_vowel(self, token):
        if self.phonology is not None and hasattr(self.phonology, 'vowel_set'):
            return token in self.phonology.vowel_set
        return token.lower() in {'a', 'e', 'i', 'o', 'u', 'y'}

    def _is_consonant(self, token):
        if self.phonology is not None and hasattr(self.phonology, 'consonant_set'):
            return token in self.phonology.consonant_set
        return token.isalpha() and not self._is_vowel(token)

    def score_word(self, word):
        if not word:
            return {'word': word, 'score': 0, 'accepted': False, 'issues': ['empty']}

        score = 100
        issues = []

        if self.phonology is not None and hasattr(self.phonology, 'is_valid_sequence'):
            if not self.phonology.is_valid_sequence(word):
                score -= 35
                issues.append('illegal_sequence')

        if re.search(r'(.)\1\1', word):
            score -= 20
            issues.append('triple_repeat')

        tokens = self._tokenize(word)
        if not tokens:
            return {'word': word, 'score': 0, 'accepted': False, 'issues': ['tokenization_failed']}

        vowel_count = sum(1 for token in tokens if self._is_vowel(token))
        consonant_count = sum(1 for token in tokens if self._is_consonant(token))
        total_count = max(1, vowel_count + consonant_count)
        vowel_ratio = vowel_count / total_count

        if vowel_ratio < 0.22:
            score -= int((0.22 - vowel_ratio) * 120)
            issues.append('too_few_vowels')
        if vowel_ratio > 0.78:
            score -= int((vowel_ratio - 0.78) * 120)
            issues.append('too_many_vowels')

        max_cluster = 0
        current_cluster = 0
        for token in tokens:
            if self._is_consonant(token):
                current_cluster += 1
                max_cluster = max(max_cluster, current_cluster)
            else:
                current_cluster = 0

        preferred_cluster = 3
        if self.phonology is not None and hasattr(self.phonology, 'max_consonant_cluster'):
            preferred_cluster = max(2, int(self.phonology.max_consonant_cluster) + 1)

        if max_cluster > preferred_cluster:
            score -= (max_cluster - preferred_cluster) * 12
            issues.append('heavy_consonant_cluster')

        if len(tokens) < 2:
            score -= 5
            issues.append('very_short')
        elif len(tokens) > 9:
            score -= (len(tokens) - 9) * 2
            issues.append('very_long')

        score = max(0, min(100, score))
        accepted = score >= self.min_score
        return {
            'word': word,
            'score': score,
            'accepted': accepted,
            'issues': issues,
            'vowel_ratio': round(vowel_ratio, 3),
            'max_cluster': max_cluster,
        }

    def is_acceptable(self, word, min_score=None):
        threshold = int(self.min_score if min_score is None else min_score)
        scored = self.score_word(word)
        return scored['score'] >= threshold

    def filter_acceptable(self, words, min_score=None):
        threshold = int(self.min_score if min_score is None else min_score)
        accepted = []
        rejected = []
        for word in words:
            result = self.score_word(word)
            if result['score'] >= threshold:
                accepted.append(result)
            else:
                rejected.append(result)
        return accepted, rejected
