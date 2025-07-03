from flask import Flask, request, jsonify, render_template
import csv
import datetime
import hashlib
import os
import requests
import json
import pokemon_cache_loader
import uuid
from flask import session, redirect, url_for

app = Flask(__name__)

def load_pokemon(csv_path):
    pokemon = []
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                generation = int(row['gen'])
            except ValueError:
                continue  # Skip rows where 'gen' is not an integer
            name = row['Pokemon'].strip().lower()
            # Normalize Nidoran names for file/image compatibility
            if name in ['nidoran♀', 'nidoran♀.', 'nidoran ♀', 'nidoran ♀.']:
                name = 'nidoranfemale'
            elif name in ['nidoran♂', 'nidoran♂.', 'nidoran ♂', 'nidoran ♂.']:
                name = 'nidoranmale'
            # Try to get weight and height if present in CSV
            try:
                weight = float(row.get('Weight', '') or 0)
            except Exception:
                weight = None
            try:
                height = float(row.get('Height', '') or 0)
            except Exception:
                height = None
            pokemon.append({
                'name': name,
                'generation': generation,
                'type1': row['Type I'].strip().lower(),
                'type2': row['Type II'].strip().lower() if row['Type II'] else row['Type I'].strip().lower(),
                'weight': weight,
                'height': height
            })
    return pokemon

CSV_FILE = os.path.join(os.path.dirname(__file__), 'Pokemon Data - National Pokedex.csv')
POKEMON_LIST = load_pokemon(CSV_FILE)

