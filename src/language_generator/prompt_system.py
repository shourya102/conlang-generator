def ask_text(prompt, default=None, allow_empty=False):
    while True:
        suffix = f" [{default}]" if default is not None else ''
        value = input(f"{prompt}{suffix}: ").strip()
        if not value and default is not None:
            return default
        if value or allow_empty:
            return value
        print('Please enter a value.')


def ask_int(prompt, default=None, minimum=None, maximum=None):
    while True:
        raw = ask_text(prompt, default=str(default) if default is not None else None)
        try:
            value = int(raw)
        except ValueError:
            print('Please enter an integer value.')
            continue

        if minimum is not None and value < minimum:
            print(f'Value must be >= {minimum}.')
            continue
        if maximum is not None and value > maximum:
            print(f'Value must be <= {maximum}.')
            continue
        return value


def ask_yes_no(prompt, default=True):
    default_hint = 'Y/n' if default else 'y/N'
    while True:
        raw = input(f"{prompt} [{default_hint}]: ").strip().lower()
        if not raw:
            return default
        if raw in {'y', 'yes'}:
            return True
        if raw in {'n', 'no'}:
            return False
        print('Please answer yes or no.')


def ask_choice(prompt, options, default_index=0):
    if not options:
        raise ValueError('ask_choice requires at least one option.')

    print(prompt)
    for idx, option in enumerate(options, start=1):
        marker = ' (default)' if idx - 1 == default_index else ''
        print(f"  {idx}. {option}{marker}")

    while True:
        raw = input('Select option number: ').strip()
        if not raw:
            return options[default_index]
        if raw.isdigit():
            numeric = int(raw)
            if 1 <= numeric <= len(options):
                return options[numeric - 1]
        print('Please enter a valid option number.')
