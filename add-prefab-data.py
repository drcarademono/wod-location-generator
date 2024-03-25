import pandas as pd
import numpy as np

def update_locations_with_lookup(populated_locations_path, location_names_path, output_path):
    # Load the data
    populated_locations = pd.read_csv(populated_locations_path)
    location_names = pd.read_csv(location_names_path)
    
    # Create a mapping from name to prefab and type
    name_to_prefabs = location_names.groupby('name')['prefab'].apply(list).to_dict()
    name_to_types = location_names.drop_duplicates('name').set_index('name')['type'].to_dict()
    
    # Update prefab and type fields in populated locations
    for index, row in populated_locations.iterrows():
        # Choose a prefab at random for the given name
        if row['name'] in name_to_prefabs:
            populated_locations.at[index, 'prefab'] = np.random.choice(name_to_prefabs[row['name']])
            populated_locations.at[index, 'type'] = name_to_types[row['name']]
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

