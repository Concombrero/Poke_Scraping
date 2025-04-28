"""Code to scrape Pokémon information from Pokepedia."""

import requests
import os
import csv

from bs4 import BeautifulSoup

POKEPEDIA= "https://pokepedia.fr/"

GENERTAIONS_URL = {
    1: "Liste_des_Pokémon_de_la_première_génération",
    2: "Liste_des_Pokémon_de_la_deuxième_génération",
    3: "Liste_des_Pokémon_de_la_troisième_génération",
    4: "Liste_des_Pokémon_de_la_quatrième_génération",
    5: "Liste_des_Pokémon_de_la_cinquième_génération",
    6: "Liste_des_Pokémon_de_la_sixième_génération",
    7: "Liste_des_Pokémon_de_la_septième_génération",
    8: "Liste_des_Pokémon_de_la_huitième_génération",
    9: "Liste_des_Pokémon_de_la_neuvième_génération"
}

OUTPUT_DIR = "output"

def get_html_pokemon(pokemon_name: str):
    """
    Fetches the HTML content of a Pokepedia page for a given Pokémon name.
    Args:
        pokemon_name (str): The name of the Pokémon.
    Returns:
        str: The HTML content of the page.
    """
    url = f"{POKEPEDIA}{pokemon_name}"
    response = requests.get(url, timeout=300)
    if response.status_code == 200:
        return response.text
    elif response.status_code == 404:
        raise ValueError(f"The page for Pokémon '{pokemon_name}' does not exist (404 Not Found).")
    else:
        raise Exception(f"Failed to fetch page for {pokemon_name}.  Status code: {response.status_code}")


def parse_html(html: str):
    """
    Parses the HTML content to extract Pokémon information.
    Args:
        html (str): The HTML content of the page.
    Returns:
        dict: A dictionary containing Pokémon information.
    """
    soup = BeautifulSoup(html, 'html.parser')

    # Extract Pokémon name
    name = soup.find('h1').text.strip()

    # Extract Pokémon types
    types_section = soup.find('th', string=lambda text: text in ['Types', 'Type'])
    if types_section:
        types_section = types_section.find_next('td')
        types = [a['title'].replace(" (type)", "") for a in types_section.find_all('a') if 'title' in a.attrs]
        types = "-".join(types)

    # Extract Pokémon height and weight
    height = soup.find('th', string='Taille').find_next('td').text.strip()
    weight = soup.find('th', string='Poids').find_next('td').text.strip()


    # Locate the "Statistiques" section
    stats_section = soup.find('span', id="Statistiques")
    stats = {}
    if stats_section:
        # Find the table immediately following the "Statistiques" section
        stats_table = stats_section.find_next('table', class_='tableaustandard')
        if stats_table:
            rows = stats_table.find_all('tr')
            for row in rows:
                # Find the stat name in the first column
                stat_name_cell = row.find('a', title="Statistique")
                if stat_name_cell:
                    stat_name = stat_name_cell.text.strip()
                    # Get the base stat value from the second column
                    columns = row.find_all('td')
                    if len(columns) >= 2:
                        stat_value = int(columns[1].text.strip())
                        stats[stat_name] = stat_value

    return {
        'name': name,
        'types': types,
        'height': height,
        'weight': weight,
        'stats': stats
    }

def get_pokemons_from_generation(generation: int):
    """
    Fetches Pokémon names from a specific generation.
    Args:
        generation (int): The generation number (1 to 9).
    Returns:
        list: A list of Pokémon names with the first letter capitalized.
    """
    # Construct the URL for the generation
    if generation not in GENERTAIONS_URL:
        raise ValueError(f"Invalid generation number: {generation}. Must be between 1 and 9.")

    url = f"{POKEPEDIA}{GENERTAIONS_URL[generation]}"
    response = requests.get(url, timeout=300)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Locate the table containing Pokémon names
        table = soup.find('table', class_='tableaustandard')
        if not table:
            raise Exception("Failed to locate the Pokémon table on the page.")

        # Extract rows from the table
        rows = table.find_all('tr')
        pokemon_list = []

        for row in rows:
            # Get all columns (cells) in the row
            columns = row.find_all('td')
            if len(columns) >= 3:  # Ensure the row has at least 3 columns
                # Extract the name from the 3rd column
                name = columns[2].find('a', title=True)
                if name:
                    pokemon_list.append(name['title'].strip())

        # Ensure the first letter of each name is capitalized
        pokemon_list = [name.capitalize() for name in pokemon_list]

        return pokemon_list
    else:
        raise Exception(f"Failed to fetch Pokémon from generation {generation}. Status code: {response.status_code}")

def create_database(generation: int):
    """
    Creates a CSV database of Pokémon information with an additional 'devis' column
    based on the average of their stats.
    """
    
    all_pokemons = get_pokemons_from_generation(generation)

    file = os.path.join(OUTPUT_DIR, f"pokemon_GEN{generation}.csv")
    with open(file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['name', 'types', 'height', 'weight', 'stats', 'devis']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for pokemon in all_pokemons:
            try:
                html = get_html_pokemon(pokemon)
                print(f"Fetching data for Pokémon: {pokemon}")
                
                
                pokemon_info = parse_html(html)
                print(f"Parsed data for Pokémon: {pokemon_info['name']}")

                # Calculate the average of stats
                stats = pokemon_info['stats']
                if stats:
                    average_stats = sum(stats.values()) / len(stats)
                else:
                    average_stats = 0

                # Determine the Pokéball type based on the average stats
                if average_stats <= 50:
                    devis = 'Pokéball'
                elif 50 < average_stats <= 100:
                    devis = 'Superball'
                elif 100 < average_stats <= 150:
                    devis = 'Hyperball'
                else:
                    devis = 'Masterball'

                # Add the 'devis' field to the Pokémon info
                pokemon_info['devis'] = devis

                writer.writerow(pokemon_info)
            except Exception as e:
                print(f"Error writing Pokémon {pokemon}: {e}")


def get_pokemon():
    """
    Get Pokémon information from user input. 
    """
    pokemon = input("Enter the name of the Pokémon (ex: Bulbizarre): ")
    pokemon.strip().capitalize()
    html=get_html_pokemon(pokemon)
    pokemon_info = parse_html(html)
    print(f"Name: {pokemon_info['name']}")
    print(f"Types: {pokemon_info['types']}")
    print(f"Height: {pokemon_info['height']}")
    print(f"Weight: {pokemon_info['weight']}")
    print("Stats:")
    for stat, value in pokemon_info['stats'].items():
        print(f"  {stat}: {value}")



def main():
    """
    Main function to fetch and parse Pokémon information.
    Args:
        pokemon_name (str): The name of the Pokémon.
    """
    try:
        a = input("Do you want to create a database of Pokémon? (yes/no): ").strip().lower()
        if a == 'yes':
            generation = int(input("Enter the generation number (1-9): "))
            create_database(generation)
            print(f"Database created for generation {generation} in {OUTPUT_DIR}/pokemon_GEN{generation}.csv")
        else:
            get_pokemon()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
