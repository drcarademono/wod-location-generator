import pandas as pd
import numpy as np

def update_locations_with_lookup(populated_locations_path, location_names_path, output_path):
    # Load the data
    populated_locations = pd.read_csv(populated_locations_path)
    location_names = pd.read_csv(location_names_path)
    
    # Prepare a dictionary that maps each name to its possible prefabs along with type, sizeX, and sizeY
    name_to_details = location_names.groupby('name').apply(lambda df: df[['prefab', 'type', 'sizeX', 'sizeY']].to_dict('records')).to_dict()
    
    # Update prefab, type, sizeX, and sizeY fields in populated locations
    for index, row in populated_locations.iterrows():
        # Choose a prefab and its details at random for the given name
        if row['name'] in name_to_details:
            chosen_entry = np.random.choice(name_to_details[row['name']])
            populated_locations.at[index, 'prefab'] = chosen_entry['prefab']
            populated_locations.at[index, 'type'] = chosen_entry['type']
            populated_locations.at[index, 'sizeX'] = chosen_entry['sizeX']
            populated_locations.at[index, 'sizeY'] = chosen_entry['sizeY']
        else:
            print(f"No prefab found for name: {row['name']}")
    
    # Save the updated dataframe to a new CSV
    populated_locations.to_csv(output_path, index=False)
    print(f"Updated populated locations saved to {output_path}")

# Paths for the files (update these as necessary)
populated_locations_path = 'populated_locations.csv'
location_names_path = 'location_names.csv'
output_path = 'updated_populated_locations.csv'

# Run the function
update_locations_with_lookup(populated_locations_path, location_names_path, output_path)

