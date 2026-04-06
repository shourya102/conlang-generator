import datetime
import os
import re


class LanguageStorage:
    def __init__(self, storage_dir):
        self.storage_dir = os.path.abspath(storage_dir)
        os.makedirs(self.storage_dir, exist_ok=True)

    @staticmethod
    def slugify(value):
        lowered = (value or 'language').strip().lower()
        lowered = re.sub(r'[^a-z0-9]+', '-', lowered)
        lowered = lowered.strip('-')
        return lowered or 'language'

    def language_path(self, name):
        filename = f"{self.slugify(name)}.lang.json"
        return os.path.join(self.storage_dir, filename)

    def list_languages(self):
        items = []
        for name in sorted(os.listdir(self.storage_dir)):
            if name.endswith('.lang.json'):
                items.append(os.path.join(self.storage_dir, name))
        return items

    def save_language(self, language, name, template_name='balanced', style_preset='balanced', metadata=None):
        path = self.language_path(name)
        package_metadata = {
            'name': name,
            'template_name': template_name,
            'style_preset': style_preset,
            'saved_at': datetime.datetime.utcnow().isoformat() + 'Z',
        }
        if metadata:
            package_metadata.update(metadata)
        language.save(path, metadata=package_metadata)
        return path

    def resolve_language_path(self, name_or_path):
        if not name_or_path:
            return None
        if os.path.exists(name_or_path):
            return os.path.abspath(name_or_path)
        candidate = self.language_path(name_or_path)
        if os.path.exists(candidate):
            return candidate
        return None
