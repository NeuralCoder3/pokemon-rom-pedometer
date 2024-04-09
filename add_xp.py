from radicalred_savegame_editor import rr_parser
import os
import asyncio
import threading
import pokebase as pb

# path to the uncompressed srm (or sav) file
RR_FILENAME = "RadicalRed 4.1_1636 - Pokemon Fire Red (U)(Squirrels) (patched).srm"
LOG_FILENAME = "radicalred.log"
steps = 6993
image_folder = "images"
if not os.path.exists(image_folder):
    os.mkdir(image_folder)

steps_per_level = 5000
calories_per_step = 0.035
calories = steps * calories_per_step

game = rr_parser.load_radical_red_game(RR_FILENAME)
save = game.game_save
if not save:
    print("No save found")
    exit(1)
team = save.team
if not team:
    print("No team found")
    exit(1)

pk0 : rr_parser.Pokemon = team.team_pokemon_list[0]
level = pk0.level
print(pk0)

growth = pk0.sub_data_decrypted.growth
exp_offset = 4
exp_width = 4
exp = growth.data[exp_offset:exp_offset+exp_width]
exp = int.from_bytes(exp, 'little')
print("Level:", level)
print("Total EXP:", exp)
new_exp = exp+int(exp/level * steps/steps_per_level)
print("New EXP:", new_exp)


# print(name)


# Create GUI with image, name, level, progress bar for xp with highlighted progress for new xp, button to add&save

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
from io import BytesIO
from datetime import datetime
from tkinter.messagebox import showinfo

id = pk0.sub_data.species
# name = pb.pokemon(id).name
# image_url = pb.pokemon(id).sprites.front_default
image_url = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png"
name = str(id)

def add_xp_and_save():
    # add xp
    new_exp_byte = new_exp.to_bytes(exp_width, 'little')
    subdata = pk0.sub_data_decrypted.data
    # overwrite growth data block, specifically the exp
    # we can not write directly to the growth data property
    pk0.sub_data_decrypted.data = \
        subdata[:0*12+exp_offset] + new_exp_byte + subdata[0*12+exp_offset+exp_width:]

    # no need to overwrite encrypted data as we are GameType.RR
    pk0.update_from_sub_data()
    
    game.set_pokemon(pk0, 0)
    
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
        f.write(f"Added {steps} steps to {pk0.nickname} ({pk0.sub_data.species} -- {name}) changing exp from {exp} to {new_exp} (Time: {datetime.now()})\n")
    
    print("Saved")
    
    
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
    name = pb.pokemon(id).name
    image_url = pb.pokemon(id).sprites.front_default
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

# progress bar
progress = ttk.Progressbar(root, length=200, mode="determinate")
progress.grid(row=3, column=0, columnspan=2)
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
button.grid(row=4, column=0, columnspan=2)

root.mainloop()