def roman_to_int(s):
    # Robust Roman numeral parser for gens up to IX
    roman_map = {'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6, 'vii': 7, 'viii': 8, 'ix': 9}
    s = s.lower()
    if s in roman_map:
        return roman_map[s]
    # fallback: single char
    roman_numerals = {'i': 1, 'v': 5, 'x': 10}
    total = 0
    prev = 0
    for c in reversed(s):
        val = roman_numerals.get(c, 0)
        if val < prev:
            total -= val
        else:
            total += val
            prev = val
    return total if total > 0 else None

# --- Supplement with special forms from PokéAPI if missing ---
SPECIAL_FORMS = [
    # Alolan forms (Gen 7)
    ("Rattata Alola", "rattata-alola"),
    ("Raticate Alola", "raticate-alola"),
    ("Raichu Alola", "raichu-alola"),
    ("Sandshrew Alola", "sandshrew-alola"),
    ("Sandslash Alola", "sandslash-alola"),
    ("Vulpix Alola", "vulpix-alola"),
    ("Ninetales Alola", "ninetales-alola"),
    ("Diglett Alola", "diglett-alola"),
    ("Dugtrio Alola", "dugtrio-alola"),
    ("Meowth Alola", "meowth-alola"),
    ("Persian Alola", "persian-alola"),
    ("Geodude Alola", "geodude-alola"),
    ("Graveler Alola", "graveler-alola"),
    ("Golem Alola", "golem-alola"),
    ("Grimer Alola", "grimer-alola"),
    ("Muk Alola", "muk-alola"),
    ("Exeggutor Alola", "exeggutor-alola"),
    ("Marowak Alola", "marowak-alola"),
    # Galarian forms (Gen 8)
    ("Meowth Galar", "meowth-galar"),
    ("Ponyta Galar", "ponyta-galar"),
    ("Rapidash Galar", "rapidash-galar"),
    ("Slowpoke Galar", "slowpoke-galar"),
    ("Slowbro Galar", "slowbro-galar"),
    ("Farfetch'd Galar", "farfetchd-galar"),
    ("Weezing Galar", "weezing-galar"),
    ("Mr. Mime Galar", "mr-mime-galar"),
    ("Corsola Galar", "corsola-galar"),
    ("Zigzagoon Galar", "zigzagoon-galar"),
    ("Linoone Galar", "linoone-galar"),
    ("Darumaka Galar", "darumaka-galar"),
    ("Darmanitan Galar Standard", "darmanitan-galar-standard"),
    ("Yamask Galar", "yamask-galar"),
    ("Stunfisk Galar", "stunfisk-galar"),
    ("Articuno Galar", "articuno-galar"),
    ("Zapdos Galar", "zapdos-galar"),
    ("Moltres Galar", "moltres-galar"),
    # Hisuian forms (Gen 8)
    ("Growlithe Hisui", "growlithe-hisui"),
    ("Arcanine Hisui", "arcanine-hisui"),
    ("Voltorb Hisui", "voltorb-hisui"),
    ("Electrode Hisui", "electrode-hisui"),
    ("Qwilfish Hisui", "qwilfish-hisui"),
    ("Sneasel Hisui", "sneasel-hisui"),
    ("Kleavor", "kleavor"),
    ("Braviary Hisui", "braviary-hisui"),
    ("Rufflet Hisui", "rufflet-hisui"),
    ("Zorua Hisui", "zorua-hisui"),
    ("Zoroark Hisui", "zoroark-hisui"),
    ("Basculegion", "basculegion"),
    ("Basculegion Female", "basculegion-female"),
    # Paldean forms (Gen 9)
    ("Tauros Paldea Combat", "tauros-paldea-combat-breed"),
    ("Tauros Paldea Blaze", "tauros-paldea-blaze-breed"),
    ("Tauros Paldea Aqua", "tauros-paldea-aqua-breed"),
    ("Wooper Paldea", "wooper-paldea"),
    # Lycanroc forms (Gen 7)
    ("Lycanroc Midday", "lycanroc-midday"),
    ("Lycanroc Midnight", "lycanroc-midnight"),
    ("Lycanroc Dusk", "lycanroc-dusk"),
    # Other forms
    ("Sneasler", "sneasler"),
    ("Overqwil", "overqwil"),
    # Ursaluna forms
    ("Ursaluna", "ursaluna"),
    # Removed Ursaluna Bloodmoon and Keldeo forms
]

SPECIAL_FORMS_CACHE = os.path.join(os.path.dirname(__file__), 'special_forms_cache.json')

def fetch_and_cache_special_forms():
    cache = []
    for display, api_name in SPECIAL_FORMS:
        norm_name = api_name.replace('-', ' ')
        url = f"https://pokeapi.co/api/v2/pokemon/{api_name}"
        resp = requests.get(url)
        if resp.status_code == 200:
            poke = resp.json()
            types = [t['type']['name'] for t in poke['types']]
            weight = poke['weight']
            height = poke['height']
            species_url = poke['species']['url']
            gen = None
            try:
                species_resp = requests.get(species_url)
                if species_resp.status_code == 200:
                    species_data = species_resp.json()
                    gen_name = species_data['generation']['name']
                    if gen_name.startswith('generation-'):
                        roman = gen_name.split('-')[-1]
                        gen = roman_to_int(roman)
                    # Force Paldean forms to Gen 9 (handle both 'paldea' and 'paldean')
                    if 'paldea' in api_name or 'paldean' in api_name:
                        gen = 9
                    if gen == 1:
                        if 'alola' in api_name:
                            gen = 7
                        elif 'galar' in api_name or 'hisui' in api_name:
                            gen = 8
                        elif 'paldea' in api_name or 'paldean' in api_name:
                            gen = 9
            except Exception:
                pass
            type1 = types[0] if len(types) > 0 else ''
            type2 = types[1] if len(types) > 1 else ''
            cache.append({
                'name': norm_name,
                'generation': gen,
                'type1': type1,
                'type2': type2,
                'types': types,
                'weight': weight,
                'height': height,
                'display': display
            })
    with open(SPECIAL_FORMS_CACHE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

# Only fetch and cache if cache file does not exist or is empty
if not os.path.exists(SPECIAL_FORMS_CACHE) or os.stat(SPECIAL_FORMS_CACHE).st_size == 0:
    fetch_and_cache_special_forms()

# Load special forms from cache
with open(SPECIAL_FORMS_CACHE, 'r', encoding='utf-8') as f:
    special_forms_data = json.load(f)

def canonical_name(name):
    n = name.replace('-', ' ').replace('_', ' ').replace('.', '').replace("'", '').lower().strip()
    # Handle regional forms (prefix or suffix)
    region_map = {
        'hisuian': 'hisui',
        'galarian': 'galar',
        'alolan': 'alola',
        'paldean': 'paldea',
    }
    for region_prefix, region_suffix in region_map.items():
        if n.startswith(region_prefix + ' '):
            # e.g. 'hisuian zoroark' -> 'zoroark hisui'
            n = n[len(region_prefix):].strip() + ' ' + region_suffix
        elif n.endswith(' ' + region_suffix):
            # already in correct form
            pass
    n = n.replace(' ', '')
    return n

existing_names = set()
for p in POKEMON_LIST:
    p['canonical'] = canonical_name(p['name'])
    existing_names.add(p['canonical'])
for entry in special_forms_data:
    entry['canonical'] = canonical_name(entry['name'])
    if entry['canonical'] not in existing_names:
        POKEMON_LIST.append(entry)
        existing_names.add(entry['canonical'])

def get_pokemon_of_the_day(user_timezone_offset):
    now_utc = datetime.datetime.utcnow()
    user_midnight = now_utc + datetime.timedelta(hours=user_timezone_offset)
    user_midnight = user_midnight.replace(hour=0, minute=0, second=0, microsecond=0)
    seed_str = user_midnight.strftime('%Y-%m-%d')
    seed = int(hashlib.sha256(seed_str.encode()).hexdigest(), 16)
    idx = seed % len(POKEMON_LIST)
    return POKEMON_LIST[idx]

def get_pokemon_api_data(name, form=None):
    """Fetch weight and height from PokéAPI. Handles regional forms if form is provided."""
    # Handle Nidoran special cases for PokéAPI
    if name == 'nidoranfemale':
        api_name = 'nidoran-f'
    elif name == 'nidoranmale':
        api_name = 'nidoran-m'
    elif name == 'shaymin':
        api_name = 'shaymin-land'  # PokéAPI expects 'shaymin-land' for base form
    else:
        # Normalize: replace spaces with dashes, remove dots/apostrophes, lowercase
        api_name = name.replace(' ', '-').replace('.', '').replace("'", "").lower()
    if form:
        api_name = f"{api_name}-{form}"
    url = f"https://pokeapi.co/api/v2/pokemon/{api_name}"
    print('Fetching URL:', url)
    print(f'Calling PokéAPI for: {api_name}')
    resp = requests.get(url)
    print(f'PokéAPI status for {api_name}:', resp.status_code)
    if resp.status_code == 200:
        data = resp.json()
        print(f'PokéAPI data for {api_name}:', {'weight': data['weight'], 'height': data['height']})
        return {
            'weight': data['weight'],
            'height': data['height']
        }
    print('API 404 for:', url)
    return None

# In-memory mapping for demo; for production, use a persistent store
CUSTOM_GAME_FILE = os.path.join(os.path.dirname(__file__), 'custom_games.json')
if os.path.exists(CUSTOM_GAME_FILE):
    with open(CUSTOM_GAME_FILE, 'r') as f:
        custom_games = json.load(f)
else:
    custom_games = {}

def save_custom_games():
    with open(CUSTOM_GAME_FILE, 'w') as f:
        json.dump(custom_games, f)

@app.route('/custom_game', methods=['POST'])
def create_custom_game():
    data = request.json
    pokemon_name = data.get('pokemon')
    if not pokemon_name:
        return jsonify({'error': 'Missing Pokémon name'}), 400
    # Find canonical name
    norm = canonical_name(pokemon_name)
    matches = [p for p in POKEMON_LIST if p.get('canonical', canonical_name(p['name'])) == norm]
    if not matches:
        return jsonify({'error': 'Pokémon not found'}), 404
    # Generate unique code
    code = uuid.uuid4().hex[:12]
    custom_games[code] = norm
    save_custom_games()
    # Return the secret link
    link = url_for('home', game=code, _external=True)
    return jsonify({'link': link, 'code': code})

# Helper to get custom game Pokémon if code is present and valid

def get_custom_game_pokemon():
    # Accept game code from either query string or POST body
    code = request.args.get('game')
    if not code and request.is_json:
        code = request.json.get('game')
    if code and code in custom_games:
        norm = custom_games[code]
        matches = [p for p in POKEMON_LIST if p.get('canonical', canonical_name(p['name'])) == norm]
        if matches:
            return max(matches, key=lambda p: p.get('generation', 0))
    return None

@app.route('/')
def home():
    # Handle custom game creation via ?custom=NAME
    custom_name = request.args.get('custom')
    if custom_name:
        # Call the create_custom_game logic directly (not via HTTP)
        norm = canonical_name(custom_name)
        matches = [p for p in POKEMON_LIST if p.get('canonical', canonical_name(p['name'])) == norm]
        if not matches:
            # Optionally, you could show an error page here
            return redirect(url_for('home'))
        # Generate unique code
        code = uuid.uuid4().hex[:12]
        custom_games[code] = norm
        save_custom_games()
        # Redirect to the secret game link
        return redirect(url_for('home', game=code))
    # Optionally, you can pass the custom game info to the template if needed
    return render_template('home.html')

@app.route('/check_guess', methods=['POST'])
def check_guess():
    data = request.json
    guess_name = data.get('guess')
    timezone_offset = data.get('timezone_offset', 0)
    def normalize(name):
        n = name.replace('-', '').replace(' ', '').replace('_', '').replace('.', '').replace("'", '').lower()
        # Special cases for defaulting to canonical/gendered/standard forms
        if n == 'maushold':
            return 'mausholdfamilyofthree'
        if n == 'indeedee':
            return 'indeedeemale'
        if n == 'meowstic':
            return 'meowsticmale'
        if n == 'frillish':
            return 'frillishmale'
        if n == 'jellicent':
            return 'jellicentmale'
        if n == 'pyroar':
            return 'pyroarmale'
        if n == 'unfezant':
            return 'unfezantmale'
        if n == 'hippopotas':
            return 'hippopotasfemale'  # Hippopotas default is female (matches sprite convention)
        if n == 'hippowdon':
            return 'hippowdonfemale'
        if n == 'basculin':
            return 'basculinredstriped'
        if n == 'basculegion':
            return 'basculegionmale'
        if n == 'oricorio':
            return 'oricoriobaile'
        if n == 'lycanroc':
            return 'lycanrocmidday'
        if n == 'toxtricity':
            return 'toxtricityamped'
        if n in ['flabébé', 'flabebe']:
            return 'flabebe'
        return n
    norm_guess = canonical_name(guess_name)
    # Use canonical for all matching in check_guess
    matches = [p for p in POKEMON_LIST if p.get('canonical', canonical_name(p['name'])) == norm_guess]
    guess = max(matches, key=lambda p: p.get('generation', 0)) if matches else None
    # Use custom game Pokémon if present
    custom_pokemon = get_custom_game_pokemon()
    if custom_pokemon:
        target = custom_pokemon
    else:
        target = get_pokemon_of_the_day(timezone_offset)
    if not guess:
        return jsonify({'error': 'Pokemon not found.'}), 404

    def get_weight_height(p):
            # Helper function to normalize names for cache lookup
            def normalize(name):
                n = name.replace('-', '').replace(' ', '').replace('_', '').replace('.', '').replace("'", '').lower()
                # Special cases for defaulting to canonical/gendered/standard forms
                if n == 'maushold':
                    return 'mausholdfamilyofthree'
                if n == 'indeedee':
                    return 'indeedeemale'
                if n == 'meowstic':
                    return 'meowsticmale'
                if n == 'frillish':
                    return 'frillishmale'
                if n == 'jellicent':
                    return 'jellicentmale'
                if n == 'pyroar':
                    return 'pyroarmale'
                if n == 'unfezant':
                    return 'unfezantmale'
                if n == 'hippopotas':
                    return 'hippopotasfemale'  # Hippopotas default is female (matches sprite convention)
                if n == 'hippowdon':
                    return 'hippowdonfemale'
                if n == 'basculin':
                    return 'basculinredstriped'
                if n == 'basculegion':
                    return 'basculegionmale'
                if n == 'oricorio':
                    return 'oricoriobaile'
                if n == 'lycanroc':
                    return 'lycanrocmidday'
                if n == 'toxtricity':
                    return 'toxtricityamped'
                if n in ['flabébé', 'flabebe']:
                    return 'flabebe'
                if n.startswith('keldeo'):
                    return 'keldeoordinary'  # Always use ordinary form for any Keldeo guess
                return n
            print(f"[DEBUG] Looking up weight/height for: {p['name']}")
            # 1. Try cache
            norm_name = normalize(p['name'])
            # Special handling for Keldeo: always use 'keldeo' for cache/API
            if norm_name == 'keldeo':
                cache_entry = pokemon_cache_loader.find_pokemon_cache_entry('keldeo')
            else:
                cache_entry = pokemon_cache_loader.find_pokemon_cache_entry(norm_name)
            if cache_entry:
                print(f"[DEBUG] Found in cache for '{norm_name}': weight={cache_entry.get('weight')}, height={cache_entry.get('height')}")
            # Variant lookups for special cases
            special_cases = {
                'mausholdfamilyofthree': [
                    'maushold family of three', 'maushold familyofthree', 'maushold family-of-three', 'maushold-family-of-three', 'Maushold Family Of Three'
                ],
                'indeedeemale': [
                    'indeedee male', 'indeedeemale', 'indeedee-male', 'indeedee_male', 'Indeedee Male', 'INDEEDEE MALE'
                ],
                'indeedeefemale': [
                    'indeedee female', 'indeedeefemale', 'indeedee-female', 'indeedee_female', 'Indeedee Female', 'INDEEDEE FEMALE'
                ],
                'meowsticmale': [
                    'meowstic male', 'meowsticmale', 'meowstic-male', 'meowstic_male', 'Meowstic Male', 'MEOWSTIC MALE'
                ],
                'meowsticfemale': [
                    'meowstic female', 'meowsticfemale', 'meowstic-female', 'meowstic_female', 'Meowstic Female', 'MEOWSTIC FEMALE'
                ],
                'frillishmale': [
                    'frillish male', 'frillishmale', 'frillish-male', 'frillish_male', 'Frillish Male', 'FRILLISH MALE'
                ],
                'frillishfemale': [
                    'frillish female', 'frillishfemale', 'frillish-female', 'frillish_female', 'Frillish Female', 'FRILLISH FEMALE'
                ],
                'jellicentmale': [
                    'jellicent male', 'jellicentmale', 'jellicent-male', 'jellicent_male', 'Jellicent Male', 'JELLICENT MALE'
                ],
                'jellicentfemale': [
                    'jellicent female', 'jellicentfemale', 'jellicent-female', 'jellicent_female', 'Jellicent Female', 'JELLICENT FEMALE'
                ],
                'pyroarmale': [
                    'pyroar male', 'pyroarmale', 'pyroar-male', 'pyroar_male', 'Pyroar Male', 'PYROAR MALE'
                ],
                'pyroarfemale': [
                    'pyroar female', 'pyroarfemale', 'pyroar-female', 'pyroar_female', 'Pyroar Female', 'PYROAR FEMALE'
                ],
                'unfezantmale': [
                    'unfezant male', 'unfezantmale', 'unfezant-male', 'unfezant_male', 'Unfezant Male', 'UNFEZANT MALE'
                ],
                'unfezantfemale': [
                    'unfezant female', 'unfezantfemale', 'unfezant-female', 'unfezant_female', 'Unfezant Female', 'UNFEZANT FEMALE'
                ],
                'hippopotasfemale': [
                    'hippopotas female', 'hippopotasfemale', 'hippopotas-female', 'hippopotas_female', 'Hippopotas Female', 'HIPPOPOTAS FEMALE'
                ],
                'hippowdonfemale': [
                    'hippowdon female', 'hippowdonfemale', 'hippowdon-female', 'hippowdon_female', 'Hippowdon Female', 'HIPPOWDON FEMALE'
                ],
                'basculinredstriped': [
                    'basculin red striped', 'basculinredstriped', 'basculin-red-striped', 'basculin_red_striped', 'Basculin Red Striped', 'BASCULIN RED STRIPED'
                ],
                'basculegionmale': [
                    'basculegion male', 'basculegionmale', 'basculegion-male', 'basculegion_male', 'Basculegion Male', 'BASCULEGION MALE'
                ],
                'basculegionfemale': [
                    'basculegion female', 'basculegionfemale', 'basculegion-female', 'basculegion_female', 'Basculegion Female', 'BASCULEGION FEMALE'
                ],
                'oricoriobaile': [
                    'oricorio baile', 'oricoriobaile', 'oricorio-baile', 'oricorio_baile', 'Oricorio Baile', 'ORICORIO BAILE'
                ],
                'lycanrocmidday': [
                    'lycanroc midday', 'lycanrocmidday', 'lycanroc-midday', 'lycanroc_midday', 'Lycanroc Midday', 'LYCANROC MIDDAY'
                ],
                'lycanrocmidnight': [
                    'lycanroc midnight', 'lycanrocmidnight', 'lycanroc-midnight', 'lycanroc_midnight', 'Lycanroc Midnight', 'LYCANROC MIDNIGHT'
                ],
                'lycanrocdusk': [
                    'lycanroc dusk', 'lycanrocdusk', 'lycanroc-dusk', 'lycanroc_dusk', 'Lycanroc Dusk', 'LYCANROC DUSK'
                ],
                'toxtricityamped': [
                    'toxtricity amped', 'toxtricityamped', 'toxtricity-amped', 'toxtricity_amped', 'Toxtricity Amped', 'TOXTRICITY AMPED'
                ],
                'toxtricitylowkey': [
                    'toxtricity low key', 'toxtricitylowkey', 'toxtricity-low-key', 'toxtricity_low_key', 'Toxtricity Low Key', 'TOXTRICITY LOW KEY'
                ]
            }
            if not cache_entry and norm_name in special_cases:
                for v in special_cases[norm_name]:
                    cache_entry = pokemon_cache_loader.find_pokemon_cache_entry(v)
                    if cache_entry:
                        print(f"[DEBUG] Found in cache for special case '{v}': weight={cache_entry.get('weight')}, height={cache_entry.get('height')}")
                        break
            if cache_entry and 'weight' in cache_entry and 'height' in cache_entry:
                if cache_entry['weight'] not in (None, 0, '') and cache_entry['height'] not in (None, 0, ''):
                    # Convert to kg/m if needed (PokéAPI and cache are in decagrams/dm)
                    return {
                        'weight': cache_entry['weight'] / 10.0,
                        'height': cache_entry['height'] / 10.0
                    }
                else:
                    print(f"[DEBUG] Cache entry found but weight/height missing or zero for '{norm_name}'")
            # 2. Try PokéAPI as fallback
            try:
                # Special handling for Keldeo: always use 'keldeo' for API
                api_name = p['name']
                if norm_name == 'keldeo':
                    api_name = 'keldeo'
                api = get_pokemon_api_data(api_name, p.get('form'))
                if api and api['weight'] not in (None, 0, '') and api['height'] not in (None, 0, ''):
                    print(f"[DEBUG] Found in PokéAPI: weight={api['weight']}, height={api['height']}")
                    return {
                        'weight': api['weight'] / 10.0,
                        'height': api['height'] / 10.0
                    }
                else:
                    print(f"[DEBUG] PokéAPI call failed or returned missing/zero for '{p['name']}'")
            except Exception as e:
                print(f"[DEBUG] PokéAPI exception for '{p['name']}': {e}")
            print(f"[DEBUG] All sources failed for '{p['name']}' - returning None")
            return {'weight': None, 'height': None}

    guess_stats = get_weight_height(guess)
    target_stats = get_weight_height(target)
    print(f"[DEBUG] Target Pokémon raw: {target}")
    print(f"[DEBUG] Target Pokémon name: {target.get('name')}")
    print(f"[DEBUG] Target Pokémon normalized: {normalize(target.get('name'))}")
    target_stats = get_weight_height(target)
    print(f"[DEBUG] target_stats after get_weight_height: {target_stats}")
    heavier = lighter = None
    weight = height = target_weight = target_height = None
    if guess_stats['weight'] is not None and target_stats['weight'] is not None:
        heavier = guess_stats['weight'] > target_stats['weight']
        lighter = guess_stats['weight'] < target_stats['weight']
    weight = guess_stats['weight']
    height = guess_stats['height']
    target_weight = target_stats['weight']
    target_height = target_stats['height']

    # Always return 'flabebe' (no accent) as the canonical name for API responses
    response_name = guess['name']
    # Special case: show 'Basculegion' for basculegionfemale
    if normalize(guess['name']) == 'flabebe':
        response_name = 'flabebe'
    elif normalize(guess['name']) == 'basculegionfemale':
        response_name = 'Basculegion'
    result = {
        'name': response_name,
        'generation': guess.get('generation') == target.get('generation'),
        'generation_number': guess.get('generation'),
        'target_generation_number': target.get('generation'),
        'type1': guess.get('type1') == target.get('type1'),
        'type2': guess.get('type2') == target.get('type2'),
        'type1_name': guess.get('type1'),
        'type2_name': guess.get('type2') if guess.get('type2') != guess.get('type1') else '',
        'heavier': heavier,
        'lighter': lighter,
        'weight': weight,
        'height': height,
        'target_weight': target_weight,
        'target_height': target_height,
        # Add target Pokémon details for frontend modal
        'target_name': target.get('name'),
        'target_type1': target.get('type1'),
        'target_type2': target.get('type2'),
        'target_generation': target.get('generation')
    }
    print('DEBUG: guess_stats', guess_stats)
    print('DEBUG: target_stats', target_stats)
    print('DEBUG: result', result)
    return jsonify(result)

@app.route('/pokemon_of_the_day', methods=['GET'])
def pokemon_of_the_day():
    # Check for custom game code
    code = request.args.get('game')
    if code and code in custom_games:
        norm = custom_games[code]
        matches = [p for p in POKEMON_LIST if p.get('canonical', canonical_name(p['name'])) == norm]
        if matches:
            target = max(matches, key=lambda p: p.get('generation', 0))
            return jsonify({'name': target['name']})
    timezone_offset = int(request.args.get('timezone_offset', 0))
    target = get_pokemon_of_the_day(timezone_offset)
    return jsonify({'name': target['name']})

@app.route('/pokemon_names', methods=['GET'])
def pokemon_names():
    def display_name(name):
        # Normalize for display
        n = name.replace('-', ' ').replace('_', ' ').replace('.', '').replace("'", '').lower()
        if n == 'nidoranmale':
            return 'Nidoran♂'
        if n == 'nidoranfemale':
            return 'Nidoran♀'
        if n == 'darmanitan galar standard':
            return 'Galarian Darmanitan'
        # Paldean Tauros forms
        if n in ['tauros paldea combat breed', 'tauros paldea combat']:
            return 'Paldean Tauros Combat'
        if n in ['tauros paldea blaze breed', 'tauros paldea blaze']:
            return 'Paldean Tauros Blaze'
        if n in ['tauros paldea aqua breed', 'tauros paldea aqua']:
            return 'Paldean Tauros Aqua'
        if n == 'wooper paldea':
            return 'Paldean Wooper'
        # Toxtricity forms
        if n in ['toxtricityamped', 'toxtricity amped', 'toxtricity-amped', 'toxtricity_amped']:
            return 'Toxtricity (Amped)'
        if n in ['toxtricitylowkey', 'toxtricity low key', 'toxtricity-low-key', 'toxtricity_low_key']:
            return 'Toxtricity (Low Key)'
        # Basculegion forms
        if n == 'basculegionmale':
            return 'Basculegion'
        if n == 'basculegionfemale':
            return 'Basculegion'
        # Hisuian forms
        if n.endswith(' hisui'):
            base = n[:-6]
            return f'Hisuian {base.title()}'
        # Galarian forms
        if n.endswith(' galar'):
            base = n[:-6]
            return f'Galarian {base.title()}'
        # Alolan forms
        if n.endswith(' alola'):
            base = n[:-6]
            return f'Alolan {base.title()}'
        # Paldean forms
        if n.endswith(' paldea'):
            base = n[:-7]
            return f'Paldean {base.title()}'
        # Lycanroc forms
        if n.startswith('lycanroc '):
            parts = n.split()
            if len(parts) == 2:
                return 'Lycanroc ' + parts[1].capitalize()
            else:
                return 'Lycanroc'
        if n in ['flabébé', 'flabebe']:
            return 'Flabebe'
        # Default: capitalize each word
        return ' '.join([w.capitalize() for w in n.split()])
    def canonical_name(name):
        n = name.replace('-', ' ').replace('_', ' ').replace('.', '').replace("'", '').lower().strip()
        # Handle regional forms (prefix or suffix)
        region_map = {
            'hisuian': 'hisui',
            'galarian': 'galar',
            'alolan': 'alola',
            'paldean': 'paldea',
        }
        for region_prefix, region_suffix in region_map.items():
            if n.startswith(region_prefix + ' '):
                n = n[len(region_prefix):].strip() + ' ' + region_suffix
            elif n.endswith(' ' + region_suffix):
                pass
        n = n.replace(' ', '')
        return n
    names = []
    seen = set()
    all_pokemon = list(POKEMON_LIST)
    for p in all_pokemon:
        norm = p.get('canonical', canonical_name(p['name']))
        if norm in seen:
            continue
        seen.add(norm)
        names.append({
            'display': display_name(p['name']),
            'value': norm
        })
    # Add aliases for regional forms and special forms
    region_map = {
        'hisui': 'hisuian',
        'galar': 'galarian',
        'alola': 'alolan',
        'paldea': 'paldean',
    }
    for p in all_pokemon:
        n = p['name'].replace('-', ' ').replace('_', ' ').replace('.', '').replace("'", '').lower().strip()
        canon = p.get('canonical', canonical_name(p['name']))
        # If canonical ends with a regional suffix, generate all aliases
        for region_suffix, region_prefix in region_map.items():
            if canon.endswith(region_suffix):
                # base name (without region)
                base = n
                if n.endswith(' ' + region_suffix):
                    base = n[:-(len(region_suffix)+1)]
                elif n.endswith(region_suffix):
                    base = n[:-len(region_suffix)]
                base = base.strip()
                # Aliases: prefix, suffix, joined, dashed, etc.
                alias_variants = [
                    f"{region_prefix} {base}",
                    f"{base} {region_suffix}",
                    f"{base}-{region_suffix}",
                    f"{base}{region_suffix}",
                    f"{region_prefix} {base.title()}",
                    f"{base.title()} {region_suffix}",
                    f"{base.title()}-{region_suffix}",
                    f"{base.title()}{region_suffix}",
                ]
                for alias in alias_variants:
                    alias_norm = canonical_name(alias)
                    if alias_norm and alias_norm not in seen:
                        names.append({
                            'display': display_name(alias),
                            'value': canon
                        })
                        seen.add(alias_norm)
    return jsonify({'names': names})

if __name__ == '__main__':
    app.run(debug=True, port=5002)

# To run: flask run
