class GrammarEngine:
    VALID_WORD_ORDERS = {'SVO', 'SOV', 'VSO', 'VOS', 'OSV', 'OVS'}
    VALID_ADJECTIVE_POSITIONS = {'before', 'after'}
    VALID_ADPOSITION_ORDERS = {'preposition', 'postposition'}
    VALID_ADVERB_POSITIONS = {'before', 'after'}
    VALID_CASE_MARKING_STYLES = {'suffix', 'particle'}
    VALID_AFFIX_STYLES = {'prefix', 'suffix'}
    VALID_NEGATION_POSITIONS = {'before_verb', 'after_verb', 'clause_final'}
    VALID_QUESTION_POSITIONS = {'clause_initial', 'clause_final'}

    NOMINAL_TAGS = {'Noun', 'ProperNoun', 'Pronoun'}
    VERB_TAG = 'Verb'

    AUXILIARY_WORDS = {
        'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'do', 'does', 'did', 'have', 'has', 'had',
        'will', 'shall', 'would', 'should', 'can', 'could', 'may', 'might', 'must',
    }
    ARTICLE_WORDS = {'a', 'an', 'the'}
    NEGATION_WORDS = {
        'not', "n't", 'never', 'no', 'none', 'nobody', 'nothing',
        'cannot', "can't", "dont", "don't", "doesn't", "didn't", "won't", "wouldn't",
        "shouldn't", "isn't", "aren't", "wasn't", "weren't",
    }
    FUTURE_MARKERS = {'will', 'shall', 'going', 'gonna'}
    PERFECT_AUXILIARIES = {'have', 'has', 'had'}

    SUBJECT_PRONOUN_FEATURES = {
        'i': ('1', 'singular'),
        'you': ('2', 'singular'),
        'he': ('3', 'singular'),
        'she': ('3', 'singular'),
        'it': ('3', 'singular'),
        'we': ('1', 'plural'),
        'they': ('3', 'plural'),
    }
    SUBJECT_PRONOUNS = set(SUBJECT_PRONOUN_FEATURES.keys())
    OBJECT_PRONOUNS = {'me', 'him', 'her', 'us', 'them', 'whom'}
    POSSESSIVE_WORDS = {'my', 'your', 'his', 'her', 'its', 'our', 'their', 'whose'}
    PLURAL_PRONOUNS = {'we', 'us', 'they', 'them'}

    DEFAULT_AGREEMENT_MARKERS = {
        '1sg': 'm',
        '2sg': 't',
        '3sg': '',
        '1pl': 'me',
        '2pl': 'te',
        '3pl': 'n',
    }

    def __init__(self, phonology=None, config=None):
        params = config or {}
        self.phonology = phonology

        self.word_order = str(params.get('word_order', 'SVO')).upper()
        if self.word_order not in self.VALID_WORD_ORDERS:
            self.word_order = 'SVO'

        self.adjective_position = str(params.get('adjective_position', 'after')).lower()
        if self.adjective_position not in self.VALID_ADJECTIVE_POSITIONS:
            self.adjective_position = 'after'

        self.adposition_order = str(params.get('adposition_order', 'preposition')).lower()
        if self.adposition_order not in self.VALID_ADPOSITION_ORDERS:
            self.adposition_order = 'preposition'

        self.adverb_position = str(params.get('adverb_position', 'before')).lower()
        if self.adverb_position not in self.VALID_ADVERB_POSITIONS:
            self.adverb_position = 'before'

        self.drop_articles = bool(params.get('drop_articles', True))
        self.drop_redundant_auxiliaries = bool(params.get('drop_redundant_auxiliaries', True))

        self.plural_suffix = params.get('plural_suffix', 'i')
        self.accusative_suffix = params.get('accusative_suffix', 'm')
        self.genitive_suffix = params.get('genitive_suffix', 'n')
        self.past_prefix = params.get('past_prefix', 'ta')
        self.future_prefix = params.get('future_prefix', 'sa')
        self.progressive_suffix = params.get('progressive_suffix', 'ri')
        self.perfect_suffix = params.get('perfect_suffix', 'na')

        self.enable_case_marking = bool(params.get('enable_case_marking', True))
        self.case_marking_style = str(params.get('case_marking_style', 'suffix')).lower()
        if self.case_marking_style not in self.VALID_CASE_MARKING_STYLES:
            self.case_marking_style = 'suffix'

        self.case_mark_pronouns = bool(params.get('case_mark_pronouns', False))
        self.nominative_particle = params.get('nominative_particle', '')
        self.accusative_particle = params.get('accusative_particle', 'ko')
        self.genitive_particle = params.get('genitive_particle', 'no')

        self.enable_subject_agreement = bool(params.get('enable_subject_agreement', True))
        self.agreement_style = str(params.get('agreement_style', 'suffix')).lower()
        if self.agreement_style not in self.VALID_AFFIX_STYLES:
            self.agreement_style = 'suffix'
        self.agreement_markers = self._normalize_agreement_markers(params.get('agreement_markers'))

        self.negation_particle = params.get('negation_particle', 'na')
        self.negation_position = str(params.get('negation_position', 'before_verb')).lower()
        if self.negation_position not in self.VALID_NEGATION_POSITIONS:
            self.negation_position = 'before_verb'
        self.replace_lexical_negation = bool(params.get('replace_lexical_negation', True))

        self.question_particle = params.get('question_particle', 'ka')
        self.question_particle_position = str(params.get('question_particle_position', 'clause_final')).lower()
        if self.question_particle_position not in self.VALID_QUESTION_POSITIONS:
            self.question_particle_position = 'clause_final'

    def _normalize_agreement_key(self, key):
        cleaned = str(key or '').strip().lower().replace('-', '').replace('_', '')
        mapping = {
            '1sg': '1sg', '1s': '1sg', '1singular': '1sg', 'firstsingular': '1sg',
            '2sg': '2sg', '2s': '2sg', '2singular': '2sg', 'secondsingular': '2sg',
            '3sg': '3sg', '3s': '3sg', '3singular': '3sg', 'thirdsingular': '3sg',
            '1pl': '1pl', '1p': '1pl', '1plural': '1pl', 'firstplural': '1pl',
            '2pl': '2pl', '2p': '2pl', '2plural': '2pl', 'secondplural': '2pl',
            '3pl': '3pl', '3p': '3pl', '3plural': '3pl', 'thirdplural': '3pl',
        }
        return mapping.get(cleaned, '')

    def _normalize_agreement_markers(self, markers):
        normalized = dict(self.DEFAULT_AGREEMENT_MARKERS)
        if not isinstance(markers, dict):
            return normalized

        for key, value in markers.items():
            norm_key = self._normalize_agreement_key(key)
            if not norm_key:
                continue
            normalized[norm_key] = str(value or '')
        return normalized

    def _join(self, left, right):
        if not right:
            return left
        if not left:
            return right
        if self.phonology is not None and hasattr(self.phonology, 'join_segments'):
            return self.phonology.join_segments(left, right)
        return left + right

    def get_config(self):
        return {
            'word_order': self.word_order,
            'adjective_position': self.adjective_position,
            'adposition_order': self.adposition_order,
            'adverb_position': self.adverb_position,
            'drop_articles': self.drop_articles,
            'drop_redundant_auxiliaries': self.drop_redundant_auxiliaries,
            'plural_suffix': self.plural_suffix,
            'accusative_suffix': self.accusative_suffix,
            'genitive_suffix': self.genitive_suffix,
            'past_prefix': self.past_prefix,
            'future_prefix': self.future_prefix,
            'progressive_suffix': self.progressive_suffix,
            'perfect_suffix': self.perfect_suffix,
            'enable_case_marking': self.enable_case_marking,
            'case_marking_style': self.case_marking_style,
            'case_mark_pronouns': self.case_mark_pronouns,
            'nominative_particle': self.nominative_particle,
            'accusative_particle': self.accusative_particle,
            'genitive_particle': self.genitive_particle,
            'enable_subject_agreement': self.enable_subject_agreement,
            'agreement_style': self.agreement_style,
            'agreement_markers': dict(self.agreement_markers),
            'negation_particle': self.negation_particle,
            'negation_position': self.negation_position,
            'replace_lexical_negation': self.replace_lexical_negation,
            'question_particle': self.question_particle,
            'question_particle_position': self.question_particle_position,
        }

    def get_affix_inventory(self):
        prefixes = []
        suffixes = []

        if self.past_prefix:
            prefixes.append(str(self.past_prefix))
        if self.future_prefix:
            prefixes.append(str(self.future_prefix))

        if self.plural_suffix:
            suffixes.append(str(self.plural_suffix))
        if self.accusative_suffix:
            suffixes.append(str(self.accusative_suffix))
        if self.genitive_suffix:
            suffixes.append(str(self.genitive_suffix))
        if self.progressive_suffix:
            suffixes.append(str(self.progressive_suffix))
        if self.perfect_suffix:
            suffixes.append(str(self.perfect_suffix))

        for marker in self.agreement_markers.values():
            marker_value = str(marker or '')
            if not marker_value:
                continue
            if self.agreement_style == 'prefix':
                prefixes.append(marker_value)
            else:
                suffixes.append(marker_value)

        unique_prefixes = [value for value in dict.fromkeys(prefixes) if value]
        unique_suffixes = [value for value in dict.fromkeys(suffixes) if value]
        return {'prefixes': unique_prefixes, 'suffixes': unique_suffixes}

    def inflect_noun(self, noun, number='singular', grammatical_case='core'):
        if not noun:
            return noun

        form = noun
        if str(number).lower() in {'plural', 'pl'} and self.plural_suffix:
            form = self._join(form, self.plural_suffix)

        if self.enable_case_marking and self.case_marking_style == 'suffix':
            case_value = str(grammatical_case or 'core').lower()
            if case_value in {'acc', 'accusative', 'object'} and self.accusative_suffix:
                form = self._join(form, self.accusative_suffix)
            elif case_value in {'gen', 'genitive', 'possessive'} and self.genitive_suffix:
                form = self._join(form, self.genitive_suffix)

        return form

    def _agreement_marker(self, person='3', number='singular'):
        person_value = str(person or '3').strip()
        number_value = str(number or 'singular').strip().lower()
        suffix = 'pl' if number_value in {'plural', 'pl'} else 'sg'
        return str(self.agreement_markers.get(f'{person_value}{suffix}', '') or '')

    def inflect_verb(self, verb, tense='present', aspect='simple', person='3', number='singular', mood='indicative'):
        if not verb:
            return verb

        form = verb

        tense_value = str(tense or 'present').lower()
        if tense_value in {'past', 'preterite'} and self.past_prefix:
            form = self._join(self.past_prefix, form)
        elif tense_value in {'future', 'prospective'} and self.future_prefix:
            form = self._join(self.future_prefix, form)

        aspect_value = str(aspect or 'simple').lower()
        if aspect_value in {'progressive', 'continuous', 'perfect_progressive'} and self.progressive_suffix:
            form = self._join(form, self.progressive_suffix)
        if aspect_value in {'perfect', 'perfective', 'perfect_progressive'} and self.perfect_suffix:
            form = self._join(form, self.perfect_suffix)

        if self.enable_subject_agreement:
            marker = self._agreement_marker(person=person, number=number)
            if marker:
                if self.agreement_style == 'prefix':
                    form = self._join(marker, form)
                else:
                    form = self._join(form, marker)

        _ = mood
        return form

    def _normalized_source(self, item):
        source = item.get('source_normalized')
        if source:
            return str(source).strip().lower()
        source = item.get('source_token') or item.get('token') or ''
        return str(source).strip().lower()

    def _normalized_tag(self, item):
        return str(item.get('tag') or '').upper()

    def _is_nominal(self, item):
        return item.get('simple_pos') in self.NOMINAL_TAGS

    def _is_auxiliary(self, item):
        return item.get('simple_pos') == self.VERB_TAG and self._normalized_source(item) in self.AUXILIARY_WORDS

    def _find_first_main_verb_index(self, items):
        for idx, item in enumerate(items):
            if item.get('simple_pos') == self.VERB_TAG and not self._is_auxiliary(item):
                return idx
        for idx, item in enumerate(items):
            if item.get('simple_pos') == self.VERB_TAG:
                return idx
        return None

    def _infer_number(self, item):
        source = self._normalized_source(item)
        tag = self._normalized_tag(item)

        if source in self.PLURAL_PRONOUNS:
            return 'plural'
        if source in self.SUBJECT_PRONOUNS or source in self.OBJECT_PRONOUNS:
            return 'singular'
        if tag in {'NNS', 'NNPS'}:
            return 'plural'
        if source.endswith('s') and len(source) > 3 and not source.endswith(('ss', 'us', 'is')):
            return 'plural'
        return 'singular'

    def _infer_roles(self, items):
        roles = {
            'subject': set(),
            'object': set(),
            'genitive': set(),
        }

        first_verb_index = self._find_first_main_verb_index(items)

        for idx, item in enumerate(items):
            if not self._is_nominal(item):
                continue

            item_id = id(item)
            source = self._normalized_source(item)

            if source in self.POSSESSIVE_WORDS or source.endswith("'s"):
                roles['genitive'].add(item_id)

            if source in self.OBJECT_PRONOUNS:
                roles['object'].add(item_id)
                continue
            if source in self.SUBJECT_PRONOUNS:
                roles['subject'].add(item_id)
                continue

            if first_verb_index is None:
                roles['subject'].add(item_id)
            elif idx < first_verb_index:
                roles['subject'].add(item_id)
            elif idx > first_verb_index:
                roles['object'].add(item_id)

        return roles

    def _infer_subject_features(self, items, roles):
        for item in items:
            if id(item) not in roles['subject']:
                continue

            source = self._normalized_source(item)
            if source in self.SUBJECT_PRONOUN_FEATURES:
                return self.SUBJECT_PRONOUN_FEATURES[source]
            if source in self.OBJECT_PRONOUNS:
                if source in {'us', 'them'}:
                    return '3', 'plural'
                return '3', 'singular'

            number = self._infer_number(item)
            return '3', number

        return '3', 'singular'

    def _detect_clause_features(self, items, clause_ending=None):
        sources = [self._normalized_source(item) for item in items]
        tags = [self._normalized_tag(item) for item in items]

        has_future = any(source in self.FUTURE_MARKERS for source in sources)
        has_past = any(tag in {'VBD', 'VBN'} for tag in tags)
        has_progressive = any(tag == 'VBG' or source.endswith('ing') for source, tag in zip(sources, tags))
        has_perfect = any(source in self.PERFECT_AUXILIARIES for source in sources)

        if has_future:
            tense = 'future'
        elif has_past:
            tense = 'past'
        else:
            tense = 'present'

        if has_progressive and has_perfect:
            aspect = 'perfect_progressive'
        elif has_progressive:
            aspect = 'progressive'
        elif has_perfect:
            aspect = 'perfect'
        else:
            aspect = 'simple'

        roles = self._infer_roles(items)
        person, number = self._infer_subject_features(items, roles)

        first_content = None
        for item in items:
            source = self._normalized_source(item)
            if source:
                first_content = item
                break

        is_imperative = bool(
            first_content
            and first_content.get('simple_pos') == self.VERB_TAG
            and not roles['subject']
        )

        is_negative = any(source in self.NEGATION_WORDS or source.endswith("n't") for source in sources)
        is_question = str(clause_ending or '') == '?'

        return {
            'tense': tense,
            'aspect': aspect,
            'mood': 'imperative' if is_imperative else 'indicative',
            'person': person,
            'number': number,
            'is_negative': is_negative,
            'is_question': is_question,
        }

    def _strip_function_words(self, items, features):
        if not items:
            return []

        has_lexical_verb = any(
            item.get('simple_pos') == self.VERB_TAG and not self._is_auxiliary(item)
            for item in items
        )

        filtered = []
        for item in items:
            source = self._normalized_source(item)
            simple_pos = item.get('simple_pos')

            if self.drop_articles and simple_pos == 'Determiner' and source in self.ARTICLE_WORDS:
                continue

            if self.replace_lexical_negation and features.get('is_negative') and source in self.NEGATION_WORDS:
                continue

            if self.drop_redundant_auxiliaries and has_lexical_verb and self._is_auxiliary(item):
                continue

            filtered.append(item)

        return filtered

    def _apply_adjective_order_items(self, items):
        if not items:
            return []

        ordered = list(items)
        for _ in range(len(ordered)):
            changed = False
            i = 0
            while i < len(ordered) - 1:
                cur = ordered[i]
                nxt = ordered[i + 1]
                cur_pos = cur.get('simple_pos')
                nxt_pos = nxt.get('simple_pos')

                if self.adjective_position == 'after':
                    if cur_pos == 'Adjective' and nxt_pos in self.NOMINAL_TAGS:
                        ordered[i], ordered[i + 1] = ordered[i + 1], ordered[i]
                        changed = True
                        i += 2
                        continue
                else:
                    if cur_pos in self.NOMINAL_TAGS and nxt_pos == 'Adjective':
                        ordered[i], ordered[i + 1] = ordered[i + 1], ordered[i]
                        changed = True
                        i += 2
                        continue
                i += 1

            if not changed:
                break

        return ordered

    def _apply_adposition_order_items(self, items):
        if not items or self.adposition_order == 'preposition':
            return list(items)

        reordered = []
        i = 0
        while i < len(items):
            current = items[i]
            if current.get('simple_pos') == 'Preposition':
                j = i + 1
                while j < len(items) and items[j].get('simple_pos') in {'Determiner', 'Adjective', 'Number'}:
                    j += 1
                if j < len(items) and items[j].get('simple_pos') in self.NOMINAL_TAGS:
                    reordered.extend(items[i + 1:j + 1])
                    reordered.append(current)
                    i = j + 1
                    continue

            reordered.append(current)
            i += 1

        return reordered

    def _reorder_by_word_order_items(self, items, roles):
        if not items:
            return []

        verbs = [item for item in items if item.get('simple_pos') == self.VERB_TAG]
        if not verbs:
            return list(items)

        subjects = [item for item in items if id(item) in roles['subject'] and item.get('simple_pos') in self.NOMINAL_TAGS]
        objects = [item for item in items if id(item) in roles['object'] and item.get('simple_pos') in self.NOMINAL_TAGS]

        structural_ids = set(id(item) for item in subjects + verbs + objects)
        if not structural_ids:
            return list(items)

        structural_indexes = [idx for idx, item in enumerate(items) if id(item) in structural_ids]
        first_struct = min(structural_indexes)
        last_struct = max(structural_indexes)

        prelude = [item for idx, item in enumerate(items) if idx < first_struct and id(item) not in structural_ids]
        middle_extras = [
            item for idx, item in enumerate(items)
            if first_struct <= idx <= last_struct and id(item) not in structural_ids
        ]
        trailing = [item for idx, item in enumerate(items) if idx > last_struct and id(item) not in structural_ids]

        slots = {
            'S': subjects,
            'V': verbs,
            'O': objects,
        }

        arranged_core = []
        for symbol in self.word_order:
            arranged_core.extend(slots.get(symbol, []))

        return prelude + arranged_core + middle_extras + trailing

    def _apply_adverb_position_items(self, items):
        if not items:
            return []

        adverbs = [
            item for item in items
            if item.get('simple_pos') == 'Adverb' and self._normalized_source(item) not in self.NEGATION_WORDS
        ]
        if not adverbs:
            return list(items)

        remaining = [item for item in items if item not in adverbs]
        verb_indexes = [idx for idx, item in enumerate(remaining) if item.get('simple_pos') == self.VERB_TAG]
        if not verb_indexes:
            return list(items)

        if self.adverb_position == 'before':
            insert_index = verb_indexes[0]
        else:
            insert_index = verb_indexes[-1] + 1

        return remaining[:insert_index] + adverbs + remaining[insert_index:]

    def _apply_nominal_inflection(self, items, roles):
        for item in items:
            simple_pos = item.get('simple_pos')
            if simple_pos not in self.NOMINAL_TAGS:
                continue
            if simple_pos == 'Pronoun' and not self.case_mark_pronouns:
                continue

            number = self._infer_number(item)

            grammatical_case = 'core'
            if id(item) in roles['genitive']:
                grammatical_case = 'genitive'
            elif id(item) in roles['object']:
                grammatical_case = 'accusative'

            token = item.get('token', '')
            item['token'] = self.inflect_noun(token, number=number, grammatical_case=grammatical_case)

        return items

    def _apply_verb_inflection(self, items, features):
        for item in items:
            if item.get('simple_pos') != self.VERB_TAG:
                continue
            token = item.get('token', '')
            item['token'] = self.inflect_verb(
                token,
                tense=features.get('tense', 'present'),
                aspect=features.get('aspect', 'simple'),
                person=features.get('person', '3'),
                number=features.get('number', 'singular'),
                mood=features.get('mood', 'indicative'),
            )
        return items

    def _make_particle_item(self, token, source_hint, simple_pos='Particle'):
        return {
            'token': token,
            'tag': 'PART',
            'simple_pos': simple_pos,
            'is_punctuation': False,
            'is_proper_noun': False,
            'source_token': source_hint,
            'source_normalized': str(source_hint).lower(),
        }

    def _case_particle_for(self, grammatical_case):
        case_value = str(grammatical_case or 'core').lower()
        if case_value in {'nom', 'nominative', 'subject', 'core'}:
            return str(self.nominative_particle or '')
        if case_value in {'acc', 'accusative', 'object'}:
            return str(self.accusative_particle or '')
        if case_value in {'gen', 'genitive', 'possessive'}:
            return str(self.genitive_particle or '')
        return ''

    def _insert_case_particles(self, items, roles):
        if not self.enable_case_marking or self.case_marking_style != 'particle':
            return list(items)

        expanded = []
        for item in items:
            expanded.append(item)
            if item.get('simple_pos') not in self.NOMINAL_TAGS:
                continue
            if item.get('simple_pos') == 'Pronoun' and not self.case_mark_pronouns:
                continue

            grammatical_case = 'core'
            if id(item) in roles['genitive']:
                grammatical_case = 'genitive'
            elif id(item) in roles['object']:
                grammatical_case = 'accusative'
            elif id(item) in roles['subject']:
                grammatical_case = 'nominative'

            particle = self._case_particle_for(grammatical_case)
            if not particle:
                continue

            if grammatical_case == 'genitive':
                source_hint = 'possessive-case'
            elif grammatical_case == 'accusative':
                source_hint = 'object-case'
            else:
                source_hint = 'subject-case'

            expanded.append(self._make_particle_item(particle, source_hint=source_hint, simple_pos='CaseParticle'))

        return expanded

    def _insert_negation_particle(self, items, features):
        if not features.get('is_negative'):
            return list(items)
        if not self.negation_particle:
            return list(items)

        if any(item.get('token') == self.negation_particle and item.get('simple_pos') == 'NegationParticle' for item in items):
            return list(items)

        particle = self._make_particle_item(self.negation_particle, source_hint='not', simple_pos='NegationParticle')
        if self.negation_position == 'clause_final':
            return list(items) + [particle]

        verb_indexes = [idx for idx, item in enumerate(items) if item.get('simple_pos') == self.VERB_TAG]
        if not verb_indexes:
            return [particle] + list(items)

        if self.negation_position == 'after_verb':
            insert_index = verb_indexes[-1] + 1
        else:
            insert_index = verb_indexes[0]

        return list(items[:insert_index]) + [particle] + list(items[insert_index:])

    def _insert_question_particle(self, items, features):
        if not features.get('is_question'):
            return list(items)
        if not self.question_particle:
            return list(items)

        if any(item.get('token') == self.question_particle and item.get('simple_pos') == 'QuestionParticle' for item in items):
            return list(items)

        particle = self._make_particle_item(self.question_particle, source_hint='question', simple_pos='QuestionParticle')

        if self.question_particle_position == 'clause_initial':
            return [particle] + list(items)
        return list(items) + [particle]

    def transform_clause(self, clause_items, clause_ending=None):
        if not clause_items:
            return []

        working = [dict(item) for item in clause_items]

        features = self._detect_clause_features(working, clause_ending=clause_ending)

        stripped = self._strip_function_words(working, features)
        if stripped:
            working = stripped

        roles = self._infer_roles(working)

        working = self._apply_adjective_order_items(working)
        working = self._apply_adposition_order_items(working)
        working = self._reorder_by_word_order_items(working, roles)
        working = self._apply_adverb_position_items(working)
        working = self._apply_nominal_inflection(working, roles)
        working = self._apply_verb_inflection(working, features)
        working = self._insert_case_particles(working, roles)
        working = self._insert_negation_particle(working, features)
        working = self._insert_question_particle(working, features)
        return working

    def apply_adjective_order(self, token_pairs):
        if not token_pairs:
            return []

        ordered = list(token_pairs)
        i = 0
        while i < len(ordered) - 1:
            cur_word, cur_pos = ordered[i]
            nxt_word, nxt_pos = ordered[i + 1]

            if self.adjective_position == 'after':
                if cur_pos == 'Adjective' and nxt_pos in self.NOMINAL_TAGS:
                    ordered[i], ordered[i + 1] = ordered[i + 1], ordered[i]
                    i += 2
                    continue
            else:
                if cur_pos in self.NOMINAL_TAGS and nxt_pos == 'Adjective':
                    ordered[i], ordered[i + 1] = ordered[i + 1], ordered[i]
                    i += 2
                    continue
            i += 1

        return ordered

    def reorder_clause(self, token_pairs):
        if not token_pairs:
            return []

        with_adjectives = self.apply_adjective_order(token_pairs)

        verbs = [pair for pair in with_adjectives if pair[1] == self.VERB_TAG]
        if not verbs:
            return with_adjectives

        first_verb_index = next((idx for idx, pair in enumerate(with_adjectives) if pair[1] == self.VERB_TAG), None)
        if first_verb_index is None:
            return with_adjectives

        subjects = [
            pair for idx, pair in enumerate(with_adjectives)
            if pair[1] in self.NOMINAL_TAGS and idx < first_verb_index
        ]
        objects = [
            pair for idx, pair in enumerate(with_adjectives)
            if pair[1] in self.NOMINAL_TAGS and idx > first_verb_index
        ]

        structural = set(id(pair) for pair in subjects + verbs + objects)
        extras = [pair for pair in with_adjectives if id(pair) not in structural]

        slots = {
            'S': subjects,
            'V': verbs,
            'O': objects,
        }

        arranged = []
        for symbol in self.word_order:
            arranged.extend(slots.get(symbol, []))

        arranged.extend(extras)
        return arranged
