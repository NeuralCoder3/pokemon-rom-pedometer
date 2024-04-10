from radicalred_savegame_editor import rr_parser
import os
import asyncio
import threading
import pokebase as pb
module_species = rr_parser.constants.rr._species

# path to the uncompressed srm (or sav) file
RR_FILENAME = "saves/RadicalRed 4.1_1636 - Pokemon Fire Red (U)(Squirrels) (patched).srm"
LOG_FILENAME = "radicalred.log"
# pokemon_number = 0
pokemon_number = 3
image_folder = "images"
if not os.path.exists(image_folder):
    os.mkdir(image_folder)

steps_per_level = 5000
calories_per_step = 0.035
# calories = steps * calories_per_step

game = rr_parser.load_radical_red_game(RR_FILENAME)
save = game.game_save
if not save:
    print("No save found")
    exit(1)
team = save.team
if not team:
    print("No team found")
    exit(1)

pk : rr_parser.Pokemon = team.team_pokemon_list[pokemon_number]
level = pk.level
print(pk)

growth = pk.sub_data_decrypted.growth
exp_offset = 4
exp_width = 4
exp = growth.data[exp_offset:exp_offset+exp_width]
exp = int.from_bytes(exp, 'little')
print("Level:", level)
print("Total EXP:", exp)
species_id = pk.sub_data.species

# find constant SPECIES_* such that the value is the species_id
species_name = None
for name, value in module_species.__dict__.items():
    if value == species_id:
        species_name = name.split("_")[1]
        break
    
pokedex_id = rr_parser.constants.rr.get_species_pokedex_id(species_name)
    
# exit(0)
# print(name)


# Create GUI with image, name, level, progress bar for xp with highlighted progress for new xp, button to add&save

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
from io import BytesIO
from datetime import datetime
from tkinter.messagebox import showinfo

# name = pb.pokemon(id).name
# image_url = pb.pokemon(id).sprites.front_default
image_url = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png"
# name = f"Pokemon {pokedex_id}"
name = species_name.capitalize()
steps = 0
new_exp = exp

def add_xp_and_save():
    # add xp
    new_exp_byte = new_exp.to_bytes(exp_width, 'little')
    subdata = pk.sub_data_decrypted.data
    # overwrite growth data block, specifically the exp
    # we can not write directly to the growth data property
    pk.sub_data_decrypted.data = \
        subdata[:0*12+exp_offset] + new_exp_byte + subdata[0*12+exp_offset+exp_width:]

    # no need to overwrite encrypted data as we are GameType.RR
    pk.update_from_sub_data()
    
    game.set_pokemon(pk, pokemon_number)
    
    # save
        
    # move original save to .orig\d file
    # save as original file
    i = 0
    while True:
        RR_ORIG_PATH = f"{RR_FILENAME}.orig{i}"
        if not os.path.exists(RR_ORIG_PATH):
            break
        i += 1
    os.rename(RR_FILENAME, RR_ORIG_PATH)
    rr_parser.save_game(game, RR_FILENAME)
    
    # append date and time to log file
    with open(LOG_FILENAME, "a") as f:
        f.write(f"Added {steps} steps to {pk.nickname} ({pk.sub_data.species} -- {name}) changing exp from {exp} to {new_exp} (Time: {datetime.now()})\n")
    
    print("Saved")
    
def compute_new_exp(given_steps):
    global new_exp, steps
    steps = given_steps
    # linear
    # new_exp = exp+int(exp/level * steps/steps_per_level)
    # https://bulbapedia.bulbagarden.net/wiki/Experience
    # https://www.pokewiki.de/Erfahrung
    # https://pwo-wiki.info/index.php/Experience_Typ
    levels_to_add = steps/steps_per_level
    # as float; for computation
    new_level = level + levels_to_add
    # the experience is roughly cubic to the level
    # f(l) = c * l^3
    # but with x^3, we overapproximate a lot, let's try x^2
    exponent = 2
    estimated_c = exp / level**exponent
    new_exp = int(estimated_c * new_level**exponent)
    print("New EXP:", new_exp)
    
    
