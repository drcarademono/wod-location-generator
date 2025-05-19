import csv
import pandas as pd
import random
import numpy as np

direction_offsets = {
    'N': (0, 1),
    'E': (1, 0),
    'S': (0, -1),
    'W': (-1, 0)
}

def get_opposite_directions(directions):
    """
    Modified to exclude directions that would move the location onto a road or track.
    For diagonal roads, it excludes the direction of the road and its component cardinal directions.
    """
    opposite = {
        'N': ['N', 'S'],
        'S': ['S', 'N'],
        'E': ['E', 'W'],
        'W': ['W', 'E']
    }
    # Diagonal roads will block their component cardinal directions
    diagonal_blocking = {
        'NE': ['N', 'E'],
        'NW': ['N', 'W'],
        'SE': ['S', 'E'],
        'SW': ['S', 'W']
    }
    
    available_directions = set(['N', 'S', 'E', 'W'])
    
    for d in directions:
        if d in opposite:
            available_directions -= set(opposite[d])
        if d in diagonal_blocking:
            available_directions -= set(diagonal_blocking[d])
    
    return list(available_directions)

def get_opposite_directions_center(directions):
    """
    Modified to exclude directions that would move the location onto a road or track.
    For diagonal roads, it excludes the direction of the road and its component cardinal directions.
    """
    opposite = {
        'N': ['N'],
        'S': ['S'],
        'E': ['E'],
        'W': ['W']
    }
    # Diagonal roads will block their component cardinal directions
    diagonal_blocking = {
        'NE': ['NE'],
        'NW': ['NW'],
        'SE': ['SE'],
        'SW': ['SW']
    }
    
    available_directions = set(['N', 'S', 'E', 'W'])
    
    for d in directions:
        if d in opposite:
            available_directions -= set(opposite[d])
        if d in diagonal_blocking:
            available_directions -= set(diagonal_blocking[d])
    
    return list(available_directions)

def calculate_cardinal_displacement(sizeX, sizeY):
    """
    Calculate the displacement needed to move the location off the cardinal-direction road.
    """
    # Displacement is half the size plus buffer in the given cardinal direction
    displacementX = (sizeX + 2) / 2.0  # +2 for extra buffer
    displacementY = (sizeY + 2) / 2.0  # +2 for extra buffer
    return displacementX, displacementY

def calculate_diagonal_displacement(sizeX, sizeY):
    """
    Calculate the displacement needed to move the location off the diagonal road.
    """
    # Calculate the half-diagonal span of the location including buffer
    diagonal_span = np.sqrt((sizeX / 2) ** 2 + (sizeY / 2) ** 2)
    # Displacement for diagonal directions; we move perpendicularly to the diagonal road
    displacement = diagonal_span + (diagonal_span / 2) + 1  # +1 for extra buffer
    return displacement, displacement

def is_affected_by_road_track(roads, tracks):
    # Check if either roads or tracks field contains non-empty, non-null data
    return (pd.notnull(roads) and roads.strip() != "") or (pd.notnull(tracks) and tracks.strip() != "")


def calculate_displacement_for_diagonal_clearance(sizeX, sizeY):
    """
    Calculate displacement needed to clear diagonal roads when moving in a cardinal direction.
    This assumes that the diagonal span of the location is the largest obstacle to clear.
    """
    diagonal_clearance = np.sqrt((sizeX ** 2) + (sizeY ** 2))
    buffer = 2  # Additional buffer for safety
    return (diagonal_clearance / 2) + buffer

