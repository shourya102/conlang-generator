import argparse
import os
import sys

if __package__ is None or __package__ == '':
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from src.language_generator.language import Language
from src.language_generator.prompt_system import ask_choice, ask_int, ask_text, ask_yes_no
from src.language_generator.pseudo_real_world import list_pseudo_templates_by_region
from src.language_generator.sound_change import SoundChangeEngine
from src.language_generator.storage import LanguageStorage
from src.language_generator.templates import list_builtin_templates, list_templates, template_description


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_STORAGE_DIR = os.path.join(BASE_DIR, 'languages')


def _print_header():
    print('Conlang Studio CLI')
    print('=' * 60)


def _resolve_language(storage, language_ref):
    path = storage.resolve_language_path(language_ref)
    if path is None:
        raise ValueError(f"Language '{language_ref}' was not found.")

    language = Language.load(path)
    if language is None:
        raise ValueError(f"Failed to load language from '{path}'.")
    return language, path


def _save_language(language, output_path, metadata=None):
    saved = language.save(output_path, metadata=metadata)
    if not saved:
        raise RuntimeError(f"Failed to save language to '{output_path}'.")
    return output_path


def cmd_templates(_args):
    _print_header()
    print('Tip: pseudo templates also accept aliases like latin, english, spanish, japanese, hindi, bengali, and tamil.')
    print('Built-in templates:')
    for template_name in list_builtin_templates():
        print(f"- {template_name}: {template_description(template_name)}")

    print('\nPseudo real-world templates:')
    by_region = list_pseudo_templates_by_region()
    for region in sorted(by_region.keys()):
        print(f"  {region.replace('-', ' ').title()}")
        for template_name in by_region[region]:
            print(f"  - {template_name}: {template_description(template_name)}")


def cmd_new(args):
    _print_header()
    storage = LanguageStorage(args.storage_dir)

    language = Language.from_template(
        template_name=args.template,
        bootstrap=not args.no_bootstrap,
        metadata={'name': args.name},
    )

    if args.output:
        output_path = os.path.abspath(args.output)
    else:
        output_path = storage.language_path(args.name)

    _save_language(
        language,
        output_path,
        metadata={
            'name': args.name,
            'template_name': language.template_name,
            'style_preset': language.style_preset,
        },
    )

    print(f"Created language '{args.name}' from template '{args.template}'.")
    print(f"Saved to: {output_path}")


def cmd_translate(args):
    _print_header()
    storage = LanguageStorage(args.storage_dir)
    language, path = _resolve_language(storage, args.language)

    text = args.text if args.text else ask_text('Enter English text to translate')
    if args.use_grammar:
        translated = language.translate_with_grammar(text)
    else:
        translated = language.translate(text)

    print('\nTranslation:')
    print(translated)

    if args.autosave:
        _save_language(language, path)


def cmd_generate(args):
    _print_header()
    storage = LanguageStorage(args.storage_dir)
    language, path = _resolve_language(storage, args.language)

    print(f"Generating {args.count} items of kind '{args.kind}'")

    outputs = []
    for index in range(args.count):
        label = f"{args.meaning_prefix}{index + 1}"

        if args.kind == 'noun':
            generated = language.generate_noun(
                english_meaning=label,
                noun_type='common',
                number=args.number,
                grammatical_case=args.grammatical_case,
            )
        elif args.kind == 'proper-noun':
            generated = language.generate_noun(
                english_meaning=label,
                noun_type='proper',
                category=args.category,
                gender=args.gender,
            )
        elif args.kind == 'name':
            generated = language.generate_proper_noun(label, category=args.category, gender=args.gender)
        else:
            generated = language.phonology.generate_word(args.min_syllables, args.max_syllables)
            if generated and not language.evaluator.is_acceptable(generated, min_score=args.min_score):
                generated = None

        if generated:
            outputs.append(generated)
            print(f"{index + 1}. {generated}")
        else:
            print(f"{index + 1}. [generation failed]")

    if args.autosave:
        _save_language(language, path)


def cmd_derive(args):
    _print_header()
    storage = LanguageStorage(args.storage_dir)
    language, _ = _resolve_language(storage, args.language)

    daughter = language.derive_daughter_language(preset_name=args.preset)
    if daughter is None:
        raise RuntimeError('No sound-change rules were available to derive a daughter language.')

    if args.output:
        output_path = os.path.abspath(args.output)
    else:
        name = args.name if args.name else f"{language.metadata.get('name', 'derived')}-{args.preset}"
        output_path = storage.language_path(name)

    _save_language(
        daughter,
        output_path,
        metadata={
            'name': args.name if args.name else os.path.splitext(os.path.basename(output_path))[0],
            'derived_with_preset': args.preset,
        },
    )

    print(f"Derived daughter language using preset '{args.preset}'.")
    print(f"Saved to: {output_path}")


