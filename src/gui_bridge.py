import argparse
import contextlib
import copy
import io
import json
import os
import sys
import traceback

if __package__ is None or __package__ == '':
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from src.language_generator.defaults import (  # noqa: E402
    DEFAULT_GRAMMAR_PARAMS,
    DEFAULT_MORPHOLOGY_PARAMS,
    DEFAULT_NAMEGEN_PARAMS,
    DEFAULT_PHONOLOGY_PARAMS,
    DEFAULT_SOUND_CHANGE_RULES,
    DEFAULT_WORDGEN_PARAMS,
    deep_merge,
)
from src.language_generator.language import Language  # noqa: E402
from src.language_generator.pseudo_real_world import (  # noqa: E402
    list_pseudo_templates_by_region,
)
from src.language_generator.sound_change import SoundChangeEngine  # noqa: E402
from src.language_generator.storage import LanguageStorage  # noqa: E402
from src.language_generator.templates import (  # noqa: E402
    list_builtin_templates,
    list_templates,
    template_description,
)


def _compact_list(value):
    if value is None:
        return None
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(',') if item.strip()]
    return None


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)

    normalized = str(value).strip().lower()
    if normalized in {'1', 'true', 'yes', 'on'}:
        return True
    if normalized in {'0', 'false', 'no', 'off', ''}:
        return False
    return bool(value)


def _load_language(storage_dir, language_ref):
    storage = LanguageStorage(storage_dir)
    path = storage.resolve_language_path(language_ref)
    if path is None:
        raise ValueError(f"Language '{language_ref}' was not found.")

    language = Language.load(path)
    if language is None:
        raise ValueError(f"Failed to load language from '{path}'.")
    return language, path, storage


def _normalize_overrides(overrides):
    if not isinstance(overrides, dict):
        return {}

    normalized = copy.deepcopy(overrides)

    phonology = normalized.get('phonology')
    if isinstance(phonology, dict):
        for key in ['consonants', 'vowels', 'syllable_structures', 'onsets', 'codas', 'epenthetic_vowels', 'hiatus_glides', 'allowed_boundary_clusters']:
            if key in phonology:
                compacted = _compact_list(phonology.get(key))
                if compacted is not None:
                    phonology[key] = compacted

    morphology = normalized.get('morphology')
    if isinstance(morphology, dict):
        for key in ['num_roots', 'num_prefixes', 'num_suffixes', 'root_min_syl', 'root_max_syl', 'affix_max_syl']:
            if key in morphology and morphology[key] != '':
                try:
                    morphology[key] = int(morphology[key])
                except (TypeError, ValueError):
                    morphology.pop(key, None)

    grammar = normalized.get('grammar')
    if isinstance(grammar, dict):
        for key in [
            'enable_case_marking',
            'drop_articles',
            'drop_redundant_auxiliaries',
            'case_mark_pronouns',
            'enable_subject_agreement',
            'replace_lexical_negation',
        ]:
            if key in grammar:
                grammar[key] = _as_bool(grammar[key])

    quality = normalized.get('generation_quality')
    if isinstance(quality, dict):
        if 'min_pronounceability_score' in quality:
            try:
                quality['min_pronounceability_score'] = int(quality['min_pronounceability_score'])
            except (TypeError, ValueError):
                quality.pop('min_pronounceability_score', None)

    wordgen = normalized.get('word_generator_params')
    if isinstance(wordgen, dict):
        for key in ['prefix_prob', 'suffix_prob', 'function_word_long_form_chance']:
            if key in wordgen and wordgen[key] != '':
                try:
                    wordgen[key] = float(wordgen[key])
                except (TypeError, ValueError):
                    wordgen.pop(key, None)
        for key in ['function_word_min_syl', 'function_word_max_syl', 'function_word_max_chars']:
            if key in wordgen and wordgen[key] != '':
                try:
                    wordgen[key] = int(wordgen[key])
                except (TypeError, ValueError):
                    wordgen.pop(key, None)
        if 'max_gen_attempts' in wordgen:
            try:
                wordgen['max_gen_attempts'] = int(wordgen['max_gen_attempts'])
            except (TypeError, ValueError):
                wordgen.pop('max_gen_attempts', None)
        for key in ['compact_function_words', 'function_word_allow_affixes']:
            if key in wordgen:
                wordgen[key] = _as_bool(wordgen[key])
        for key in ['function_word_pos_tags', 'function_word_meanings']:
            if key in wordgen:
                compacted = _compact_list(wordgen.get(key))
                if compacted is not None:
                    wordgen[key] = compacted

    namegen = normalized.get('name_generator_params')
    if isinstance(namegen, dict):
        for key in ['person_min_syl', 'person_max_syl', 'place_min_syl', 'place_max_syl', 'thing_min_syl', 'thing_max_syl', 'max_attempts']:
            if key in namegen and namegen[key] != '':
                try:
                    namegen[key] = int(namegen[key])
                except (TypeError, ValueError):
                    namegen.pop(key, None)
        for key in ['person_suffix_prob', 'place_suffix_prob', 'thing_suffix_prob']:
            if key in namegen and namegen[key] != '':
                try:
                    namegen[key] = float(namegen[key])
                except (TypeError, ValueError):
                    namegen.pop(key, None)
        for key in ['person_male_suffixes', 'person_female_suffixes', 'person_neutral_suffixes', 'place_suffixes', 'thing_suffixes']:
            if key in namegen:
                compacted = _compact_list(namegen.get(key))
                if compacted is not None:
                    namegen[key] = compacted

    return normalized


