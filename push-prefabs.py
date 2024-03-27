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
    displacement = diagonal_span + 1  # +1 for extra buffer
    return displacement, displacement

def is_affected_by_road_track(roads, tracks):
    # Check if either roads or tracks field contains non-empty, non-null data
    return (pd.notnull(roads) and roads.strip() != "") or (pd.notnull(tracks) and tracks.strip() != "")

def move_off_road_track_center(roads_tracks, sizeX, sizeY):
    sizeX += 2  # Adding buffer
    sizeY += 2  # Adding buffer

    # Splitting roads_tracks to identify occupied directions
    roads_tracks_split = roads_tracks.split('|')
    all_cardinals = {'N', 'E', 'S', 'W'}
    occupied_directions = set(roads_tracks_split)

    available_directions = all_cardinals - occupied_directions

    if not available_directions:
        # All cardinal directions are occupied. 
        # As a fallback, move two steps away in a direction diagonally.
        # This is a workaround for a rare case and should be refined as per your project requirements.
        available_diagonals = {'NE', 'SE', 'SW', 'NW'} - occupied_directions
        if not available_diagonals:
            raise ValueError("No available directions to move from the center, including diagonals.")
        chosen_diagonal = random.choice(list(available_diagonals))
        if chosen_diagonal in ['NE', 'SE']:
            dx = 2  # Move East if NE or SE is available
        else:
            dx = -2  # Move West if SW or NW is available
        if chosen_diagonal in ['NE', 'NW']:
            dy = 2  # Move North if NE or NW is available
        else:
            dy = -2  # Move South if SE or SW is available
    else:
        # Pick a random direction from the available ones
        new_direction = random.choice(list(available_directions))
        direction_offsets = {
            'E': (1, 0),
            'W': (-1, 0),
            'N': (0, 1),
            'S': (0, -1)
        }
        dx, dy = direction_offsets[new_direction]
        # Move one step away in the chosen direction
        dx *= 2
        dy *= 2

    # Calculate displacement without needing diagonal adjustment
    displacementX = dx * ((sizeX + 2) / 2.0)  # Apply the buffer for x direction
    displacementY = dy * ((sizeY + 2) / 2.0)  # Apply the buffer for y direction
    
    # Calculate new position considering the displacement
    new_x = round(64 + displacementX)
    new_y = round(64 + displacementY)
    
    return new_x, new_y


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
        # Fallback to original position if no available directions are left, which should be rare
        return row['terrainX'], row['terrainY']
    
    # Pick a random direction from the available ones
    new_direction = random.choice(available_directions)
    direction_offsets = {
        'E': (1, 0),
        'W': (-1, 0),
        'N': (0, 1),
        'S': (0, -1)
    }
    dx, dy = direction_offsets[new_direction]
    
    # Determine the type of road and calculate displacement accordingly
    if any(d in directions for d in ['N', 'E', 'S', 'W']):  # Cardinal road present
        displacementX, displacementY = calculate_cardinal_displacement(sizeX, sizeY)
    elif any(d in directions for d in ['NE', 'NW', 'SE', 'SW']):  # Diagonal road present
        displacementX, displacementY = calculate_diagonal_displacement(sizeX, sizeY)
    else:
        # If neither cardinal nor diagonal roads are affecting the location, default to no displacement
        displacementX, displacementY = 0, 0

    # Apply the displacement to the location's coordinates
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