def cmd_style(args):
    _print_header()
    storage = LanguageStorage(args.storage_dir)
    language, path = _resolve_language(storage, args.language)

    language.switch_style_preset(
        preset_name=args.style,
        regenerate_lexicon=args.regenerate_lexicon,
        bootstrap=not args.no_bootstrap,
    )

    output_path = os.path.abspath(args.output) if args.output else path
    _save_language(
        language,
        output_path,
        metadata={
            'style_preset': language.style_preset,
            'template_name': language.template_name,
            'style_switched_at_runtime': True,
        },
    )

    print(f"Switched style preset to '{args.style}'.")
    print(f"Saved to: {output_path}")


def cmd_evaluate(args):
    _print_header()
    storage = LanguageStorage(args.storage_dir)
    language, _ = _resolve_language(storage, args.language)

    print(f"Evaluating {args.count} generated words with threshold {args.min_score}")

    accepted = 0
    for index in range(args.count):
        candidate = language.phonology.generate_word(args.min_syllables, args.max_syllables)
        if not candidate:
            print(f"{index + 1}. [generation failed]")
            continue

        result = language.evaluator.score_word(candidate)
        status = 'ACCEPT' if result['score'] >= args.min_score else 'REJECT'
        if status == 'ACCEPT':
            accepted += 1

        if args.only_rejected and status == 'ACCEPT':
            continue

        print(f"{index + 1}. {candidate:<18} score={result['score']:>3} {status} issues={','.join(result['issues']) or 'none'}")

    print(f"Accepted: {accepted}/{args.count}")


def cmd_list_languages(args):
    _print_header()
    storage = LanguageStorage(args.storage_dir)
    paths = storage.list_languages()
    if not paths:
        print('No stored languages found.')
        return

    print('Stored languages:')
    for path in paths:
        print(f"- {path}")


