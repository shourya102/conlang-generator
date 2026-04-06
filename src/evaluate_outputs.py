import argparse
import os
import sys

if __package__ is None or __package__ == '':
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from src.language_generator.language import Language
from src.language_generator.storage import LanguageStorage


def resolve_language(storage_dir, language_ref):
    storage = LanguageStorage(storage_dir)
    path = storage.resolve_language_path(language_ref)
    if path is None:
        raise ValueError(f"Language '{language_ref}' not found in storage or as direct path.")

    language = Language.load(path)
    if language is None:
        raise ValueError(f"Failed to load language from '{path}'.")
    return language, path


def main():
    parser = argparse.ArgumentParser(description='Evaluate generated output pronounceability.')
    parser.add_argument('--storage-dir', default='src/languages')
    parser.add_argument('--language', required=True, help='Language name or full path.')
    parser.add_argument('--count', type=int, default=100)
    parser.add_argument('--min-score', type=int, default=58)
    parser.add_argument('--min-syllables', type=int, default=1)
    parser.add_argument('--max-syllables', type=int, default=4)
    parser.add_argument('--only-rejected', action='store_true')
    args = parser.parse_args()

    language, path = resolve_language(args.storage_dir, args.language)
    print(f"Loaded language: {path}")
    print(f"Sampling {args.count} generated words")

    accepted = 0
    rejected = 0

    for idx in range(args.count):
        candidate = language.phonology.generate_word(args.min_syllables, args.max_syllables)
        if not candidate:
            continue

        result = language.evaluator.score_word(candidate)
        accepted_flag = result['score'] >= args.min_score
        if accepted_flag:
            accepted += 1
        else:
            rejected += 1

        if args.only_rejected and accepted_flag:
            continue

        state = 'ACCEPT' if accepted_flag else 'REJECT'
        issues = ','.join(result['issues']) if result['issues'] else 'none'
        print(f"{idx + 1:>3}. {candidate:<20} score={result['score']:>3} {state} issues={issues}")

    total = accepted + rejected
    print('-' * 60)
    print(f"Accepted: {accepted}")
    print(f"Rejected: {rejected}")
    print(f"Acceptance rate: {(accepted / total * 100) if total else 0:.2f}%")


if __name__ == '__main__':
    main()
