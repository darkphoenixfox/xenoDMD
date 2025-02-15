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
import sys
import configparser
from PIL import Image, ImageTk, ImageOps

PROCESS_ALL_ACCESS = 0x1F0FFF  # Full access permissions
CONFIG_FILE = "config.cfg"


def load_config():
    """Loads settings from the config file and returns them as variables."""
    config = configparser.ConfigParser()
    config.read("config.cfg")

    # DMD settings
    dmd_enabled = config.getboolean("DMD", "enabled", fallback=True)
    dmd_width = int(config["DMD"]["dmd_width"])
    dmd_height = int(config["DMD"]["dmd_height"])
    dmd_x = int(config["DMD"]["dmd_x"])
    dmd_y = int(config["DMD"]["dmd_y"])
    dmd_bg = config["DMD"]["dmd_bg"]
    bg_alpha = int(config["DMD"]["bg_alpha"])


    # Backglass settings
    backglass_enabled = config.getboolean("BACKGLASS", "enabled", fallback=True)
    back_x = int(config["BACKGLASS"]["back_x"])
    back_y = int(config["BACKGLASS"]["back_y"])
    back_width = int(config["BACKGLASS"]["back_width"])
    back_height = int(config["BACKGLASS"]["back_height"])
    backglass_bg = config["BACKGLASS"]["backglass_bg"]

    # Display settings
    score_color = config["DISPLAYS"]["score_color"]
    score_x = config["DISPLAYS"]["score_x"]
    score_y = config["DISPLAYS"]["score_y"]
    score_size = int(config["DISPLAYS"]["score_size"])
    score_font = config["DISPLAYS"]["score_font"]
    ball_count_enabled = config.getboolean("DISPLAYS", "ball_count_enabled", fallback=True)
    ball_count_label = config["DISPLAYS"]["ball_count_label"]
    ball_count_color = config["DISPLAYS"]["ball_count_color"]
    ball_count_x = config["DISPLAYS"]["ball_count_x"]
    ball_count_y = config["DISPLAYS"]["ball_count_y"]
    ball_count_size = config["DISPLAYS"]["ball_count_size"]
    disp1_enabled = config.getboolean("DISPLAYS", "disp1_enabled", fallback=True)
    disp1_label = config["DISPLAYS"]["disp1_label"]
    disp1_color = config["DISPLAYS"]["disp1_color"]
    disp1_x = config["DISPLAYS"]["disp1_x"]
    disp1_y = config["DISPLAYS"]["disp1_y"]
    disp1_size = config["DISPLAYS"]["disp1_size"]
    disp2_enabled = config.getboolean("DISPLAYS", "disp2_enabled", fallback=True)
    disp2_label = config["DISPLAYS"]["disp2_label"]
    disp2_color = config["DISPLAYS"]["disp2_color"]
    disp2_size = config["DISPLAYS"]["disp2_size"]
    disp2_x = config["DISPLAYS"]["disp2_x"]
    disp2_y = config["DISPLAYS"]["disp2_y"]

    

    # Memory settings
    process_name = config["MEMORY"]["process_name"]
    module_name = config["MEMORY"]["module_name"]
    module2_name = config["MEMORY"]["module2_name"]
    score_address = int(config["MEMORY"]["score_address"], 16)
    score_offsets = [int(offset, 16) for offset in config["MEMORY"]["score_offsets"].split(",")]

    ball_count_base = int(config["MEMORY"]["ball_count_base"], 16)
    ball_count_offsets = [int(offset, 16) for offset in config["MEMORY"]["ball_count_offsets"].split(",")]

    disp1_base = int(config["MEMORY"]["disp1_base"], 16)
    disp1_offsets = [int(offset, 16) for offset in config["MEMORY"]["disp1_offsets"].split(",")]

    disp2_base = int(config["MEMORY"]["disp2_base"], 16)
    disp2_offsets = [int(offset, 16) for offset in config["MEMORY"]["disp2_offsets"].split(",")]

    return (
        dmd_width, dmd_height, dmd_x, dmd_y, score_size, dmd_bg, bg_alpha, score_font,
        back_x, back_y, back_width, back_height, backglass_bg,
        score_color, ball_count_label, ball_count_color, disp1_label, disp1_color, disp2_label, disp2_color,
        process_name, module_name, module2_name, score_address, score_offsets,
        ball_count_base, ball_count_offsets, disp1_base, disp1_offsets, disp2_base, disp2_offsets,
        disp1_x, disp1_y, disp1_size, disp2_x, disp2_y, disp2_size,
        ball_count_x, ball_count_y, ball_count_size, dmd_enabled, backglass_enabled,
        ball_count_enabled, disp1_enabled, disp2_enabled,
        score_x, score_y
    )


