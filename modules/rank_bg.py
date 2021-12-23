from modules import cache_get as cache
def fetch(user_id):
    user = cache.get_user(user_id)
    file = "default.png"
    if user_id == 416617058248425473:
        file = "bridge.png"
    retval = "other/" + file
    return retval