def _base_config_from_template(template_name):
    template = Language.from_template(template_name=template_name, bootstrap=False)
    return template.get_config(), template


def _base_default_config():
    return {
        'template_name': 'custom',
        'style_preset': 'custom',
        'phonology': copy.deepcopy(DEFAULT_PHONOLOGY_PARAMS),
        'morphology': copy.deepcopy(DEFAULT_MORPHOLOGY_PARAMS),
        'lexicon': {'entries': {}},
        'word_generator_params': copy.deepcopy(DEFAULT_WORDGEN_PARAMS),
        'name_generator_params': copy.deepcopy(DEFAULT_NAMEGEN_PARAMS),
        'grammar': copy.deepcopy(DEFAULT_GRAMMAR_PARAMS),
        'sound_change_rules': copy.deepcopy(DEFAULT_SOUND_CHANGE_RULES),
        'generation_quality': {'min_pronounceability_score': 58},
    }


def action_list_templates(payload):
    templates = []
    for name in list_templates():
        templates.append({'name': name, 'description': template_description(name)})

    return {
        'templates': templates,
        'builtins': list_builtin_templates(),
        'pseudoByRegion': list_pseudo_templates_by_region(),
    }


def action_list_languages(payload):
    storage_dir = payload.get('storageDir', os.path.join('src', 'languages'))
    storage = LanguageStorage(storage_dir)
    paths = storage.list_languages()

    languages = []
    for path in paths:
        language = Language.load(path)
        metadata = language.metadata if language else {}
        languages.append({
            'path': path,
            'name': metadata.get('name', os.path.splitext(os.path.basename(path))[0]),
            'template': metadata.get('template_name', 'unknown'),
            'style': metadata.get('style_preset', 'unknown'),
        })

    return {'languages': languages}


def action_update_language(payload):
    storage_dir = payload.get('storageDir', os.path.join('src', 'languages'))
    language_ref = payload.get('language')
    updates = payload.get('updates', {})
    rename_file = bool(payload.get('renameFile', False))

    if not isinstance(updates, dict):
        raise ValueError('updates must be an object.')

    language, path, storage = _load_language(storage_dir, language_ref)
    metadata = copy.deepcopy(language.metadata or {})

    name_value = str(updates.get('name', '') or '').strip()
    template_value = str(updates.get('template_name', '') or '').strip()
    style_value = str(updates.get('style_preset', '') or '').strip()

    if name_value:
        metadata['name'] = name_value
    if template_value:
        metadata['template_name'] = template_value
        language.template_name = template_value
    if style_value:
        metadata['style_preset'] = style_value
        language.style_preset = style_value

    output_path = path
    old_path = path
    if rename_file and name_value:
        target_path = storage.language_path(name_value)
        if os.path.abspath(target_path) != os.path.abspath(path):
            if os.path.exists(target_path):
                raise ValueError(f"Cannot rename file because '{target_path}' already exists.")
            output_path = target_path

    if not language.save(output_path, metadata=metadata):
        raise RuntimeError(f"Failed to save language at '{output_path}'.")

    if os.path.abspath(output_path) != os.path.abspath(path) and os.path.exists(path):
        os.remove(path)

    return {
        'path': output_path,
        'oldPath': old_path,
        'renamed': os.path.abspath(output_path) != os.path.abspath(old_path),
        'metadata': metadata,
    }


def action_delete_language(payload):
    storage_dir = payload.get('storageDir', os.path.join('src', 'languages'))
    language_ref = payload.get('language')

    _language, path, _storage = _load_language(storage_dir, language_ref)

    if not os.path.exists(path):
        raise ValueError(f"Language file '{path}' does not exist.")

    os.remove(path)
    return {'deleted': True, 'path': path}


