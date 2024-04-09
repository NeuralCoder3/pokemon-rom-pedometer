import os

filename = "RadicalRed 4.1_1636 - Pokemon Fire Red (U)(Squirrels) (patched).srm"
os.rename(filename+".orig0", filename)
# remove all .orig files
i = 1
while True:
    RR_ORIG_PATH = f"{filename}.orig{i}"
    if not os.path.exists(RR_ORIG_PATH):
        break
    os.remove(RR_ORIG_PATH)
    i += 1