root = tk.Tk()
root.title("Add XP")
root.geometry("400x400")
root.resizable(False, False)
root.columnconfigure(0, weight=1)

# image
response = requests.get(image_url)
img = Image.open(BytesIO(response.content))
img = img.resize((300, 300))
img = ImageTk.PhotoImage(img)
panel = tk.Label(root, image=img)
panel.grid(row=0, column=0, columnspan=2)

# name
name_label = tk.Label(root, text=name)
name_label.grid(row=1, column=0, columnspan=2)

# load name and image_url from pokebase asynchonously
def load_pokebase_data():
    global name, image_url
    # name = pb.pokemon(species_id).name
    # name = species_name 
    # image_url = pb.pokemon(species_id).sprites.front_default
    image_url = pb.pokemon(pokedex_id).sprites.front_default
    print("Loaded pokebase data:", name, image_url)
    # update name and image in GUI
    name_label.config(text=name)
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    img = img.resize((300, 300))
    img = ImageTk.PhotoImage(img)
    panel.config(image=img)
    panel.image = img
    root.update()
    
# asyncio.run(load_pokebase_data())
# loop = asyncio.get_event_loop()
# loop.create_task(load_pokebase_data())
# loop.run_until_complete(load_pokebase_data())
threading.Thread(target=load_pokebase_data).start()

# level
level_label = tk.Label(root, text=f"Level: {level}")
level_label.grid(row=2, column=0, columnspan=2)

# number input field for steps
input_panel = tk.Frame(root)
input_panel.grid(row=3, column=0, columnspan=2)
steps_label = tk.Label(input_panel, text="Steps:")
steps_label.pack(side="left")
steps_entry = tk.Entry(input_panel)
steps_entry.pack(side="left")
# steps_entry["width"] = 10

# on change => compute new exp
def on_change(event):
    global steps
    steps = int(steps_entry.get())
    compute_new_exp(steps)
    progress["value"] = exp
    progress["maximum"] = new_exp
    style.configure("LabeledProgressbar", text=f"{exp}/{new_exp}")
steps_entry.bind("<KeyRelease>", on_change)

# progress bar
progress = ttk.Progressbar(root, length=200, mode="determinate")
progress.grid(row=4, column=0, columnspan=2)
progress["maximum"] = new_exp
progress["value"] = exp
# show value as white text on progress bar
style = ttk.Style()
style.layout("LabeledProgressbar",
             [('LabeledProgressbar.trough',
               {'children': [('LabeledProgressbar.pbar',
                              {'side': 'left', 'sticky': 'ns'}),
                             ("LabeledProgressbar.label", {"sticky": ""})],
               'sticky': 'nswe'})])
style.configure("LabeledProgressbar", text=f"{exp}/{new_exp}")
style.map("LabeledProgressbar",
          foreground=[('!disabled', 'white')],
          # color of the progress bar
          background=[('!disabled', 'dark blue')],
          # color behind the progress bar
          troughcolor=[('!disabled', 'light blue')]
          )
progress["style"] = "LabeledProgressbar"

# button
def execute():
    if new_exp == exp:
        showinfo("No Change", "Please enter a number of steps to add")
        return
    add_xp_and_save()
    # show popup 
    showinfo("Saved", "Successfully added XP and saved to \""+RR_FILENAME+"\"")
    # root.update()
    root.destroy()
    # popup = tk.Toplevel()
    # popup.title("Saved")
    # popup.geometry("200x100")
    # popup.resizable(False, False)
    # label = tk.Label(popup, text="Saved")
    # label.pack()
    # def close():
    #     popup.destroy()
    #     root.destroy()
    # button = tk.Button(popup, text="Close", command=close)
    # button.pack()
    
    # popup.mainloop()
    
button = tk.Button(root, text="Add XP and Save", command=execute)
button.grid(row=5, column=0, columnspan=2)

root.mainloop()