def action_create_language(payload):
    storage_dir = payload.get('storageDir', os.path.join('src', 'languages'))
    storage = LanguageStorage(storage_dir)

    language_name = payload.get('name', 'generated-language').strip() or 'generated-language'
    template_name = (payload.get('template') or '').strip()
    bootstrap = bool(payload.get('bootstrap', True))

    if template_name:
        base_config, template_language = _base_config_from_template(template_name)
        config = copy.deepcopy(base_config)
        metadata = copy.deepcopy(template_language.metadata)
        config['lexicon'] = {'entries': {}}
    else:
        config = _base_default_config()
        metadata = {}

    manual_overrides = _normalize_overrides(payload.get('overrides', {}))

    for section in ['phonology', 'morphology', 'word_generator_params', 'name_generator_params', 'grammar', 'generation_quality']:
        section_overrides = manual_overrides.get(section)
        if isinstance(section_overrides, dict):
            config[section] = deep_merge(config.get(section, {}), section_overrides)

    sound_rules = manual_overrides.get('sound_change_rules')
    if isinstance(sound_rules, list):
        config['sound_change_rules'] = sound_rules

    if template_name:
        config['template_name'] = template_name
        config['style_preset'] = template_name

    metadata.update({
        'name': language_name,
        'template_name': config.get('template_name', template_name or 'custom'),
        'style_preset': config.get('style_preset', template_name or 'custom'),
        'created_with_gui': True,
    })

    language = Language.from_config(config=config, metadata=metadata, bootstrap=bootstrap)

    output_path = payload.get('outputPath')
    if output_path:
        save_path = os.path.abspath(output_path)
    else:
        save_path = storage.language_path(language_name)

    if not language.save(save_path, metadata=metadata):
        raise RuntimeError(f"Failed to save generated language at '{save_path}'.")

    return {
        'path': save_path,
        'name': language_name,
        'template': language.template_name,
        'style': language.style_preset,
        'metadata': language.metadata,
    }


def action_translate(payload):
    storage_dir = payload.get('storageDir', os.path.join('src', 'languages'))
    language_ref = payload.get('language')
    text = payload.get('text', '')
    use_grammar = bool(payload.get('useGrammar', False))

    language, path, _storage = _load_language(storage_dir, language_ref)
    detail = language.translate_with_breakdown(text, use_grammar=use_grammar)

    if bool(payload.get('autosave', False)):
        language.save(path)

    return {
        'translated': detail.get('translated', ''),
        'breakdown': detail.get('breakdown', []),
        'dictionary': detail.get('dictionary', []),
        'path': path,
        'sourceText': text,
        'useGrammar': use_grammar,
    }


def action_dictionary_lookup(payload):
    storage_dir = payload.get('storageDir', os.path.join('src', 'languages'))
    language_ref = payload.get('language')
    query = payload.get('query')
    if query is None:
        query = payload.get('word', '')

    language, path, _storage = _load_language(storage_dir, language_ref)
    lookup = language.lookup_dictionary_entry(query)

    return {
        'path': path,
        'query': lookup.get('query', str(query or '')),
        'found': bool(lookup.get('found', False)),
        'match': lookup.get('match'),
        'entry': lookup.get('entry'),
    }


def action_generate(payload):
    storage_dir = payload.get('storageDir', os.path.join('src', 'languages'))
    language_ref = payload.get('language')
    kind = payload.get('kind', 'word')
    count = int(payload.get('count', 10))
    min_syl = int(payload.get('minSyllables', 1))
    max_syl = int(payload.get('maxSyllables', 4))
    min_score = int(payload.get('minScore', 58))

    language, path, _storage = _load_language(storage_dir, language_ref)

    results = []
    for index in range(max(1, count)):
        label = payload.get('meaningPrefix', 'gui-generated-') + str(index + 1)

        if kind == 'noun':
            word = language.generate_noun(
                english_meaning=label,
                noun_type='common',
                number=payload.get('number', 'singular'),
                grammatical_case=payload.get('grammaticalCase', 'core'),
            )
        elif kind == 'proper-noun':
            word = language.generate_noun(
                english_meaning=label,
                noun_type='proper',
                category=payload.get('category', 'person'),
                gender=payload.get('gender'),
            )
        elif kind == 'name':
            word = language.generate_proper_noun(
                label,
                category=payload.get('category', 'person'),
                gender=payload.get('gender'),
            )
        else:
            word = language.phonology.generate_word(min_syl, max_syl)
            if word and not language.evaluator.is_acceptable(word, min_score=min_score):
                word = None

        results.append({'index': index + 1, 'value': word})

    if bool(payload.get('autosave', False)):
        language.save(path)

    return {'results': results, 'path': path}


