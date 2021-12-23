from modules import cache_get as cache
from PIL import Image
import random
def fetch(user_id):
    user = cache.get_user(user_id)
    file = "default.png"
    if user_id == 416617058248425473:
        file = random.choice(["bridge", "bridge_2", "bridge_3", "bridge_4", "graffitti1", "graffitti2", "graffitti3", "graffitti4", "street_wet_night", "street_night", "street_night_2", "snow", "rocks", "city_road", "city_dusk", "cherry_blossums"])
        file = file + ".png"
    retval = "other/" + file
    return retval

def get_dominant_color(img):
    img2 = img.resize((1, 1), Image.ANTIALIAS)
    temp = img2.getpixel((0,0))
    retval = (temp[0] + 40, temp[1] + 40, temp[2] + 40)
    return retval