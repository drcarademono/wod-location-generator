import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from shapely.affinity import affine_transform

def read_bytes_file(filename):
    with open(filename, 'rb') as file:
        return file.read()

def get_byte_at_position(data, x, y, width):
    index = x + (y * width)
    return data[index]

def interpret_byte(byte_value):
    paths = {'N': False, 'NE': False, 'E': False, 'SE': False, 
             'S': False, 'SW': False, 'W': False, 'NW': False}

    if byte_value & 0b10000000:  # N
        paths['N'] = True
    if byte_value & 0b01000000:  # NE
        paths['NE'] = True
    if byte_value & 0b00100000:  # E
        paths['E'] = True
    if byte_value & 0b00010000:  # SE
        paths['SE'] = True
    if byte_value & 0b00001000:  # S
        paths['S'] = True
    if byte_value & 0b00000100:  # SW
        paths['SW'] = True
    if byte_value & 0b00000010:  # W
        paths['W'] = True
    if byte_value & 0b00000001:  # NW
        paths['NW'] = True

    return paths

def check_coordinate(x, y, road_data, track_data, width):
    road_byte = get_byte_at_position(road_data, x, y, width)
    track_byte = get_byte_at_position(track_data, x, y, width)

    road_paths = interpret_byte(road_byte)
    track_paths = interpret_byte(track_byte)

    return {'roads': road_paths, 'tracks': track_paths}

def construct_lines_for_coordinate(x, y, road_data, track_data, width):
    paths = check_coordinate(x, y, road_data, track_data, width)
    road_lines = []
    track_lines = []

    directions = {
        'N': (0, -1), 'NE': (1, -1), 'E': (1, 0), 'SE': (1, 1),
        'S': (0, 1), 'SW': (-1, 1), 'W': (-1, 0), 'NW': (-1, -1)
    }

    for direction, exists in paths['roads'].items():
        if exists:
            dx, dy = directions[direction]
            end_x, end_y = x + dx, y + dy
            road_lines.append(LineString([(x, y), (end_x, end_y)]))

    for direction, exists in paths['tracks'].items():
        if exists:
            dx, dy = directions[direction]
            end_x, end_y = x + dx, y + dy
            track_lines.append(LineString([(x, y), (end_x, end_y)]))

    return road_lines, track_lines

def transform_geometries(gdf):
    # This transformation mirrors across the X-axis and then translates
    transformed_gdf = gdf.copy()
    transformed_gdf['geometry'] = transformed_gdf['geometry'].apply(lambda geom: affine_transform(geom, [1, 0, 0, -1, 0.5, -0.5]))
    return transformed_gdf

# Main execution starts here
if __name__ == "__main__":
    road_data = read_bytes_file('roadData.bytes')
    track_data = read_bytes_file('trackData.bytes')
    width, height = 1000, 500

    road_lines = []
    track_lines = []

    for y in range(height):
        for x in range(width):
            roads, tracks = construct_lines_for_coordinate(x, y, road_data, track_data, width)
            road_lines.extend(roads)
            track_lines.extend(tracks)

    road_gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries(MultiLineString(road_lines)))
    track_gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries(MultiLineString(track_lines)))

    # Apply transformation (mirror and translate)
    transformed_road_gdf = transform_geometries(road_gdf)
    transformed_track_gdf = transform_geometries(track_gdf)

    # Save the transformed geometries to separate GeoPackage files
    transformed_road_gdf.to_file("transformed_roads.gpkg", driver="GPKG")
    transformed_track_gdf.to_file("transformed_tracks.gpkg", driver="GPKG")

    print("Transformed GeoPackage files 'transformed_roads.gpkg' and 'transformed_tracks.gpkg' have been created.")

