import requests
import json

# Fetch all Pokémon species (for names, forms, and generations)
species_url = 'https://pokeapi.co/api/v2/pokemon-species?limit=10000'
species_resp = requests.get(species_url)
species_data = species_resp.json()['results']

pokemon_list = []

for species in species_data:
    species_detail = requests.get(species['url']).json()
    # Get generation (as a number)
    gen_str = species_detail['generation']['name']  # e.g. 'generation-i'
    generation = int(gen_str.split('-')[-1].replace('i','1').replace('v','5').replace('x','10')) if gen_str.startswith('generation-') else None
    # Get all varieties (forms)
    for variety in species_detail['varieties']:
        poke_url = variety['pokemon']['url']
        poke_detail = requests.get(poke_url).json()
        name = poke_detail['name']
        # Types
        types = [t['type']['name'] for t in poke_detail['types']]
        type1 = types[0] if len(types) > 0 else None
        type2 = types[1] if len(types) > 1 else type1
        # Weight and height
        weight = poke_detail.get('weight')
        height = poke_detail.get('height')
        # Use display name (species name or form name)
        display_name = poke_detail['name'].replace('-', ' ').title()
        pokemon_list.append({
            'name': display_name,
            'api_name': poke_detail['name'],
            'generation': generation,
            'type1': type1,
            'type2': type2,
            'weight': weight,
            'height': height
        })

with open('pokemon_data.json', 'w', encoding='utf-8') as f:
    json.dump(pokemon_list, f, ensure_ascii=False, indent=2)

print(f"Saved {len(pokemon_list)} Pokémon entries to pokemon_data.json")
