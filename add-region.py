import geopandas as gpd
import pandas as pd

def add_region_from_gpkg(csv_filename, gpkg_filename):
    # Load regions from geopackage
    regions = gpd.read_file(gpkg_filename)
    
    # Load locations and convert to GeoDataFrame
    locations_df = pd.read_csv(csv_filename)
    locations_gdf = gpd.GeoDataFrame(locations_df, geometry=gpd.points_from_xy(locations_df.gisX, locations_df.gisY))
    
    # Set the CRS for locations to WGS 84 (assuming gisX, gisY are longitude and latitude)
    locations_gdf.crs = "EPSG:4326"
    
    # Perform the spatial join
    joined_gdf = gpd.sjoin(locations_gdf, regions, how="left", op='intersects')
    
    # Extract the region name (assuming the column in the regions layer is named 'region')
    locations_df['region'] = joined_gdf['region']
    
    # Write updated CSV file
    locations_df.to_csv('updated_with_region_' + csv_filename, index=False)

# Example usage:
add_region_from_gpkg('locations.csv', 'Regions.gpkg')

