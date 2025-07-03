import os
import requests

# List of (display, api_name) as in your SPECIAL_FORMS in pokemon.py
SPECIAL_FORMS = [
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
    ("Growlithe Hisui", "growlithe-hisui"),
    ("Arcanine Hisui", "arcanine-hisui"),
    ("Voltorb Hisui", "voltorb-hisui"),
    ("Electrode Hisui", "electrode-hisui"),
    ("Qwilfish Hisui", "qwilfish-hisui"),
    ("Sneasel Hisui", "sneasel-hisui"),
    ("Tauros Paldea Combat", "tauros-paldea-combat-breed"),
    ("Tauros Paldea Blaze", "tauros-paldea-blaze-breed"),
    ("Tauros Paldea Aqua", "tauros-paldea-aqua-breed"),
    ("Wooper Paldea", "wooper-paldea"),
]

SPRITE_DIR = os.path.join(os.path.dirname(__file__), "static", "pokemon")
os.makedirs(SPRITE_DIR, exist_ok=True)

for display, api_name in SPECIAL_FORMS:
    filename = f"{api_name.replace('-', ' ')}.png"
    filepath = os.path.join(SPRITE_DIR, filename)
    if os.path.exists(filepath):
        print(f"Exists: {filename}")
        continue
    # Try Showdown's gen9 sprite set first, fallback to gen8
    showdown_url = f"https://play.pokemonshowdown.com/sprites/gen9/regular/{api_name}.png"
    resp = requests.get(showdown_url)
    if resp.status_code != 200:
        showdown_url = f"https://play.pokemonshowdown.com/sprites/gen8/regular/{api_name}.png"
        resp = requests.get(showdown_url)
    if resp.status_code == 200:
        with open(filepath, "wb") as f:
            f.write(resp.content)
        print(f"Downloaded: {filename} (Showdown)")
        continue
    # Fallback: use PokéAPI official artwork
    pokeapi_url = f"https://pokeapi.co/api/v2/pokemon/{api_name}"
    pokeapi_resp = requests.get(pokeapi_url)
    if pokeapi_resp.status_code == 200:
        poke_data = pokeapi_resp.json()
        # Try official-artwork, then home, then front_default
        sprite_url = None
        try:
            sprite_url = poke_data['sprites']['other']['official-artwork']['front_default']
        except Exception:
            pass
        if not sprite_url:
            try:
                sprite_url = poke_data['sprites']['other']['home']['front_default']
            except Exception:
                pass
        if not sprite_url:
            sprite_url = poke_data['sprites']['front_default']
        if sprite_url:
            img_resp = requests.get(sprite_url)
            if img_resp.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(img_resp.content)
                print(f"Downloaded: {filename} (PokéAPI)")
                continue
    print(f"Failed to download: {filename}")

print("Done.")