def create_backglass_window(back_x, back_y, back_width, back_height, backglass_bg, root):
    """Creates a separate window to display the backglass image."""
    wall_root = tk.Toplevel()
    wall_root.overrideredirect(True)
    wall_root.geometry(f"{back_width}x{back_height}+{back_x}+{back_y}")

    canvas = Canvas(wall_root, width=back_width, height=back_height, highlightthickness=0, bd=0)
    canvas.pack()

    if os.path.exists(backglass_bg):
        image = Image.open(backglass_bg).convert("RGBA")
        image = image.resize((back_width, back_height), Image.LANCZOS)
        bg_image = ImageTk.PhotoImage(image)
        canvas.create_image(0, 0, anchor="nw", image=bg_image)
        canvas.image = bg_image

    wall_root.bind("<Escape>", lambda event: (wall_root.destroy(), root.destroy()))
    return wall_root


def create_dmd():
    """Initializes and creates the GUI window for displaying the DMD and backglass, loading necessary settings."""
    (
        dmd_width, dmd_height, dmd_x, dmd_y, score_size, dmd_bg, bg_alpha, score_font,
        back_x, back_y, back_width, back_height, backglass_bg,
        score_color, ball_count_label, ball_count_color, disp1_label, disp1_color, disp2_label, disp2_color,
        process_name, module_name, module2_name, score_address, score_offsets,
        ball_count_base, ball_count_offsets, disp1_base, disp1_offsets, disp2_base, disp2_offsets,
        disp1_x, disp1_y, disp1_size, disp2_x, disp2_y, disp2_size,
        ball_count_x, ball_count_y, ball_count_size, dmd_enabled, backglass_enabled,
        ball_count_enabled, disp1_enabled, disp2_enabled,
        score_x, score_y
    ) = load_config()


    
    root = tk.Tk()
    root.overrideredirect(True)  # Removes title bar
    root.geometry(f"{dmd_width}x{dmd_height}+{dmd_x}+{dmd_y}")
    root.configure(bg='black')
    
    canvas = Canvas(root, width=dmd_width, height=dmd_height, highlightthickness=0, bd=0, bg='black')
    canvas.pack()
    
    if os.path.exists(dmd_bg):
        image = Image.open(dmd_bg).convert("RGBA")
        image = image.resize((dmd_width, dmd_height), Image.LANCZOS)
        
        black_bg = Image.new("RGBA", (dmd_width, dmd_height), (0, 0, 0, 255))
        image = Image.alpha_composite(black_bg, image)
        alpha_channel = image.split()[3].point(lambda p: int(p * (bg_alpha / 255)))
        image.putalpha(alpha_channel)
        
        bg_image = ImageTk.PhotoImage(image)
        canvas.create_image(0, 0, anchor="nw", image=bg_image)
        canvas.image = bg_image

    if backglass_enabled:
        wallpaper_window = create_backglass_window(back_x, back_y, back_width, back_height, backglass_bg, root)
    
    custom_font = font.Font(family=score_font, size=int(score_size))
    ball_count_font = font.Font(family=score_font, size=int(ball_count_size))
    disp2_font = font.Font(family=score_font, size=int(disp2_size))
    disp1_font = font.Font(family=score_font, size=int(disp1_size))

    global label_fg, label_disp1, label_disp2, label_ball_count
    label_fg = None
    label_ball_count = None
    label_disp1 = None
    label_disp2 = None

    
    label_fg = tk.Label(canvas, text="", fg=score_color, bg='black', font=custom_font)
    label_fg.place(relx=float(score_x) / 100, rely=float(score_y) / 100, anchor='center')
    
    label_ball_count = tk.Label(root, text="", fg=ball_count_color, bg='black', font=ball_count_font)
    if ball_count_enabled:
        label_ball_count.place(relx=float(ball_count_x) / 100, rely=float(ball_count_y) / 100, anchor='center')
    
    label_disp1 = tk.Label(root, text="", fg=disp1_color, bg='black', font=disp1_font)
    if disp1_enabled:
        label_disp1.place(relx=float(disp1_x) / 100, rely=float(disp1_y) / 100, anchor='center')

    label_disp2 = tk.Label(root, text="", fg=disp2_color, bg='black', font=disp2_font)
    if disp2_enabled:
        label_disp2.place(relx=float(disp2_x) / 100, rely=float(disp2_y) / 100, anchor='center')
    
    root.bind("<Escape>", lambda event: (root.destroy()))
    root.bind("<F5>", reload_config)
    
    threading.Thread(
    target=update_dmd,
    args=(
        process_name, score_address, score_offsets, module_name, module2_name, 
            disp1_base, disp1_offsets, disp2_base, disp2_offsets, 
            ball_count_base, ball_count_offsets, label_fg, label_ball_count, 
            label_disp1, label_disp2, root, ball_count_label, 
            disp1_label, disp2_label, disp1_x, disp1_y,
            disp1_size, disp2_x, disp2_y, disp2_size,
            ball_count_x, ball_count_y, ball_count_size, dmd_enabled,
            ball_count_enabled, disp1_enabled, disp2_enabled,
            score_x, score_y
    ),
    daemon=True
    ).start()



    root.mainloop()

