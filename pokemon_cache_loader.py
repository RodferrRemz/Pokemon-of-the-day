import json
import os

def load_pokemon_cache(json_path):
    with open(json_path, encoding='utf-8') as f:
        return json.load(f)

POKEMON_CACHE_FILE = os.path.join(os.path.dirname(__file__), 'pokemon_data.json')
POKEMON_CACHE = load_pokemon_cache(POKEMON_CACHE_FILE)

# Helper: get cache entry by normalized name (case-insensitive, ignore dashes/underscores)
def find_pokemon_cache_entry(name):
    # Normalize: lowercase, remove dashes, underscores, and spaces
    def normalize(s):
        return s.replace('-', '').replace('_', '').replace(' ', '').strip().lower()
    norm = normalize(name)
    for entry in POKEMON_CACHE:
        entry_norm = normalize(entry['name'])
        if norm == entry_norm:
            return entry
    return None
