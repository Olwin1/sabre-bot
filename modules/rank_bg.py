# Importing necessary modules
from modules import cache_get as cache
from PIL import Image
import random

# Function to fetch user data and return the path to a randomly selected image file
def fetch(user_id):
    # Retrieving user data from cache
    user = cache.get_user(user_id)
    
    # Setting a default image file
    file = "default.png"
    
    # If user ID matches a specific ID, choose a random image file from a list
    if user_id == 416617058248425473:
        file = random.choice(["bridge", "bridge_2", "bridge_3", "bridge_4", "graffitti1", "graffitti2", "graffitti3", "graffitti4", "street_wet_night", "street_night", "street_night_2", "snow", "rocks", "city_road", "city_dusk", "cherry_blossums", "car_sunset"])
        # Adding .png extension to the chosen file name
        file = file + ".png"
    
    # Constructing the final file path and returning it
    retval = "other/" + file
    return retval

# Function to get the dominant color of an image
def get_dominant_color(img):
    # Resizing the image to 1x1 pixel and getting its color
    img2 = img.resize((1, 1), Image.ANTIALIAS)
    temp = img2.getpixel((0,0))
    
    # Adding 40 to each RGB value to make the color slightly brighter
    retval = (temp[0] + 40, temp[1] + 40, temp[2] + 40)
    return retval