def update_dmd(process_name, score_address, score_offsets, module_name, module2_name, 
               disp1_base, disp1_offsets, disp2_base, disp2_offsets, 
               ball_count_base, ball_count_offsets, label_fg, label_ball_count, 
               label_disp1, label_disp2, root, ball_count_label, 
               disp1_label, disp2_label, disp1_x, disp1_y,
               disp1_size, disp2_x, disp2_y, disp2_size,
               ball_count_x, ball_count_y, ball_count_size, dmd_enabled,
               ball_count_enabled, disp1_enabled, disp2_enabled,
               score_x, score_y):   
    """Continuously updates the DMD display and exits if XENOTILT.exe is closed."""
    
    global previous_ball_count  
    previous_ball_count = None  
    displaying_message = False  
    detected_once = False  # Track if the process was found at least once

    def restore_score():
        """Restores the score display after message delay."""
        nonlocal displaying_message
        displaying_message = False  
        score_value = read_memory_value(process_name, score_address, module_name, score_offsets)
        if score_value is not None:
            formatted_score = format_score(score_value)
            label_fg.config(text=formatted_score)

    while True:
        # Check if the process is running
        if is_process_running(process_name):
            detected_once = True  # Mark that the process has been seen at least once
        elif detected_once:
            print(f"Process {process_name} has closed. Exiting...")
            root.destroy()  # Close the Tkinter window
            sys.exit(0)  # Terminate the script

        # Read memory values
        score_value = read_memory_value(process_name, score_address, module_name, score_offsets)
        ball_count_value = read_memory_value(process_name, ball_count_base, module2_name, ball_count_offsets)
        disp1_value = read_memory_value(process_name, disp1_base, module2_name, disp1_offsets)
        disp2_value = read_memory_value(process_name, disp2_base, module_name, disp2_offsets)
        

 
        if score_value is None:
            label_fg.config(text="XENODMD READY")

        elif score_value is not None and not displaying_message:
            formatted_score = format_score(score_value)
            label_fg.config(text=formatted_score)

        if ball_count_enabled:
            if ball_count_value is not None:
                label_ball_count.config(text=f"{ball_count_label} {ball_count_value:02d}")

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

        if disp1_enabled and disp1_value is not None:
            label_disp1.config(text=f"{disp1_label} {disp1_value:02d}") 

        if disp2_enabled and disp2_value is not None:
            label_disp2.config(text=f"{disp2_label} {disp2_value:02d}")

        root.after(1, lambda: None)  
        time.sleep(0.5)


