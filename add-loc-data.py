import csv
from PIL import Image
import pandas as pd
import geopandas as gpd

def read_bytes_file(filename):
    with open(filename, 'rb') as file:
        return file.read()

def get_byte_at_position(data, x, y, width):
    index = x + (y * width)
    return data[index]

def interpret_byte(byte_value):
    paths = {'N': False, 'NE': False, 'E': False, 'SE': False, 
             'S': False, 'SW': False, 'W': False, 'NW': False}

    if byte_value & 0b10000000:
        paths['N'] = True
    if byte_value & 0b01000000:
        paths['NE'] = True
    if byte_value & 0b00100000:
        paths['E'] = True
    if byte_value & 0b00010000:
        paths['SE'] = True
    if byte_value & 0b00001000:
        paths['S'] = True
    if byte_value & 0b00000100:
        paths['SW'] = True
    if byte_value & 0b00000010:
        paths['W'] = True
    if byte_value & 0b00000001:
        paths['NW'] = True

    return paths

def roads_vector_to_string(roads_vector):
    return ''.join(['1' if roads_vector[d] else '0' for d in ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']])

def read_csv_file(filename):
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

def write_csv_file(filename, fieldnames, data):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)

def interpret_byte_to_string(byte_value):
    """Convert the byte to a pipe-separated string representation showing which directions are available."""
    paths = interpret_byte(byte_value)
    return '|'.join([direction for direction, available in paths.items() if available])

def check_road_coordinate(x, y, road_data, width):
    road_byte = get_byte_at_position(road_data, x, y, width)
    return interpret_byte_to_string(road_byte)  # Use the updated function for pipe-separated values

def check_track_coordinate(x, y, track_data, width):
    track_byte = get_byte_at_position(track_data, x, y, width)
    return interpret_byte_to_string(track_byte)  # Reuse interpret_byte_to_string for tracks

def interpret_terrain(terrainX, terrainY, roads_vector):
    """
    Compares terrainX, terrainY with the lookup table and roads_vector to find a match.
    For (64, 64) locations, copies roads_vector into roads.
    """
    # Lookup table for terrain values
    terrain_lookup = {
        (32, 96): 'NW', (64, 96): 'N', (96, 96): 'NE',
        (32, 64): 'W',  (96, 64): 'E',
        (32, 32): 'SW', (64, 32): 'S', (96, 32): 'SE'
    }
    
    # Special case for (64, 64)
    if terrainX == 64 and terrainY == 64:
        return roads_vector  # Copy roads_vector into roads
    
    # Check for other matches in the lookup table
    for (tx, ty), direction in terrain_lookup.items():
        if terrainX == tx and terrainY == ty:
            # Check if this direction is in the roads_vector
            if direction in roads_vector.split('|'):
                return direction
    return ''

def read_df_location_csv(filename):
    """
    Reads the DFLocations.csv and returns two dictionaries:
    one with (worldX, worldY) as keys and locationtype as values,
    and another with (worldX, worldY) as keys and dungeontype as values.
    """
    df_locationtype_map = {}
    df_dungeontype_map = {}
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            key = (int(row['worldX']), int(row['worldY']))
            df_locationtype_map[key] = row['locationtype']
            df_dungeontype_map[key] = row['dungeontype']
    return df_locationtype_map, df_dungeontype_map

# Dictionary to map colors to climate types
color_to_climate = {
    (0, 32, 192): 'ocean',
    (0, 190, 0): 'woodland',
    (191, 143, 191): 'woodlandHills',
    (190, 166, 143): 'hauntedWoodland',
    (230, 196, 230): 'mountain',
    (216, 154, 62): 'hammerfellMountain',
    (0, 152, 25): 'rainforest',
    (115, 153, 141): 'swamp',
    (180, 180, 180): 'subtropical',
    (217, 217, 217): 'desert',
    (255, 255, 255): 'desert2'
}

def get_climate_from_image(image, x, y):
    """Get the climate type based on the pixel color at (x, y) in the image."""
    r, g, b = image.getpixel((x, y))[:3]  # Ignore the alpha channel
    return color_to_climate.get((r, g, b), 'unknown')  # Return 'unknown' if color does not match

# Now let's define the function to add the region using geopandas
def add_region(csv_filename, gpkg_filename):
    # Read the geopackage file with regions
    regions_gdf = gpd.read_file(gpkg_filename)

    # Read the locations csv file into a pandas DataFrame
    locations_df = pd.read_csv(csv_filename)
    # Convert the DataFrame to a GeoDataFrame
    locations_gdf = gpd.GeoDataFrame(locations_df, geometry=gpd.points_from_xy(locations_df.gisX, locations_df.gisY))
    locations_gdf.crs = "EPSG:4326"  # Set CRS to WGS 84
    
    # Ensure both GeoDataFrames have the same CRS
    locations_gdf = locations_gdf.to_crs(regions_gdf.crs)

    # Spatial join to find which region each location belongs to
    joined_gdf = gpd.sjoin(locations_gdf, regions_gdf, how="left", predicate='intersects')

    # Add the region information to the original DataFrame
    locations_df['region'] = joined_gdf['region']

    return locations_df

def determine_wilderness_level(row):
    # Conditions for wilderness_level 0
    if row['roads'] or row['df_locationtype'] in ['TownCity', 'TownHamlet', 'TownVillage']:
        return 0
    
    # Conditions for wilderness_level 1
    if not row['roads'] and row['roads_vector'] or \
       row['tracks'] or \
       row['df_locationtype'] in ['HomeFarms', 'Tavern', 'ReligionTemple', 'HomeWealthy']:
        return 1
    
    # If none of the above conditions are met, assign wilderness_level 2
    return 2

# Main function that processes all the data and updates the CSV
def update_csv_with_all_data(csv_filename, road_data_filename, track_data_filename, df_location_filename, climate_image_filename, gpkg_filename):
    road_data = read_bytes_file(road_data_filename)
    track_data = read_bytes_file(track_data_filename)
    df_locationtype_map, df_dungeontype_map = read_df_location_csv(df_location_filename)
    locations = read_csv_file(csv_filename)
    width = 1000  # Width of the map, assuming it's the same for both roads and tracks

    # Load the climate image and process each location
    with Image.open(climate_image_filename) as climate_img:
        for location in locations:
            x = int(location['worldX'])
            y = int(location['worldY'])

            # Assigning roads, tracks, location type, and climate
            location['roads_vector'] = check_road_coordinate(x, y, road_data, width)
            location['roads'] = interpret_terrain(int(location['terrainX']), int(location['terrainY']), location['roads_vector'])
            location['tracks_vector'] = check_track_coordinate(x, y, track_data, width)
            location['tracks'] = interpret_terrain(int(location['terrainX']), int(location['terrainY']), location['tracks_vector'])
            location['df_locationtype'] = df_locationtype_map.get((x, y), '')
            location['df_dungeontype'] = df_dungeontype_map.get((x, y), '')  # New field for dungeon type
            location['climate'] = get_climate_from_image(climate_img, x, y)

    # Convert updated location data to DataFrame for further processing
    locations_df = pd.DataFrame(locations)

    
    # Add region using the add_region function
    locations_with_region_df = add_region(csv_filename, gpkg_filename)

    # Ensure 'worldX' and 'worldY' are integers in both dataframes
    locations_df['worldX'] = locations_df['worldX'].astype(int)
    locations_df['worldY'] = locations_df['worldY'].astype(int)
    locations_with_region_df['worldX'] = locations_with_region_df['worldX'].astype(int)
    locations_with_region_df['worldY'] = locations_with_region_df['worldY'].astype(int)

    # Merge the updated location data with region information
    locations_df = locations_df.merge(locations_with_region_df[['worldX', 'worldY', 'region']], on=['worldX', 'worldY'], how='left')

    # Clean duplicates based on 'locationID' just before exporting
    locations_df = locations_df.drop_duplicates(subset='locationID', keep='first')

    # Apply the determine_wilderness_level function to each row to calculate 'wilderness_level'
    locations_df['wilderness_level'] = locations_df.apply(determine_wilderness_level, axis=1)
    
    # Prepare the fieldnames list for the CSV output
    fieldnames = list(locations_df.columns)
    
    # Write the final updated data to CSV
    write_csv_file('updated_' + csv_filename, fieldnames, locations_df.to_dict('records'))

# Example usage:
update_csv_with_all_data(
    'locations.csv',
    'roadData.bytes',
    'trackData.bytes',
    'DFLocations.csv',
    'DFClimateMap.png',
    'Regions.gpkg'
)