def move_off_road_track_center(roads_tracks, sizeX, sizeY, locationID):
    sizeX += 2  # Adding buffer
    sizeY += 2  # Adding buffer

    # Splitting roads_tracks to identify occupied directions
    roads_tracks_split = roads_tracks.split('|')

    # Determine available movement directions based on the roads/tracks
    available_directions = get_opposite_directions_center(roads_tracks_split)

    if all(direction in roads_tracks_split for direction in ['N', 'E', 'S', 'W']):
        # Since all cardinal directions are blocked, we select two at random to move the location
        print(f"Debug: All cardinal directions are blocked for locationID: {locationID}.")
        to_clear = random.sample(['N', 'E', 'S', 'W'], 2)

        displacementX, displacementY = 0, 0
        for direction in to_clear:
            displacement = calculate_displacement_for_diagonal_clearance(sizeX, sizeY)
            if direction == 'N':
                displacementY -= displacement
            elif direction == 'S':
                displacementY += displacement
            elif direction == 'E':
                displacementX += displacement
            elif direction == 'W':
                displacementX -= displacement
    else:
        # If not all cardinal directions are blocked, use the available directions from get_opposite_directions
        new_direction = random.choice(available_directions)
        dx, dy = direction_offsets[new_direction]

        # Check for diagonal roads in the way based on the chosen direction
        diagonal_road_in_the_way = any(road in roads_tracks_split for road in ['NE', 'NW', 'SE', 'SW'])
        
        # Calculate displacement based on the presence of diagonal roads
        if diagonal_road_in_the_way:
            displacement = calculate_displacement_for_diagonal_clearance(sizeX, sizeY)
        else:
            # Use standard displacement for cardinal directions
            displacement = (sizeX / 2) if new_direction in ['E', 'W'] else (sizeY / 2)
        
        # Apply the displacement only in the direction chosen
        displacementX = dx * displacement
        displacementY = dy * displacement

    # Calculate new position considering the displacement
    new_x = 64 + displacementX
    new_y = 64 + displacementY
    
    return round(new_x), round(new_y)

def move_off_road_track_general(row):
    """
    Adjusts the location off roads or tracks using only cardinal directions. It takes into account
    diagonal roads by ensuring movement is in a direction that clears the location from such roads.
    """
    sizeX, sizeY = row['sizeX'] + 2, row['sizeY'] + 2  # Adjust sizes for buffer

    # Handle NaN values by converting them to empty strings
    roads = str(row['roads']) if pd.notnull(row['roads']) else ""
    tracks = str(row['tracks']) if pd.notnull(row['tracks']) else ""
    directions = roads.split('|') + tracks.split('|')

    # Get available cardinal directions excluding those blocked by roads/tracks
    available_directions = get_opposite_directions(directions)
    
    if not available_directions:
        # Fallback to original position if no available directions are left
        return row['terrainX'], row['terrainY']
    
    # Pick a random direction from the available ones
    new_direction = random.choice(available_directions)
    
    # Determine the type of road and calculate displacement accordingly
    displacementX, displacementY = 0, 0  # Initialize displacement values
    if any(d in directions for d in ['NE', 'NW', 'SE', 'SW']):  # Diagonal road present
        # Calculate displacement needed to clear the diagonal road
        displacement, _ = calculate_diagonal_displacement(sizeX, sizeY)
        # Only move perpendicular to the diagonal road
        if 'N' in directions or 'S' in directions:
            displacementX = displacement
            displacementY = 0
        else:
            displacementX = 0
            displacementY = displacement
    elif any(d in directions for d in ['N', 'E', 'S', 'W']):  # Cardinal road present
        displacementX, displacementY = calculate_cardinal_displacement(sizeX, sizeY)
        dx, dy = direction_offsets[new_direction]
        displacementX *= dx  # Apply the displacement only in the chosen cardinal direction
        displacementY *= dy

    # Apply the displacement to the location's coordinates
    new_x = min(max(row['terrainX'] + displacementX, sizeX / 2.0), 128 - sizeX / 2.0)
    new_y = min(max(row['terrainY'] + displacementY, sizeY / 2.0), 128 - sizeY / 2.0)
    
    return round(new_x), round(new_y)


def move_off_road_track(row):
    roads = str(row['roads']) if pd.notnull(row['roads']) else ""
    tracks = str(row['tracks']) if pd.notnull(row['tracks']) else ""
    
    # Only proceed if the location is actually affected by roads or tracks
    if is_affected_by_road_track(roads, tracks):
        if row['terrainX'] == 64 and row['terrainY'] == 64:
            # For center locations, only move if roads or tracks information is actually present
            if roads.strip() or tracks.strip():
                return move_off_road_track_center(roads + '|' + tracks, row['sizeX'], row['sizeY'], row['locationID'])
            else:
                return 64, 64
        else:
            return move_off_road_track_general(row)
    else:
        # If not affected by roads or tracks, return the current coordinates unchanged
        return row['terrainX'], row['terrainY']

# Read CSV
df = pd.read_csv('updated_populated_locations.csv')

# Apply the function to move locations off roads/tracks
df[['terrainX', 'terrainY']] = df.apply(lambda row: move_off_road_track(row), axis=1, result_type='expand')

# Save to a new CSV file
df.to_csv('updated_locations_off_roads_tracks.csv', index=False)

print("Locations have been updated and saved to 'updated_locations_off_roads_tracks.csv'.")

