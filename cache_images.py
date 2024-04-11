import shelve
import pokebase as pb

max_id = 1024
cache = shelve.open("cache")

def get_image(id):
    return pb.pokemon(id).sprites.front_default

for id in range(1, max_id):
    str_id = str(id)
    if str_id not in cache:
        print("Fetching", id)
        cache[str_id] = get_image(id)
    else:
        print("Cached", id)
    
cache.close()