import pandas as pd

# Load CSV
df = pd.read_csv('/Users/rodrigoferreira/Pokemon Wordle/Pokemon Data - National Pokedex.csv')

def get_gen(nat):
    if 152 <= nat <= 251:
        return 2
    elif 252 <= nat <= 386:
        return 3
    elif 387 <= nat <= 494:
        return 4
    elif 495 <= nat <= 649:
        return 5
    elif 650 <= nat <= 721:
        return 6
    elif 722 <= nat <= 809:
        return 7
    elif 810 <= nat <= 898:
        return 8
    elif 899 <= nat <= 905:
        return 'other'
    elif 906 <= nat <= 1010:
        return 9
    else:
        return df.loc[df['Nat'] == nat, 'gen'].values[0]

df['gen'] = df['Nat'].apply(get_gen)

# Save back to CSV
df.to_csv('/Users/rodrigoferreira/Pokemon Wordle/Pokemon Data - National Pokedex.csv', index=False)