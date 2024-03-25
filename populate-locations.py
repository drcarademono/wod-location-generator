import pandas as pd
import numpy as np

def load_data(locations_path, rules_path):
    df_locations = pd.read_csv(locations_path)
    rules_df = pd.read_csv(rules_path)
    return df_locations, rules_df

def split_conditions(conditions):
    return [] if pd.isnull(conditions) else [condition.strip() for condition in conditions.split('|')]

def check_in_conditions(row_value, conditions):
    return True if not conditions else row_value in conditions

def check_not_in_conditions(row_value, conditions):
    return True if not conditions or row_value not in conditions else False

def apply_rules(row, rules_df):
    name_probabilities = {name: 1 for name in rules_df['name'].unique()}
    
    for _, rule in rules_df.iterrows():
        wilderness_level_rule = rule['wilderness_level'] if not pd.isnull(rule['wilderness_level']) else -1
        
        # Check if wilderness level matches
        if wilderness_level_rule == -1 or row['wilderness_level'] == wilderness_level_rule:
            in_climate_conditions = split_conditions(rule['in_climate'])
            not_in_climate_conditions = split_conditions(rule['not_in_climate'])
            in_region_conditions = split_conditions(rule['in_region'])
            not_in_region_conditions = split_conditions(rule['not_in_region'])
            in_locationtype_conditions = split_conditions(rule.get('df_locationtype', ''))
            in_dungeontype_conditions = split_conditions(rule.get('df_dungeontype', ''))
            
            # Check if climate, region, location type, and dungeon type conditions match
            if (check_in_conditions(row['climate'], in_climate_conditions) and
                check_not_in_conditions(row['climate'], not_in_climate_conditions) and
                check_in_conditions(row['region'], in_region_conditions) and
                check_not_in_conditions(row['region'], not_in_region_conditions) and
                check_in_conditions(row.get('df_locationtype', ''), in_locationtype_conditions) and
                check_in_conditions(row.get('df_dungeontype', ''), in_dungeontype_conditions)):
                name_probabilities[rule['name']] *= rule['probability_scale']

    # Normalize probabilities
    total_scale = sum(name_probabilities.values())
    normalized_probabilities = {k: v / total_scale for k, v in name_probabilities.items()}

    return normalized_probabilities


def choose_name(probabilities):
    names, probs = zip(*probabilities.items())
    chosen_name = np.random.choice(names, p=probs)
    return chosen_name

def update_locations(df_locations, rules_df):
    for index, row in df_locations.iterrows():
        probabilities = apply_rules(row, rules_df)
        df_locations.at[index, 'name'] = choose_name(probabilities)  # Set the chosen 'name' in the locations DataFrame
        if (index + 1) % 10 == 0:
            print(f"Processed {index + 1}/{len(df_locations)} locations...")
    return df_locations

def main(locations_path, rules_path, output_path):
    df_locations, rules_df = load_data(locations_path, rules_path)
    updated_locations = update_locations(df_locations, rules_df)
    updated_locations.to_csv(output_path, index=False)
    print("Update complete. File saved to", output_path)

# Update these paths as needed
locations_path = 'updated_locations.csv'
rules_path = 'location_rules.csv'
output_path = 'populated_locations.csv'

main(locations_path, rules_path, output_path)

