import csv
import random

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

def check_coordinate(x, y, road_data, track_data, width):
    road_byte = get_byte_at_position(road_data, x, y, width)
    track_byte = get_byte_at_position(track_data, x, y, width)

    road_paths = interpret_byte(road_byte)
    track_paths = interpret_byte(track_byte)

    combined_paths = {k: road_paths[k] or track_paths[k] for k in road_paths}
    has_any_path = any(combined_paths.values())
    return combined_paths, has_any_path

def cell_center_from_direction(directions, has_any_path):
    centers = []
    if has_any_path:
        # Include the center cell if there's any road or track
        centers.append((64, 64))

    # Mapping additional directions to 3x3 cell centers within a 128x128 grid
    direction_to_center = {
        'N': (64, 95), 'NE': (95, 95), 'E': (95, 64), 'SE': (95, 32),
        'S': (64, 32), 'SW': (32, 32), 'W': (32, 64), 'NW': (32, 95)
    }

    for direction, has_path in directions.items():
        if has_path:
            centers.append(direction_to_center[direction])
    return centers

def calculate_gis_coordinates(worldX, worldY, terrainX, terrainY):
    gisX = worldX + (terrainX / 128.0)
    gisY = -(worldY) - (1 - terrainY / 128.0)
    return gisX, gisY

def load_exclusions_from_dflocations(dflocations_filename):
    exclusions = set()
    town_exclusions = set()
    with open(dflocations_filename, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            worldX = int(row['worldX'])
            worldY = int(row['worldY'])
            # Add to exclusions if there's already a central location
            exclusions.add((worldX, worldY))
            # Add to town exclusions if the location type is a town or hamlet
            if row['locationtype'] in ['TownCity', 'TownHamlet']:
                town_exclusions.add((worldX, worldY))
    return exclusions, town_exclusions

def should_generate_location(probability):
    """Return True with a likelihood of 1/probability."""
    return random.randint(1, probability) == 1

def generate_wilderness_centers(has_road, exclusions, x, y):
    centers = []
    if has_road:
        # In cells with roads, also check the empty cells for a 1 in 18 chance of location
        for terrainX in range(0, 128, 64):
            for terrainY in range(0, 128, 64):
                if (terrainX, terrainY) != (64, 64) and should_generate_location(18):
                    centers.append((terrainX, terrainY))
    else:
        # For a wilderness map pixel, add a location at the center with a 1 in 32 chance
        if should_generate_location(32):
            centers.append((64, 64))
    return centers

def generate_csv_with_locations(road_data_filename, track_data_filename, dflocations_filename, output_csv_filename):
    road_data = read_bytes_file(road_data_filename)
    track_data = read_bytes_file(track_data_filename)
    exclusions, town_exclusions = load_exclusions_from_dflocations(dflocations_filename)
    width, height = 1000, 500

    with open(output_csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['name', 'type', 'prefab', 'worldX', 'worldY', 'terrainX', 'terrainY', 'locationID', 'gisX', 'gisY'])
        
        for y in range(height):
            for x in range(width):
                if (x, y) in town_exclusions:
                    continue

                combined_paths, has_any_path = check_coordinate(x, y, road_data, track_data, width)
                
                # Generate locations on road cells with a 1 in 6 chance
                road_centers = cell_center_from_direction(combined_paths, False)
                road_centers = [center for center in road_centers if should_generate_location(6)]
                
                # Handle wilderness cells within the map pixel
                wilderness_centers = generate_wilderness_centers(has_any_path, exclusions, x, y)
                
                # Combine centers from roads and wilderness, but exclude the center if it's already marked by DFLocation.csv
                centers = road_centers + wilderness_centers
                if (x, y) in exclusions:
                    centers = [center for center in centers if center != (64, 64)]
                
                # Write the locations to the CSV
                for terrainX, terrainY in centers:
                    gisX, gisY = calculate_gis_coordinates(x, y, terrainX, terrainY)
                    writer.writerow(['', '', '', x, y, terrainX, terrainY, '', gisX, gisY])

# Example usage
generate_csv_with_locations('roadData.bytes', 'trackData.bytes', 'DFLocations.csv', 'locations.csv')

