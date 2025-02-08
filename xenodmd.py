import ctypes
import struct
import psutil
import pymem
import pymem.process
import tkinter as tk
from tkinter import font, Canvas, PhotoImage
import threading
import time
import os
import configparser
from PIL import Image, ImageTk, ImageOps

PROCESS_ALL_ACCESS = 0x1F0FFF  # Full access permissions
CONFIG_FILE = "config.cfg"


def load_config():
    """Load GUI settings from config file and provide default values for any missing entries."""
    config = configparser.ConfigParser()
    default_config = {
        "width": "1280",
        "height": "720",
        "x": "1920",
        "y": "0",
        "scale": "100",
        "text_color": "#95f184",
        "ball_count_color": "#ffcc00",
        "disp2_color": "#ff4444",
        "disp1_color": "#ff4444",
        "disp1_label": "Display 1:",
        "disp2_label": "Display 2:",
        "font": "Courier",
        "bg_alpha": "255",
        "wall_x": "100",
        "wall_y": "100",
        "wall_size_x": "800",
        "wall_size_y": "600",
        "process_name": "XENOTILT.exe"
    }
    
    if not os.path.exists(CONFIG_FILE):
        config["GUI"] = default_config
        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)
    else:
        config.read(CONFIG_FILE)
        if "GUI" not in config:
            config["GUI"] = default_config
        else:
            for key, value in default_config.items():
                if key not in config["GUI"]:
                    config["GUI"][key] = value
        with open(CONFIG_FILE, "w") as configfile:
            config.write(configfile)
    
    gui_config = config["GUI"]
    return (
        int(gui_config["width"]), int(gui_config["height"]), int(gui_config["x"]), int(gui_config["y"]), 
        int(gui_config["scale"]), gui_config["text_color"], gui_config["ball_count_color"], gui_config["disp2_color"],
        gui_config["disp1_color"], gui_config["disp1_label"], gui_config["disp2_label"], 
        gui_config["font"], int(gui_config["bg_alpha"]),
        int(gui_config["wall_x"]), int(gui_config["wall_y"]), int(gui_config["wall_size_x"]), int(gui_config["wall_size_y"]),
        gui_config["process_name"]
    )


def create_wallpaper_window(wall_x, wall_y, wall_size_x, wall_size_y, root):
    """Creates a second GUI window that displays the wallpaper.png image."""
    wall_root = tk.Toplevel()
    wall_root.overrideredirect(True)
    wall_root.geometry(f"{wall_size_x}x{wall_size_y}+{wall_x}+{wall_y}")
    
    canvas = Canvas(wall_root, width=wall_size_x, height=wall_size_y, highlightthickness=0, bd=0)
    canvas.pack()
    
    if os.path.exists("wallpaper.png"):
        image = Image.open("wallpaper.png").convert("RGBA")
        image = image.resize((wall_size_x, wall_size_y), Image.LANCZOS)
        bg_image = ImageTk.PhotoImage(image)
        canvas.create_image(0, 0, anchor="nw", image=bg_image)
        canvas.image = bg_image  
    
    wall_root.bind("<Escape>", lambda event: (wall_root.destroy(), root.destroy()))
    return wall_root

# Remove duplicate create_wallpaper_window function

def create_wallpaper_window(wall_x, wall_y, wall_size_x, wall_size_y, root):
    """Creates a second GUI window that displays the wallpaper.png image."""
    wall_root = tk.Toplevel()
    wall_root.overrideredirect(True)
    wall_root.geometry(f"{wall_size_x}x{wall_size_y}+{wall_x}+{wall_y}")
    
    canvas = Canvas(wall_root, width=wall_size_x, height=wall_size_y, highlightthickness=0, bd=0)
    canvas.pack()
    
    if os.path.exists("wallpaper.png"):
        image = Image.open("wallpaper.png").convert("RGBA")
        image = image.resize((wall_size_x, wall_size_y), Image.LANCZOS)
        bg_image = ImageTk.PhotoImage(image)
        canvas.create_image(0, 0, anchor="nw", image=bg_image)
        canvas.image = bg_image  
    
    wall_root.bind("<Escape>", lambda event: (wall_root.destroy(), root.destroy()))
    return wall_root

# Remove duplicate create_wallpaper_window function


def format_score(value):
    """Format the score with dots every three digits, ensuring it is always 12 digits long."""
    formatted_value = f"{value:012d}"
    return ".".join([formatted_value[max(i - 3, 0):i] for i in range(len(formatted_value), 0, -3)][::-1])


def read_memory_value(process_name, base_address, module_name, offsets):
    """Reads memory value using module base address + offsets."""
    try:
        pm = pymem.Pymem(process_name)
        module_base = pymem.process.module_from_name(pm.process_handle, module_name).lpBaseOfDll
        address = module_base + base_address
        for offset in offsets:
            address = pm.read_ulonglong(address)
            address += offset
        value = pm.read_ulonglong(address)
        return value
    except:
        return None


