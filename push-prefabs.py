import csv
import pandas as pd
import random
import numpy as np

def get_opposite_directions(directions):
    """Given a list of directions, returns a list of directions excluding the opposites and the same directions."""
    opposite = {
        'N': ['N', 'S', 'SE', 'SW'],
        'S': ['S', 'N', 'NE', 'NW'],
        'E': ['E', 'W', 'SW', 'NW'],
        'W': ['W', 'E', 'SE', 'NE'],
        'NE': ['NE', 'SW', 'S', 'W'],
        'NW': ['NW', 'SE', 'S', 'E'],
        'SE': ['SE', 'NW', 'N', 'W'],
        'SW': ['SW', 'NE', 'N', 'E']
    }
    available_directions = set(['N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW'])
    for d in directions:
        if d in opposite:
            available_directions -= set(opposite[d])
    return list(available_directions)

def calculate_displacement(dx, dy, sizeX, sizeY):
    # Check if movement is diagonal
    is_diagonal = dx != 0 and dy != 0
    # Apply a larger adjustment for diagonal movements to ensure clearing the road
    diagonal_adjustment = np.sqrt(2) if is_diagonal else 1

    displacementX = dx * ((sizeX + 2) / 2.0) * diagonal_adjustment  # +2 for extra buffer
    displacementY = dy * ((sizeY + 2) / 2.0) * diagonal_adjustment  # +2 for extra buffer
    return displacementX, displacementY

def is_affected_by_road_track(roads, tracks):
    # Check if either roads or tracks field contains non-empty, non-null data
    return (pd.notnull(roads) and roads.strip() != "") or (pd.notnull(tracks) and tracks.strip() != "")

def move_off_road_track_center(roads_tracks, sizeX, sizeY):
    # Add 2 to each dimension for extra buffer
    sizeX += 2
    sizeY += 2

    directions = ['E', 'W', 'N', 'S', 'NE', 'NW', 'SE', 'SW']
    occupied = set()

    if isinstance(roads_tracks, str):
        for direction in roads_tracks.split('|'):
            if direction in directions:
                occupied.add(direction)

    available_directions = list(set(directions) - occupied)

    if not available_directions:
        new_direction = 'E'
    else:
        new_direction = random.choice(available_directions)

    direction_offsets = {
        'E': (1, 0),
        'W': (-1, 0),
        'N': (0, 1),
        'S': (0, -1),
        'NE': (1, 1),
        'NW': (-1, 1),
        'SE': (1, -1),
        'SW': (-1, -1)
    }
    dx, dy = direction_offsets[new_direction]
    
    # Apply diagonal adjustment if necessary
    displacementX, displacementY = calculate_displacement(dx, dy, sizeX, sizeY)
    
    # Calculate new position considering diagonal adjustment
    # Assuming the original center position (64,64) needs adjustment for context-specific logic
    new_x = round(64 + displacementX)
    new_y = round(64 + displacementY)
    return new_x, new_y

def move_off_road_track_general(row):
    # Adjust sizes for buffer
    sizeX, sizeY = row['sizeX'] + 2, row['sizeY'] + 2

    # Handle NaN values by converting them to empty strings before splitting
    roads = str(row['roads']) if pd.notnull(row['roads']) else ""
    tracks = str(row['tracks']) if pd.notnull(row['tracks']) else ""
    directions = roads.split('|') + tracks.split('|')

    # Get available directions that are not opposite to the roads/tracks
    available_directions = get_opposite_directions(directions)
    
    if not available_directions:
        # Fallback in case no available directions are left, which should be rare
        return row['terrainX'], row['terrainY']
    
    # Pick a random direction from the available ones
    new_direction = random.choice(available_directions)
    direction_offsets = {
        'E': (1, 0),
        'W': (-1, 0),
        'N': (0, 1),
        'S': (0, -1),
        'NE': (1, 1),
        'NW': (-1, 1),
        'SE': (1, -1),
        'SW': (-1, -1)
    }
    dx, dy = direction_offsets[new_direction]
    
    # Apply diagonal adjustment if necessary
    displacementX, displacementY = calculate_displacement(dx, dy, sizeX, sizeY)
    
    # Move the location considering the diagonal adjustment
    new_x = round(min(max(row['terrainX'] + displacementX, sizeX / 2.0), 128 - sizeX / 2.0))
    new_y = round(min(max(row['terrainY'] + displacementY, sizeY / 2.0), 128 - sizeY / 2.0))
    return new_x, new_y

def move_off_road_track(row):
    roads = str(row['roads']) if pd.notnull(row['roads']) else ""
    tracks = str(row['tracks']) if pd.notnull(row['tracks']) else ""
    
    # Only proceed if the location is actually affected by roads or tracks
    if is_affected_by_road_track(roads, tracks):
        if row['terrainX'] == 64 and row['terrainY'] == 64:
            # For center locations, only move if roads or tracks information is actually present
            if roads.strip() or tracks.strip():
                return move_off_road_track_center(roads + '|' + tracks, row['sizeX'], row['sizeY'])
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