def action_style_switch(payload):
    storage_dir = payload.get('storageDir', os.path.join('src', 'languages'))
    language_ref = payload.get('language')
    style = payload.get('style')

    if not style:
        raise ValueError('style is required for style switching.')

    language, path, _storage = _load_language(storage_dir, language_ref)
    language.switch_style_preset(
        preset_name=style,
        regenerate_lexicon=bool(payload.get('regenerateLexicon', False)),
        bootstrap=not bool(payload.get('noBootstrap', False)),
    )

    output_path = os.path.abspath(payload.get('outputPath')) if payload.get('outputPath') else path
    language.save(output_path, metadata={
        'template_name': language.template_name,
        'style_preset': language.style_preset,
        'style_switched_at_runtime': True,
    })

    return {
        'path': output_path,
        'style': language.style_preset,
        'template': language.template_name,
    }


def action_derive(payload):
    storage_dir = payload.get('storageDir', os.path.join('src', 'languages'))
    language_ref = payload.get('language')
    preset = payload.get('preset', 'lenition')
    language_name = payload.get('name')

    language, path, storage = _load_language(storage_dir, language_ref)
    daughter = language.derive_daughter_language(preset_name=preset)
    if daughter is None:
        raise RuntimeError('Unable to derive daughter language from current settings.')

    base_name = language_name or f"{language.metadata.get('name', 'derived')}-{preset}"
    daughter.metadata['name'] = base_name

    output_path = os.path.abspath(payload.get('outputPath')) if payload.get('outputPath') else storage.language_path(base_name)
    daughter.save(output_path, metadata={'name': base_name, 'derived_with_preset': preset})

    return {'path': output_path, 'name': base_name, 'preset': preset}


def action_evaluate(payload):
    storage_dir = payload.get('storageDir', os.path.join('src', 'languages'))
    language_ref = payload.get('language')
    count = int(payload.get('count', 40))
    min_score = int(payload.get('minScore', 58))
    min_syl = int(payload.get('minSyllables', 1))
    max_syl = int(payload.get('maxSyllables', 4))

    language, path, _storage = _load_language(storage_dir, language_ref)

    results = []
    accepted = 0
    for idx in range(max(1, count)):
        word = language.phonology.generate_word(min_syl, max_syl)
        if not word:
            continue
        score = language.evaluator.score_word(word)
        is_accepted = score['score'] >= min_score
        if is_accepted:
            accepted += 1
        score['accepted'] = is_accepted
        results.append(score)

    return {
        'path': path,
        'accepted': accepted,
        'total': len(results),
        'results': results,
    }


def action_sound_change_presets(payload):
    return {'presets': SoundChangeEngine.available_presets()}


def action_load_language(payload):
    storage_dir = payload.get('storageDir', os.path.join('src', 'languages'))
    language_ref = payload.get('language')
    language, path, _storage = _load_language(storage_dir, language_ref)

    return {
        'path': path,
        'template': language.template_name,
        'style': language.style_preset,
        'metadata': language.metadata,
        'config': language.get_config(),
    }


ACTION_MAP = {
    'list_templates': action_list_templates,
    'list_languages': action_list_languages,
    'update_language': action_update_language,
    'delete_language': action_delete_language,
    'create_language': action_create_language,
    'translate': action_translate,
    'dictionary_lookup': action_dictionary_lookup,
    'generate': action_generate,
    'style_switch': action_style_switch,
    'derive': action_derive,
    'evaluate': action_evaluate,
    'sound_change_presets': action_sound_change_presets,
    'load_language': action_load_language,
}


def _parse_payload(stdin_payload):
    if not stdin_payload:
        return {}
    try:
        return json.loads(stdin_payload)
    except json.JSONDecodeError:
        return {}


def main():
    parser = argparse.ArgumentParser(description='GUI bridge for Conlang Studio.')
    parser.add_argument('--action', required=True, choices=sorted(ACTION_MAP.keys()))
    args = parser.parse_args()

    payload = _parse_payload(sys.stdin.read())

    output_capture = io.StringIO()
    try:
        with contextlib.redirect_stdout(output_capture):
            result = ACTION_MAP[args.action](payload)
        response = {'ok': True, 'result': result, 'logs': output_capture.getvalue()}
    except Exception as error:
        response = {
            'ok': False,
            'error': str(error),
            'logs': output_capture.getvalue(),
            'traceback': traceback.format_exc(),
        }

    print(json.dumps(response, ensure_ascii=False))


if __name__ == '__main__':
    main()
