import csv
import pandas as pd
import random
import numpy as np

def move_off_road_track_center(roads_tracks):
    directions = ['E', 'W', 'N', 'S', 'NE', 'NW', 'SE', 'SW']
    occupied = set()

    # Size of the location
    size = 2.5

    if isinstance(roads_tracks, str):
        for direction in roads_tracks.split('|'):
            if direction in directions:
                occupied.add(direction)

    # Find directions not occupied by roads or tracks
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

    new_x = 64 + (dx * size)
    new_y = 64 + (dy * size)
    return new_x, new_y

def move_off_road_track_general(row):
    size = 2.5  # Half the size of the location
    directions = {
        'E': (1, 0),
        'W': (-1, 0),
        'N': (0, 1),
        'S': (0, -1),
        'NE': (1, 1),
        'NW': (-1, 1),
        'SE': (1, -1),
        'SW': (-1, -1)
    }

    # Initially no offset
    offset_x, offset_y = 0, 0

    # Convert NaN to empty strings before attempting to split
    roads = str(row['roads']) if pd.notnull(row['roads']) else ""
    tracks = str(row['tracks']) if pd.notnull(row['tracks']) else ""

    # If there are specified roads or tracks, proceed as before
    if roads or tracks:
        for direction in (roads + '|' + tracks).split('|'):
            if direction:
                dx, dy = directions[direction]
                offset_x += dx * size
                offset_y += dy * size
    else:
        # If no specific direction due to road/track, pick a random direction to move
        random_direction = random.choice(list(directions.values()))
        offset_x, offset_y = random_direction[0] * size, random_direction[1] * size

    # Calculate the new position with random movement if not specified by roads or tracks
    new_x = min(max(row['terrainX'] + offset_x, size), 128 - size)
    new_y = min(max(row['terrainY'] + offset_y, size), 128 - size)

    return new_x, new_y

def move_off_road_track(row):
    roads_tracks_combined = (str(row['roads']) if pd.notnull(row['roads']) else "") + '|' + (str(row['tracks']) if pd.notnull(row['tracks']) else "")
    if row['terrainX'] == 64 and row['terrainY'] == 64:
        return move_off_road_track_center(roads_tracks_combined)
    else:
        return move_off_road_track_general(row)

# Read CSV
df = pd.read_csv('updated_populated_locations.csv')

# Apply the function to move locations off roads/tracks
df[['terrainX', 'terrainY']] = df.apply(lambda row: move_off_road_track(row), axis=1, result_type='expand')

# Save to a new CSV file
df.to_csv('updated_locations_off_roads_tracks.csv', index=False)

print("Locations have been updated and saved to 'updated_locations_off_roads_tracks.csv'.")

