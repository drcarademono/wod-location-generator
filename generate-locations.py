import csv
import random
from PIL import Image

# Example probability values, adjust them as needed
wilderness_chance = 32
track_chance = 9
road_chance = 3

# Define the baseline brightness of the color #848683 for comparison
baseline_brightness = (132 + 134 + 131) / 3  # Brightness of the color #848683

def calculate_brightness(rgb):
    """Calculate the average brightness of an RGB color."""
    return sum(rgb) / 3

def get_scaling_factor(worldX, worldY, image):
    """Calculate the scaling factor based on pixel brightness at (worldX, worldY) compared to the reference color."""
    pixel_rgb = image.getpixel((worldX, worldY))
    pixel_brightness = calculate_brightness(pixel_rgb)
    reference_brightness = calculate_brightness(reference_color_rgb)
    scaling_factor = pixel_brightness / reference_brightness
    return scaling_factor

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
        'N': (64, 107), 'NE': (107, 107), 'E': (107, 64), 'SE': (107, 21),
        'S': (64, 21), 'SW': (21, 21), 'W': (21, 64), 'NW': (21, 107)
    }

    for direction, has_path in directions.items():
        if has_path:
            centers.append(direction_to_center[direction])
    # Filter out any coordinates that are not 21, 64, or 107
    centers = [center for center in centers if center[0] in [21, 64, 107] and center[1] in [21, 64, 107]]
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

def is_center_water_pixel(cell_x, cell_y, water_map):
    # The scaling factors are determined by the ratio of the water map size to the game map size (in cells)
    scale_x = water_map.size[0] / 3000  # water map width / game map width in cells
    scale_y = water_map.size[1] / 1500  # water map height / game map height in cells
    
    # Calculate the corresponding top-left pixel of the cell block on the water map
    water_x = int(cell_x * scale_x)
    water_y = int(cell_y * scale_y)
    
    # Determine the center of the cell block on the water map
    center_x = water_x + int(scale_x / 2)
    center_y = water_y + int(scale_y / 2)
    
    # Assuming the water is represented by black in RGBA
    black_color = (0, 0, 0, 255)  
    pixel_color = water_map.getpixel((center_x, center_y))
    
    return pixel_color == black_color

def should_generate_location(chance, worldX, worldY, heatmap):
    """Decides whether to generate a location based on modified chance influenced by heatmap brightness."""
    baseline_brightness = (132 + 134 + 131) / 3  # Brightness of the color #848683
    scaling_factor = calculate_scaling_factor(worldX, worldY, heatmap, baseline_brightness)
    adjusted_chance = max(1, int(chance * scaling_factor))  # Ensure the chance is at least 1
    return random.randint(1, adjusted_chance) == 1

def calculate_scaling_factor(worldX, worldY, heatmap, baseline_brightness):
    pixel = heatmap.getpixel((worldX, worldY))
    pixel_brightness = sum(pixel[:3]) / 3  # Average of R, G, B values
    
    # Inverting the scaling effect with a simple approach and normalization
    scaling_factor = baseline_brightness / max(pixel_brightness, 1)  # Avoid division by zero
    
    # Normalize or limit the scaling factor to prevent extreme values
    scaling_factor = min(max(scaling_factor, 1.0), 4.0)  # Example bounds: 0.5 to 2

    return scaling_factor

def generate_wilderness_centers(has_road, exclusions, x, y, map_pixel_has_df_location, heatmap):
    """Generates wilderness center locations based on road presence and DFLocation exclusions, adjusted by heatmap."""
    centers = []
    valid_terrain_coords = [21, 64, 107]  # The valid terrain coordinates within a map pixel
    global wilderness_chance, track_chance, road_chance  # Ensure these are defined at the script's start

    # Adjust chances based on heatmap
    if map_pixel_has_df_location:
        chance = road_chance  # Adjusted example; choose the appropriate chance based on your logic
    elif has_road:
        chance = track_chance
    else:
        chance = wilderness_chance

    for terrainX in valid_terrain_coords:
        for terrainY in valid_terrain_coords:
            if (terrainX, terrainY) != (64, 64) and should_generate_location(chance, x, y, heatmap):
                centers.append((terrainX, terrainY))
                
    return centers
    return centers

def generate_csv_with_locations(road_data_filename, track_data_filename, dflocations_filename, water_map_filename, output_csv_filename, heatmap_filename):
    road_data = read_bytes_file(road_data_filename)
    track_data = read_bytes_file(track_data_filename)
    exclusions, town_exclusions = load_exclusions_from_dflocations(dflocations_filename)
    water_map = Image.open(water_map_filename)  # Open the detailed water map
    heatmap = Image.open(heatmap_filename)  # Open the heatmap for scaling factors based on brightness
    width, height = 1000, 500  # Width and height for the game map

    with open(output_csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['name', 'type', 'prefab', 'worldX', 'worldY', 'terrainX', 'terrainY', 'locationID', 'gisX', 'gisY'])

        for y in range(height):
            for x in range(width):
                combined_paths, has_any_path = check_coordinate(x, y, road_data, track_data, width)
                map_pixel_has_df_location = (x, y) in exclusions
                
                # If the map pixel is listed in DFLocations.csv, all cells have a 1 in 6 chance of getting a location,
                # except for the center cell (64, 64), which is handled within the generate_wilderness_centers function.
                if map_pixel_has_df_location:
                    centers = generate_wilderness_centers(True, exclusions, x, y, True, heatmap)
                else:
                    road_centers = cell_center_from_direction(combined_paths, has_any_path)
                    road_centers = [center for center in road_centers if should_generate_location(road_chance, x, y, heatmap)]
                    wilderness_centers = generate_wilderness_centers(has_any_path, exclusions, x, y, False, heatmap)
                    centers = road_centers + wilderness_centers

                for terrainX, terrainY in centers:
                    # Convert terrain coordinates (0-127) to cell coordinates (0-2) and adjust for water map checking
                    cell_x = (x * 3) + (terrainX // (128 // 3))
                    cell_y = (y * 3) + (terrainY // (128 // 3))

                    # Skip if the center of the cell would be in water or if it's a town exclusion
                    if is_center_water_pixel(cell_x, cell_y, water_map) or (x, y) in town_exclusions:
                        continue

                    # Calculate GIS coordinates
                    gisX, gisY = calculate_gis_coordinates(x, y, terrainX, terrainY)

                    # Generate locationID with leading zeros if necessary
                    locationID = f"{x:02}{terrainX:02}{y:02}{terrainY:02}"

                    # Write to CSV if the cell is not water
                    writer.writerow(['', '', '', x, y, terrainX, terrainY, locationID, gisX, gisY])

# Example usage
generate_csv_with_locations('roadData.bytes', 'trackData.bytes', 'DFLocations.csv', 'DFWaterMap.png', 'locations.csv', 'DFPopHeatMap.png')


