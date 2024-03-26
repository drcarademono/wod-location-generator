import os
import pandas as pd
from pathlib import Path

# Define the CSV files to be partitioned
csv_files = [
    "Locations.csv"
]

# Directory to store the partitioned files
locations_dir = Path("Locations")
locations_dir.mkdir(exist_ok=True)

# Define the columns to be included in the partitioned files
columns_to_include = [
    "name", "type", "prefab", "worldX", "worldY",
    "terrainX", "terrainY", "locationID", "gisX", "gisY"
]

# Columns to convert to string without trailing .0s
columns_to_convert = ["type", "worldX", "worldY", "terrainX", "terrainY"]

# Function to partition a CSV file
def partition_csv(file_name):
    file_path = Path(file_name)
    # Check if the CSV file exists
    if not file_path.is_file():
        print(f"File {file_name} not found. Skipping...")
        return
    
    df = pd.read_csv(file_path)
    
    for region, group in df.groupby('region'):
        # Convert specified fields to integers then to strings to remove trailing .0s
        for column in columns_to_convert:
            if column in group.columns:
                group[column] = group[column].fillna(0).astype(int).astype(str)
        
        # Filter the group to only include specified columns
        group_filtered = group[columns_to_include]
        
        # Directory names keep spaces
        region_dir = locations_dir / region
        region_dir.mkdir(parents=True, exist_ok=True)
        
        # Filenames have spaces removed
        sanitized_region_name = region.replace(" ", "")
        partitioned_file_name = f"{sanitized_region_name}_{file_path.name}"
        partitioned_file_path = region_dir / partitioned_file_name
        
        # Check if the partitioned file already exists
        if partitioned_file_path.is_file():
            print(f"File {partitioned_file_path} already exists. Skipping...")
            continue
        
        group_filtered.to_csv(partitioned_file_path, index=False)
        print(f"Partitioned file created: {partitioned_file_path}")

# Partition each CSV file if it exists and hasn't been processed yet
for file in csv_files:
    partition_csv(file)

