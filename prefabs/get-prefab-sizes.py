import pandas as pd
import xml.etree.ElementTree as ET
import os

# Step 1: Read the CSV file
df = pd.read_csv('location_names.csv')

# New columns for sizeX and sizeY
df['sizeX'] = None
df['sizeY'] = None

# Step 2: Iterate over each row in the DataFrame
for index, row in df.iterrows():
    prefab_name = row['prefab']
    xml_filename = f'{prefab_name}.txt'
    
    # Check if the corresponding XML file exists
    if os.path.exists(xml_filename):
        # Step 3: Parse the XML file and extract the height and width
        tree = ET.parse(xml_filename)
        root = tree.getroot()
        
        height = root.find('height').text if root.find('height') is not None else None
        width = root.find('width').text if root.find('width') is not None else None
        
        # Step 4: Update the DataFrame with sizeX and sizeY
        df.at[index, 'sizeX'] = width
        df.at[index, 'sizeY'] = height

# Step 5: Save the modified DataFrame to a new CSV file
df.to_csv('location_names.csv', index=False)

