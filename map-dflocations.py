import csv
from PIL import Image

def generate_image(csv_file, output_file, width=1000, height=500):
    # Create a new black image
    img = Image.new('RGB', (width, height), color='black')

    # Open the CSV file and iterate through rows
    with open(csv_file, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Extract worldX and worldY from the row
            worldX = int(row['worldX'])
            worldY = int(row['worldY'])

            # Map the worldX and worldY to pixel coordinates
            pixelX = worldX - 1  # Adjust for 0-based indexing
            pixelY = height - worldY  # Flip Y-axis
            # Set the pixel to white
            img.putpixel((pixelX, pixelY), (255, 255, 255))

    # Save the image
    img.save(output_file)

if __name__ == "__main__":
    csv_file = 'DFLocations.csv'
    output_file = 'output.png'
    generate_image(csv_file, output_file)

