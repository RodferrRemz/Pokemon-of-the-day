import os
import requests

# List of missing Hisuian forms (add more as needed)
MISSING_HISUIAN = [
    ("zorua hisui", "zorua-hisui"),
    ("zoroark hisui", "zoroark-hisui"),
]

SPRITE_DIR = os.path.join(os.path.dirname(__file__), "static", "pokemon")

# Use official PokéAPI sprite URLs (front_default is usually 96x96, but dream_world or official-artwork is higher quality)
def get_sprite_url(api_name):
    # Try official-artwork first, fallback to front_default
    base_url = f"https://pokeapi.co/api/v2/pokemon/{api_name}"
    resp = requests.get(base_url)
    if resp.status_code != 200:
        print(f"Failed to fetch API for {api_name}")
        return None
    data = resp.json()
    # Try official artwork
    art_url = data['sprites']['other']['official-artwork']['front_default']
    if art_url:
        return art_url
    # Fallback to dream_world
    dream_url = data['sprites']['other']['dream_world']['front_default']
    if dream_url:
        return dream_url
    # Fallback to front_default
    return data['sprites']['front_default']

def download_sprite(name, api_name):
    url = get_sprite_url(api_name)
    if not url:
        print(f"No sprite found for {name} ({api_name})")
        return
    out_path = os.path.join(SPRITE_DIR, f"{name}.png")
    print(f"Downloading {name} from {url}")
    resp = requests.get(url)
    if resp.status_code == 200:
        with open(out_path, "wb") as f:
            f.write(resp.content)
        print(f"Saved to {out_path}")
    else:
        print(f"Failed to download {url}")

if __name__ == "__main__":
    os.makedirs(SPRITE_DIR, exist_ok=True)
    for name, api_name in MISSING_HISUIAN:
        download_sprite(name, api_name)
