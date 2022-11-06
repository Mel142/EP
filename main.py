from fastapi import FastAPI
from fastapi.responses import FileResponse
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image

app = FastAPI()

# Get image size, bands, coordinate reference system and georeferenced bounding box attributes.
@app.get("/attributes")
def read_attributes():
    src = rasterio.open('S2L2A_2022-06-09.tiff')
    att = {
        "image_size" : {
            "width" : src.width,
            "height" : src.height
        },
        "bands" : src.count,
        "Coordinate Reference System" : src.crs,
        "Georeferenced Bounding Box" : src.bounds
    }
    return att

# Generate a 200x200 thumbnail of the image
@app.get("/thumbnail")
def create_thumbnail():
    src = rasterio.open('S2L2A_2022-06-09.tiff')
    red =  src.read(3)
    green = src.read(4)
    blue = src.read(2)

    # Normalize an array values to 0-255 range
    def normalize(band):
        band *= 255/band.max()
        return band

    # Adjust the contrast and brigtness by multiplying and adding a contast to the array
    def brigthen(band):
        alpha = 0.05
        beta = 0
        return np.clip(alpha*band+beta, 0,255)

    # Apply the brighten function and then normalizes each array
    red_b = brigthen(red)
    blue_b = brigthen(blue)
    green_b = brigthen(green)
    
    red_bn = normalize(red_b)
    blue_bn = normalize(blue_b)
    green_bn = normalize(green_b)

    # Create a 3D array by stacking the 3 arrays and convert it to int
    rgb_composite_bn = np.dstack((red_bn, green_bn, blue_bn)).astype(np.uint8)

    # Process the array as an image, generates and saves the thumbnail
    im = Image.fromarray(rgb_composite_bn, 'RGB')
    im.thumbnail((200,200))
    im.save('image_thumbnail.png', 'PNG')
    return FileResponse('image_thumbnail.png')

#Calculate NDVI and return it as an image
@app.get("/ndvi")
def calculate_ndvi():
    src = rasterio.open('S2L2A_2022-06-09.tiff')
    red = src.read(4)
    nir = src.read(8)
    ndvi = np.zeros(src.shape, dtype=rasterio.float32)
    ndvi = np.where(nir.astype(float) - red.astype(float)==0.,0,(nir.astype(float) - red.astype(float))/(nir + red))
    plt.imshow(ndvi, interpolation='lanczos')
    plt.axis('off')
    plt.savefig('ndvi.png',dpi=200,bbox_inches='tight', pad_inches=0)
    plt.close('all')
    return FileResponse('ndvi.png')