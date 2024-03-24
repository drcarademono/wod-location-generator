import csv

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

def update_csv_with_all_data(csv_filename, road_data_filename, track_data_filename, df_location_filename):
    road_data = read_bytes_file(road_data_filename)
    track_data = read_bytes_file(track_data_filename)
    locations = read_csv_file(csv_filename)
    width = 1000  # Width of the map, assuming it's the same for both roads and tracks
    
    # Create the (worldX, worldY) to locationtype mapping
    df_location_map = read_df_location_csv(df_location_filename)

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
        key = (x, y)
        location['df_locationtype'] = df_location_map.get(key, '')

    # Update fieldnames to include the new field
    fieldnames = list(locations[0].keys())
    if 'df_locationtype' not in fieldnames:
        fieldnames.append('df_locationtype')
        
    write_csv_file('updated_' + csv_filename, fieldnames, locations)

# Run the updated function to process roads, tracks data, and add df_locationtype
update_csv_with_all_data('locations.csv', 'roadData.bytes', 'trackData.bytes', 'DFLocations.csv')