def cmd_interactive(args):
    _print_header()
    storage = LanguageStorage(args.storage_dir)

    active_language = None
    active_path = None

    templates = list_templates()

    while True:
        print('\nInteractive Menu')
        active_label = active_path if active_path else '[none loaded]'
        print(f"Active language: {active_label}")

        choice = ask_choice(
            'Choose an action:',
            [
                'Create language from template',
                'Load language',
                'Save active language',
                'Translate text',
                'Translate text with grammar',
                'Generate words and nouns',
                'Derive daughter language',
                'Switch style preset',
                'Evaluate generated outputs',
                'List templates',
                'List saved languages',
                'Exit',
            ],
            default_index=0,
        )

        if choice == 'Create language from template':
            template = ask_choice('Select template:', templates, default_index=0)
            language_name = ask_text('Language name', default=f"{template}-language")
            bootstrap = ask_yes_no('Bootstrap core lexicon?', default=True)
            active_language = Language.from_template(template_name=template, bootstrap=bootstrap, metadata={'name': language_name})
            active_path = storage.language_path(language_name)
            _save_language(
                active_language,
                active_path,
                metadata={'name': language_name, 'template_name': template, 'style_preset': template},
            )
            print(f"Created and saved: {active_path}")

        elif choice == 'Load language':
            reference = ask_text('Enter language name or path')
            try:
                active_language, active_path = _resolve_language(storage, reference)
                print(f"Loaded language from: {active_path}")
            except Exception as error:
                print(f"Error: {error}")

        elif choice == 'Save active language':
            if active_language is None:
                print('No language is currently loaded.')
                continue
            target = ask_text('Save path', default=active_path)
            try:
                _save_language(active_language, target)
                active_path = target
                print(f"Saved language to: {active_path}")
            except Exception as error:
                print(f"Error: {error}")

        elif choice == 'Translate text':
            if active_language is None:
                print('Load or create a language first.')
                continue
            text = ask_text('English text')
            print(active_language.translate(text, use_grammar=False))

        elif choice == 'Translate text with grammar':
            if active_language is None:
                print('Load or create a language first.')
                continue
            text = ask_text('English text')
            print(active_language.translate_with_grammar(text))

        elif choice == 'Generate words and nouns':
            if active_language is None:
                print('Load or create a language first.')
                continue

            gen_kind = ask_choice('What do you want to generate?', ['word', 'noun', 'proper-noun', 'name'])
            count = ask_int('Count', default=10, minimum=1, maximum=200)
            min_score = ask_int('Minimum pronounceability score', default=58, minimum=0, maximum=100)

            for idx in range(count):
                label = f"interactive-{idx + 1}"
                if gen_kind == 'word':
                    generated = active_language.phonology.generate_word(1, 3)
                    if generated and not active_language.evaluator.is_acceptable(generated, min_score=min_score):
                        generated = None
                elif gen_kind == 'noun':
                    generated = active_language.generate_noun(english_meaning=label, noun_type='common')
                elif gen_kind == 'proper-noun':
                    generated = active_language.generate_noun(english_meaning=label, noun_type='proper', category='person')
                else:
                    generated = active_language.generate_proper_noun(label, category='person')

                print(f"{idx + 1}. {generated if generated else '[generation failed]'}")

        elif choice == 'Derive daughter language':
            if active_language is None:
                print('Load or create a language first.')
                continue

            preset = ask_choice('Select sound-change preset:', SoundChangeEngine.available_presets())
            new_name = ask_text('Name for daughter language', default=f"{active_language.metadata.get('name', 'language')}-{preset}")
            daughter = active_language.derive_daughter_language(preset_name=preset)
            if daughter is None:
                print('Derivation failed.')
                continue
            daughter.metadata['name'] = new_name
            daughter_path = storage.language_path(new_name)
            _save_language(daughter, daughter_path, metadata={'name': new_name, 'derived_with_preset': preset})
            print(f"Derived language saved to: {daughter_path}")

        elif choice == 'Switch style preset':
            if active_language is None:
                print('Load or create a language first.')
                continue

            style = ask_choice('Select style preset:', list_templates())
            regenerate_lexicon = ask_yes_no('Regenerate lexicon for new style?', default=False)
            active_language.switch_style_preset(
                preset_name=style,
                regenerate_lexicon=regenerate_lexicon,
                bootstrap=True,
            )
            print(f"Switched active style to: {style}")

        elif choice == 'Evaluate generated outputs':
            if active_language is None:
                print('Load or create a language first.')
                continue
            count = ask_int('How many words to evaluate?', default=25, minimum=1, maximum=500)
            threshold = ask_int('Acceptance threshold', default=58, minimum=0, maximum=100)
            rejected = 0
            for idx in range(count):
                candidate = active_language.phonology.generate_word(1, 4)
                if not candidate:
                    continue
                score = active_language.evaluator.score_word(candidate)
                state = 'ACCEPT' if score['score'] >= threshold else 'REJECT'
                if state == 'REJECT':
                    rejected += 1
                print(f"{idx + 1}. {candidate:<18} score={score['score']:>3} {state}")
            print(f"Rejected words: {rejected}/{count}")

        elif choice == 'List templates':
            cmd_templates(args)

        elif choice == 'List saved languages':
            cmd_list_languages(args)

        elif choice == 'Exit':
            print('Bye.')
            break