def format_score(value):
    """Formats the score with dots every three digits, ensuring it is always 12 digits long."""
    formatted_value = f"{value:013d}"
    return ".".join([formatted_value[max(i - 3, 0):i] for i in range(len(formatted_value), 0, -3)][::-1])


def read_memory_value(process_name, score_address, module_name, score_offsets):
    """Reads a memory value from a specific process, following the given base address and offsets."""
    try:
        pm = pymem.Pymem(process_name)
        module_base = pymem.process.module_from_name(pm.process_handle, module_name).lpBaseOfDll
        address = module_base + score_address
        for offset in score_offsets:
            address = pm.read_ulonglong(address)
            address += offset
        value = pm.read_ulonglong(address)
        return value
    except:
        return None
    
def is_process_running(process_name):
    """Check if a process is running by name."""
    for process in psutil.process_iter(attrs=['name']):
        if process.info['name'].lower() == process_name.lower():
            return True
    return False


def reload_config(event=None):
    """Reloads configuration values when the F5 key is pressed."""
    global config_values, label_fg, label_ball_count, label_disp1, label_disp2
    print("[INFO] Reloading config...")

    # Reload the configuration
    (
        dmd_width, dmd_height, dmd_x, dmd_y, score_size, dmd_bg, bg_alpha, score_font,
        back_x, back_y, back_width, back_height, backglass_bg,
        score_color, ball_count_label, ball_count_color, disp1_label, disp1_color, disp2_label, disp2_color,
        process_name, module_name, module2_name, score_address, score_offsets,
        ball_count_base, ball_count_offsets, disp1_base, disp1_offsets, disp2_base, disp2_offsets,
        disp1_x, disp1_y, disp1_size, disp2_x, disp2_y, disp2_size,
        ball_count_x, ball_count_y, ball_count_size,
        dmd_enabled, backglass_enabled, ball_count_enabled, disp1_enabled, disp2_enabled,
        score_x, score_y
    ) = load_config()

    # Update UI elements dynamically
    label_fg.config(fg=score_color, font=font.Font(family=score_font, size=int(score_size)))
    #divide score_x and score_y by 100 to get the relative position
    label_fg.place(relx=float(score_x) / 100, rely=float(score_y) / 100, anchor='center')
   
    
    if ball_count_enabled:
        label_ball_count.place(relx=float(ball_count_x) / 100, rely=float(ball_count_y) / 100, anchor='center')
        label_ball_count.config(fg=ball_count_color, text=f"{ball_count_label} 0",
                                font=font.Font(family=score_font, size=int(ball_count_size)))
    elif ball_count_enabled == False:
        label_ball_count.place_forget()
    
    if disp1_enabled:
        label_disp1.config(fg=disp1_color, text=f"{disp1_label} 00",
                       font=font.Font(family=score_font, size=int(disp1_size)))
        label_disp1.place(relx=float(disp1_x) / 100, rely=float(disp1_y) / 100, anchor='center')
    
    elif disp1_enabled == False:
        label_disp1.place_forget()

    if disp2_enabled:
        label_disp2.config(fg=disp2_color, text=f"{disp2_label} 00",
                        font=font.Font(family=score_font, size=int(disp2_size)))
        label_disp2.place(relx=float(disp2_x) / 100, rely=float(disp2_y) / 100, anchor='center')

    elif disp2_enabled == False:
        label_disp2.place_forget()
    

    print("[INFO] Config reloaded successfully.")

if __name__ == "__main__":
    
    BALL_COUNT_BASE = 0x01D21378
    BALL_COUNT_OFFSETS = [0x0, 0x58, 0x0, 0xC0, 0x28, 0x38, 0x670]
    
    DISP2_BASE = 0x00754850
    DISP2_OFFSETS = [0x198, 0x410, 0x850, 0x120, 0xB0]

    DISP1_BASE = 0x01D047E8
    DISP1_OFFSETS = [0xD0, 0x8, 0x68, 0x30, 0xB8, 0x2A0, 0x170]

    create_dmd()
