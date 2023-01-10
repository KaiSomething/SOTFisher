from time import sleep
import threading
import json
import PySimpleGUI as sg

from PIL import ImageGrab, Image
import numpy as np
import win32gui
import threading

import pytesseract
from random import randint
import io
import base64

pytesseract.pytesseract.tesseract_cmd = r"tesseract/tesseract.exe"

fish_names = "splashtail,pondie,islehopper,ancientscale,plentifin,wildsplash,devilfish,battlegill,wrecker,stormfish".split(",")
f = open("fish.json", "r")
fish_data = json.loads(f.read())
f.close()
        
def get_image():
    hwnd = win32gui.FindWindowEx(None, None, None, "Sea of Thieves")
    win32gui.SetForegroundWindow(hwnd)
    bbox = win32gui.GetWindowRect(hwnd)
    im = ImageGrab.grab(bbox)
    im = im.convert('RGBA')
    data = np.array(im)
    r, g, b, a = data.T
    thresh = 150

    black_areas = ((r > thresh) & (b > thresh) & (g > thresh))
    data[..., :-1][black_areas.T] = (thresh+1, thresh+1, thresh+1) # Transpose back needed
    white_areas = (r <= thresh) | (b <= thresh) | (g <= thresh)
    data[..., :-1][white_areas.T] = (255, 255, 255) # Transpose back needed
    white_areas = (r == thresh+1) & (b == thresh+1) & (g == thresh+1)
    data[..., :-1][white_areas.T] = (0, 0, 0) # Transpose back needed

    im = Image.fromarray(data)
    width, height = im.size

    left = width/5
    top = height/6
    right = width - width/5
    bottom = height - height/6
    
    im1 = im.crop((left, top, right, bottom))
    return im1

sg.theme('DarkAmber')   # Add a touch of color
# All the stuff inside your window.
layout = [  [sg.Text('Ruby Splashtail', font=("Helvetica", 25), key="name")],
            [sg.Column([[sg.Image('images/Ruby_Splashtail.png', key="image")]], justification="center")],
            [sg.Text("Variant: ", font=("Helvetica", 15)), sg.Text("Common variant", font=("Helvetica", 15), text_color="white", key="variant")],
            [sg.Text("Cooked: ", font=("Helvetica", 12)), sg.Text("100 gold", font=("Helvetica", 15), text_color="white", key="cooked")],
            [sg.Text("Raw: ", font=("Helvetica", 12)), sg.Text("100 gold", font=("Helvetica", 15), text_color="white", key="raw")],
            [sg.Text("Burnt: ", font=("Helvetica", 12)), sg.Text("100 gold", font=("Helvetica", 15), text_color="white", key="burnt")],
            [sg.Push(), sg.Button("Pin", key="pin")]]

def convert_to_bytes(file_or_bytes, resize=None):
    if isinstance(file_or_bytes, str):
        img = Image.open(file_or_bytes)
    else:
        try:
            img = Image.open(io.BytesIO(base64.b64decode(file_or_bytes)))
        except Exception as e:
            dataBytesIO = io.BytesIO(file_or_bytes)
            img = Image.open(dataBytesIO)

    cur_width, cur_height = img.size
    if resize:
        new_width, new_height = resize
        scale = min(new_height/cur_height, new_width/cur_width)
        img = img.resize((int(cur_width*scale), int(cur_height*scale)), Image.ANTIALIAS)
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    del img
    return bio.getvalue()

def update_window(fish, trophy):
    name = list(fish["name"])
    for i in range(len(name)):
        if(i == 0):
            name[i] = name[i].upper()
        elif(name[i-1] == " "):
            name[i] = name[i].upper()
    name = "".join(name)
    if(trophy):
        trophy = "t"
        window["name"].update("Trophy " + name)
    else:
        trophy = "r"
        window["name"].update(name)
    f = open("images/"+name.replace(" ", "_")+".png", "rb")
    image_data = f.read()
    f.close()

    window["image"].update(data=image_data)
    window["variant"].update(fish["variant"])
    window["cooked"].update(str(fish["cook_"+trophy]) + " gold")
    window["raw"].update(str(fish["raw_"+trophy]) + " gold")
    window["burnt"].update(str(fish["burn_"+trophy]) + " gold")
    print(fish)

def main_loop():
    global end
    while True:
        if(not end):
            sleep(0.5)
            if(win32gui.GetWindowText(win32gui.GetForegroundWindow()) == "Sea of Thieves"):
                img = get_image()
                text = pytesseract.image_to_string(img).lower()
                fish = None
                trophy = False
                
                for i in fish_names:
                    if(i in text):
                        found = False
                        for t in fish_data[i]:
                            if(t["name"].split(" ")[0] in text):
                                found = True
                                fish = t
                        if(not found): print("Unidentifiable "+i)
                if("trophy" in text):
                    trophy = True
                if(fish != None):
                    update_window(fish, trophy)
        else:
            break

end = False
x = threading.Thread(target=main_loop)
x.start()

# Create the Window
window = sg.Window('Fishbook', layout, finalize=True, icon='images/icon.ico')
update_window(fish_data["splashtail"][0], False)
# Event Loop to process "events" and get the "values" of the inputs
pinned = False
while True:
    event, values = window.read()
    if(event == "pin"):
        if(not pinned):
            window.TKroot.wm_attributes("-topmost", True)
            window["pin"].update("Unpin")
            pinned = True
        else:
            window.TKroot.wm_attributes("-topmost", False)
            window["pin"].update("Pin")
            pinned = False
    if event == sg.WIN_CLOSED or event == 'Exit': # if user closes window or clicks cancel
        end = True
        break

window.close()
print(window)
x.join()