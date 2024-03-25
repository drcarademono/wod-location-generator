import pandas as pd
import numpy as np

def load_data(locations_path, rules_path):
    df_locations = pd.read_csv(locations_path)
    rules_df = pd.read_csv(rules_path)
    return df_locations, rules_df

def split_conditions(conditions):
    # Split the conditions by '|' and strip whitespaces, handle NaN as empty list
    return [] if pd.isnull(conditions) else [condition.strip() for condition in conditions.split('|')]

def check_in_conditions(row_value, conditions):
    # If the list of conditions is empty, return True (no conditions to meet)
    if not conditions:
        return True
    # If row value is in conditions list, return True
    return row_value in conditions

def check_not_in_conditions(row_value, conditions):
    # If the list of conditions is empty, or the row value is not in conditions, return True
    if not conditions or row_value not in conditions:
        return True
    return False

def apply_rules(row, rules_df):
    # Define a variable to hold the default value for a wildcard
    WILDERNESS_LEVEL_WILDCARD = -1
    
    # Start with equal probability for each prefab
    prefab_probabilities = {prefab: 1 for prefab in rules_df['prefab'].unique()}

    for _, rule in rules_df.iterrows():
        # Treat NaN or empty wilderness_level as wildcard
        wilderness_level_rule = rule['wilderness_level'] if not pd.isnull(rule['wilderness_level']) else WILDERNESS_LEVEL_WILDCARD
        
        # Apply rule based on wilderness level or wildcard
        if wilderness_level_rule == WILDERNESS_LEVEL_WILDCARD or row['wilderness_level'] == wilderness_level_rule:
            in_climate_conditions = split_conditions(rule['in_climate'])
            not_in_climate_conditions = split_conditions(rule['not_in_climate'])
            in_region_conditions = split_conditions(rule['in_region'])
            not_in_region_conditions = split_conditions(rule['not_in_region'])

            # Check all conditions
            if (check_in_conditions(row['climate'], in_climate_conditions) and
                check_not_in_conditions(row['climate'], not_in_climate_conditions) and
                check_in_conditions(row['region'], in_region_conditions) and
                check_not_in_conditions(row['region'], not_in_region_conditions)):
                prefab_probabilities[rule['prefab']] *= rule['probability_scale']

    # Normalize probabilities to sum to 1
    total_scale = sum(prefab_probabilities.values())
    normalized_probabilities = {k: v / total_scale for k, v in prefab_probabilities.items()}

    return normalized_probabilities


    # Normalize probabilities to sum to 1
    total_scale = sum(prefab_probabilities.values())
    normalized_probabilities = {k: v / total_scale for k, v in prefab_probabilities.items()}

    return normalized_probabilities

def choose_prefab(probabilities):
    prefabs, probs = zip(*probabilities.items())
    chosen_prefab = np.random.choice(prefabs, p=probs)
    return chosen_prefab

def update_locations(df_locations, rules_df):
    for index, row in df_locations.iterrows():
        probabilities = apply_rules(row, rules_df)
        df_locations.at[index, 'prefab'] = choose_prefab(probabilities)
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

