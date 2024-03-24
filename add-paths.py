import csv
from PIL import Image

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
        (32, 95): 'NW', (64, 95): 'N', (95, 95): 'NE',
        (32, 64): 'W',  (95, 64): 'E',
        (32, 32): 'SW', (64, 32): 'S', (95, 32): 'SE'
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
    Reads the DFLocations.csv and returns a dictionary with (worldX, worldY) as keys
    and locationtype as values.
    """
    df_location_map = {}
    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            key = (int(row['worldX']), int(row['worldY']))
            df_location_map[key] = row['locationtype']
    return df_location_map

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

def update_csv_with_all_data(csv_filename, road_data_filename, track_data_filename, df_location_filename, climate_image_filename):
    road_data = read_bytes_file(road_data_filename)
    track_data = read_bytes_file(track_data_filename)
    df_location_map = read_df_location_csv(df_location_filename)
    locations = read_csv_file(csv_filename)
    width = 1000  # Width of the map, assuming it's the same for both roads and tracks
    
    # Load the climate image
    with Image.open(climate_image_filename) as climate_img:
        for location in locations:
            x = int(location['worldX'])
            y = int(location['worldY'])
            terrainX = int(location['terrainX'])
            terrainY = int(location['terrainY'])
            
            # Roads
            roads_vector_str = check_road_coordinate(x, y, road_data, width)
            location['roads_vector'] = roads_vector_str
            location['roads'] = interpret_terrain(terrainX, terrainY, roads_vector_str)

            # Tracks
            tracks_vector_str = check_track_coordinate(x, y, track_data, width)
            location['tracks_vector'] = tracks_vector_str
            location['tracks'] = interpret_terrain(terrainX, terrainY, tracks_vector_str)
            
            # DF Location Type
            location['df_locationtype'] = df_location_map.get((x, y), '')
            
            # Climate
            location['climate'] = get_climate_from_image(climate_img, x, y)

        # Update fieldnames to include the new fields
        fieldnames = list(locations[0].keys())
        for new_field in ['roads_vector', 'roads', 'tracks_vector', 'tracks', 'df_locationtype', 'climate']:
            if new_field not in fieldnames:
                fieldnames.append(new_field)
        
        write_csv_file('updated_' + csv_filename, fieldnames, locations)

# Example usage:
update_csv_with_all_data('locations.csv', 'roadData.bytes', 'trackData.bytes', 'DFLocations.csv', 'DFClimateMap.png')
