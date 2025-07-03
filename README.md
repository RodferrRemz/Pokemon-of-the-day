# Pokémon Wordle

A web-based guessing game inspired by Wordle, but for Pokémon fans! Each day, a new Pokémon is selected, and your goal is to guess which one it is using hints about its generation, types, weight, and height.

## Features
- **Daily Pokémon Challenge:** Guess the Pokémon of the day based on its attributes.
- **Custom Games:** Create secret, shareable custom game links for any Pokémon—challenge your friends!
- **Smart Hints:** After each guess, see color-coded hints for generation, types, weight, and height.
- **Autocomplete & Typo Correction:** Fast, user-friendly input with suggestions and typo handling.
- **Pokédex Integration:** See Pokédex entries and sprites for each Pokémon.
- **Modern UI:** Clean, mobile-friendly design with Pokémon-themed visuals.

## How to Play
1. Enter your guess for the Pokémon of the day.
2. After each guess, hints will show how close you are in generation, type, weight, and height.
3. Use the hints to narrow down your next guess.
4. Give up to reveal the answer and learn more about the Pokémon!
5. Create a custom game to challenge friends with a secret Pokémon.

## Custom Games
- Click "Create custom game" to generate a secret link for any Pokémon.
- Share the link—your friends will play a game with your chosen Pokémon as the answer.
- The Pokémon name is never revealed in the link.

## Tech Stack
- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript
- **Data:** National Pokédex CSV, PokéAPI for special forms and Pokédex entries

## Setup & Run
1. Install Python 3.8+ and pip.
2. Install dependencies:
   ```bash
   pip install flask requests
   ```
3. Run the app:
   ```bash
   python pokemon.py
   # or
   flask run
   ```
4. Open your browser to [http://localhost:5002](http://localhost:5002)

## Project Structure
- `pokemon.py` — Main Flask app
- `templates/home.html` — Main frontend page
- `static/pokemon/` — Pokémon sprite images
- `Pokemon Data - National Pokedex.csv` — Main Pokémon data
- `custom_games.json` — Stores custom game codes

## Credits
- Pokémon data and sprites © Nintendo, Game Freak, The Pokémon Company
- PokéAPI for additional data
- Inspired by [Wordle](https://www.nytimes.com/games/wordle/index.html)

## License
This project is for educational and fan use only. Not affiliated with or endorsed by Nintendo or The Pokémon Company.