def update_gui(label_fg, label_ball_count, label_disp1, label_disp2, root, scale, disp1_label, disp2_label):

    """Continuously update the GUI with the memory values."""
    global previous_ball_count  
    previous_ball_count = None  
    displaying_message = False  

    def restore_score():
        """Restores the score display after message delay."""
        nonlocal displaying_message
        displaying_message = False  
        score_value = read_memory_value(PROCESS_NAME, BASE_ADDRESS, MODULE_NAME, OFFSETS)
        if score_value is not None:
            formatted_score = format_score(score_value)
            label_fg.config(text=formatted_score)

    while True:
        score_value = read_memory_value(PROCESS_NAME, BASE_ADDRESS, MODULE_NAME, OFFSETS)
        ball_count_value = read_memory_value(PROCESS_NAME, BALL_COUNT_BASE, MODULE2_NAME, BALL_COUNT_OFFSETS)
        disp2_value = read_memory_value(PROCESS_NAME, DISP2_BASE, MODULE_NAME, DISP2_OFFSETS)
        disp1_value = read_memory_value(PROCESS_NAME, DISP1_BASE, MODULE2_NAME, DISP1_OFFSETS)

        if ball_count_value is not None:
            label_ball_count.config(text=f"ball count: {ball_count_value}")

            if previous_ball_count is not None and ball_count_value > previous_ball_count:
                message = f"BALL {ball_count_value} READY!"
                label_fg.config(text=message)
                displaying_message = True
                root.after(2000, restore_score)

            elif previous_ball_count is not None and previous_ball_count > 0 and ball_count_value == 0:
                label_fg.config(text="WELCOME BACK")
                displaying_message = True
                root.after(4000, restore_score)

            previous_ball_count = ball_count_value  

        if score_value is not None and not displaying_message:
            formatted_score = format_score(score_value)
            label_fg.config(text=formatted_score)

        if disp2_value is not None:
            label_disp2.config(text=f"{disp2_label} {disp2_value:02d}")

        if disp1_value is not None:
            label_disp1.config(text=f"{disp1_label} {disp1_value:02d}")

        root.after(1, lambda: None)  
        time.sleep(0.5)


def create_gui():
    """Creates the GUI window to display the memory values like a Pinball DMD."""
    width, height, x, y, scale, text_color, ball_count_color, disp2_color, disp1_color, disp1_label, disp2_label, font_name, bg_alpha, wall_x, wall_y, wall_size_x, wall_size_y, process_name = load_config()
    
    global FONT_NAME
    FONT_NAME = font_name
    global PROCESS_NAME
    PROCESS_NAME = process_name
    
    root = tk.Tk()
    root.overrideredirect(True)  # Removes title bar
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.configure(bg='black')
    
    canvas = Canvas(root, width=width, height=height, highlightthickness=0, bd=0, bg='black')
    canvas.pack()
    
    if os.path.exists("background.png"):
        image = Image.open("background.png").convert("RGBA")
        image = image.resize((width, height), Image.LANCZOS)
        
        black_bg = Image.new("RGBA", (width, height), (0, 0, 0, 255))
        image = Image.alpha_composite(black_bg, image)
        alpha_channel = image.split()[3].point(lambda p: int(p * (bg_alpha / 255)))
        image.putalpha(alpha_channel)
        
        bg_image = ImageTk.PhotoImage(image)
        canvas.create_image(0, 0, anchor="nw", image=bg_image)
        canvas.image = bg_image

    wallpaper_window = create_wallpaper_window(wall_x, wall_y, wall_size_x, wall_size_y, root)
    
    custom_font = font.Font(family=font_name, size=int(height * scale / 100))
    ball_count_font = font.Font(family=font_name, size=int(height * scale / 200))
    disp2_font = font.Font(family=font_name, size=int(height * scale / 350))
    disp1_font = font.Font(family=font_name, size=int(height * scale / 350))
    
    label_fg = tk.Label(canvas, text="0.000.000.000.000", fg=text_color, bg='black', font=custom_font)
    label_fg.place(relx=0.5, rely=0.5, anchor='center')
    
    label_ball_count = tk.Label(root, text=" ball count: 0", fg=ball_count_color, bg='black', font=ball_count_font)
    label_ball_count.place(relx=0.95, rely=0.95, anchor='se')
    
    label_disp2 = tk.Label(root, text=f" {disp2_label} 00", fg=disp2_color, bg='black', font=disp2_font)
    label_disp2.place(relx=0.05, rely=0.95, anchor='sw')

    label_disp1 = tk.Label(root, text=f" {disp1_label} 00", fg=disp1_color, bg='black', font=disp1_font)
    label_disp1.place(relx=0.05, rely=0.85, anchor='sw')
    
    root.bind("<Escape>", lambda event: (root.destroy()))
    
    threading.Thread(target=update_gui, args=(label_fg, label_ball_count, label_disp1, label_disp2, root, scale, disp1_label, disp2_label), daemon=True).start()

    root.mainloop()



if __name__ == "__main__":
    BASE_ADDRESS = 0x0074A0B8
    MODULE_NAME = "mono-2.0-bdwgc.dll"
    MODULE2_NAME = "UnityPlayer.dll"
    OFFSETS = [0x30, 0xE88]
    
    BALL_COUNT_BASE = 0x01D21378
    BALL_COUNT_OFFSETS = [0x0, 0x58, 0x0, 0xC0, 0x28, 0x38, 0x670]
    
    DISP2_BASE = 0x00754850
    DISP2_OFFSETS = [0x198, 0x410, 0x850, 0x120, 0xB0]

    DISP1_BASE = 0x01D047E8
    DISP1_OFFSETS = [0xD0, 0x8, 0x68, 0x30, 0xB8, 0x2A0, 0x170]

    create_gui()