def build_parser():
    parser = argparse.ArgumentParser(
        prog='conlang-studio',
        description='Conlang generator with templates, grammar, sound-change derivation, and evaluation.',
    )
    parser.add_argument('--storage-dir', default=DEFAULT_STORAGE_DIR, help='Directory for saved language packages.')

    subparsers = parser.add_subparsers(dest='command')

    templates_parser = subparsers.add_parser('templates', help='List available language templates.')
    templates_parser.add_argument('--storage-dir', default=DEFAULT_STORAGE_DIR, help='Directory for saved language packages.')
    templates_parser.set_defaults(func=cmd_templates)

    new_parser = subparsers.add_parser('new', help='Create a new language from a template.')
    new_parser.add_argument('--storage-dir', default=DEFAULT_STORAGE_DIR, help='Directory for saved language packages.')
    new_parser.add_argument('--name', required=True, help='Language name.')
    new_parser.add_argument('--template', default='balanced', help='Template preset (run templates command to list).')
    new_parser.add_argument('--output', help='Optional output path. Defaults to storage directory.')
    new_parser.add_argument('--no-bootstrap', action='store_true', help='Skip lexicon bootstrap on creation.')
    new_parser.set_defaults(func=cmd_new)

    translate_parser = subparsers.add_parser('translate', help='Translate English text into the conlang.')
    translate_parser.add_argument('--storage-dir', default=DEFAULT_STORAGE_DIR, help='Directory for saved language packages.')
    translate_parser.add_argument('--language', required=True, help='Language name or full path.')
    translate_parser.add_argument('--text', help='Text to translate. If omitted, prompts interactively.')
    translate_parser.add_argument('--use-grammar', action='store_true', help='Apply grammar engine reordering.')
    translate_parser.add_argument('--autosave', action='store_true', help='Save language package after translation.')
    translate_parser.set_defaults(func=cmd_translate)

    generate_parser = subparsers.add_parser('generate', help='Generate words, nouns, or names.')
    generate_parser.add_argument('--storage-dir', default=DEFAULT_STORAGE_DIR, help='Directory for saved language packages.')
    generate_parser.add_argument('--language', required=True, help='Language name or full path.')
    generate_parser.add_argument('--kind', default='word', choices=['word', 'noun', 'proper-noun', 'name'])
    generate_parser.add_argument('--count', type=int, default=10)
    generate_parser.add_argument('--category', default='person', choices=['person', 'place', 'thing'])
    generate_parser.add_argument('--gender', default=None, choices=['male', 'female', 'neutral', None])
    generate_parser.add_argument('--number', default='singular', choices=['singular', 'plural'])
    generate_parser.add_argument('--grammatical-case', default='core', choices=['core', 'accusative', 'genitive'])
    generate_parser.add_argument('--min-syllables', type=int, default=1)
    generate_parser.add_argument('--max-syllables', type=int, default=4)
    generate_parser.add_argument('--min-score', type=int, default=58)
    generate_parser.add_argument('--meaning-prefix', default='generated-')
    generate_parser.add_argument('--autosave', action='store_true', help='Save language package after generation.')
    generate_parser.set_defaults(func=cmd_generate)

    derive_parser = subparsers.add_parser('derive', help='Derive a daughter language using sound-change rules.')
    derive_parser.add_argument('--storage-dir', default=DEFAULT_STORAGE_DIR, help='Directory for saved language packages.')
    derive_parser.add_argument('--language', required=True, help='Language name or full path.')
    derive_parser.add_argument('--preset', default='lenition', choices=SoundChangeEngine.available_presets())
    derive_parser.add_argument('--name', help='Name for derived language package.')
    derive_parser.add_argument('--output', help='Optional output path.')
    derive_parser.set_defaults(func=cmd_derive)

    style_parser = subparsers.add_parser('style', help='Switch language style preset instantly.')
    style_parser.add_argument('--storage-dir', default=DEFAULT_STORAGE_DIR, help='Directory for saved language packages.')
    style_parser.add_argument('--language', required=True, help='Language name or full path.')
    style_parser.add_argument('--style', required=True, help='Template/style name (run templates command to list).')
    style_parser.add_argument('--output', help='Optional save path (defaults to same package).')
    style_parser.add_argument('--regenerate-lexicon', action='store_true', help='Rebuild lexicon under new style.')
    style_parser.add_argument('--no-bootstrap', action='store_true', help='Skip lexicon bootstrap after regeneration.')
    style_parser.set_defaults(func=cmd_style)

    evaluate_parser = subparsers.add_parser('evaluate', help='Evaluate pronounceability of generated outputs.')
    evaluate_parser.add_argument('--storage-dir', default=DEFAULT_STORAGE_DIR, help='Directory for saved language packages.')
    evaluate_parser.add_argument('--language', required=True, help='Language name or full path.')
    evaluate_parser.add_argument('--count', type=int, default=40)
    evaluate_parser.add_argument('--min-score', type=int, default=58)
    evaluate_parser.add_argument('--min-syllables', type=int, default=1)
    evaluate_parser.add_argument('--max-syllables', type=int, default=4)
    evaluate_parser.add_argument('--only-rejected', action='store_true')
    evaluate_parser.set_defaults(func=cmd_evaluate)

    list_parser = subparsers.add_parser('list', help='List stored language packages.')
    list_parser.add_argument('--storage-dir', default=DEFAULT_STORAGE_DIR, help='Directory for saved language packages.')
    list_parser.set_defaults(func=cmd_list_languages)

    interactive_parser = subparsers.add_parser('interactive', help='Run prompt-driven interactive CLI.')
    interactive_parser.add_argument('--storage-dir', default=DEFAULT_STORAGE_DIR, help='Directory for saved language packages.')
    interactive_parser.set_defaults(func=cmd_interactive)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, 'command', None):
        args.command = 'interactive'
        args.func = cmd_interactive

    try:
        args.func(args)
        return 0
    except KeyboardInterrupt:
        print('\nInterrupted by user.')
        return 130
    except Exception as error:
        print(f"Error: {error}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
