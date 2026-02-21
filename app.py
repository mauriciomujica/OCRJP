import threading
import keyboard
import tkinter as tk
#from tkinter import messagebox
from tkinter import ttk
import pystray
from PIL import Image, ImageGrab
from datetime import datetime

global screenshot_open
screenshot_open = False

def main():
    app = Application()
    app.mainloop()

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Japanese OCR")
        self.option_add("*tearOff", "FALSE")
        #style = ttk.Style()
        #self.call('lappend', 'auto_path', 'themes/ScidDarkTheme')
        #self.call('package', 'require', 'ttk-themes')
        #style.theme_use("sciddarkpurple")
        self.call("source", "themes/azure.tcl")
        self.call("set_theme", "dark")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.menubar = tk.Menu(self)
        menu_file = tk.Menu(self.menubar)
        menu_edit = tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=menu_file, label='File')
        self.menubar.add_cascade(menu=menu_edit, label='Edit')
        self.menubar.add_cascade(menu=menu_edit, label='Theme')
        self.menubar.add_cascade(menu=menu_edit, label='Dictionaries')
        self.menubar.add_cascade(menu=menu_edit, label='Help')
        self.menubar.add_cascade(menu=menu_edit, label='About')
        self['menu'] = self.menubar

        self.content = MainFrame(self)
        self.content.grid(row = 0, column= 0, sticky="nsew")
        self.content.grid_propagate(False)

        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - self.winfo_reqwidth()) // 2
        y = (screen_height - self.winfo_reqheight()) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.thread2 = None

    def minimize_to_tray(self):
        if self.thread2 and self.thread2.is_alive():
            self.withdraw()
        
        self.withdraw()
        image = Image.open("app.ico")
        menu = (pystray.MenuItem('Quit', self.quit_window), 
                pystray.MenuItem('Show',self.show_window))
        #icon = pystray.Icon("name", image, "My App", menu)
        thread= threading.Thread(daemon= True, target= lambda: pystray.Icon("name", image, "My App", menu).run())
        thread.start()
        
        #if screenshot_open:
        #    return messagebox.showinfo("Error", "A screenshot window is already opened.")

        if self.thread2 and self.thread2.is_alive():
            return
        
        self.thread2 = threading.Thread(daemon= True, target= self.screenshot)
        self.thread2.start()
    def screenshot(self):
        global screenshot_open
        keyboard.add_hotkey("ctrl+z", lambda: self.after(0, lambda: TakeScreenshot()) if not screenshot_open else None)
        keyboard.wait()

    def quit_window(self, icon):
        icon.stop()
        self.destroy()

    def show_window(self, icon):
        icon.stop()
        self.after(0, self.deiconify)
    

class MainFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, height= "200p", width= "400p")
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.button = ttk.Button(self, text="To tray", command= lambda:Application.minimize_to_tray(parent))
        self.button.grid(sticky="se")

class TakeScreenshot(tk.Toplevel):
    def __init__(self):
        global screenshot_open
        screenshot_open = True
        # TopLevel window where the canvas is going to be placed in
        
        super().__init__()
        self.attributes('-alpha', 0.5)
        self.attributes('-fullscreen', True)
        self.width = self.winfo_screenwidth()
        self.height = self.winfo_screenheight()
        self.protocol("WM_DELETE_WINDOW", self.quit)

        # Canvas creation

        self.canvas = tk.Canvas(self, width=self.width, height=self.height, cursor="cross", bg = "black")
        self.x = self.y = 0
        self.canvas.grid()
        self.canvas.bind("<ButtonPress-1>", self.start_pos)
        self.canvas.bind("<B1-Motion>", self.final_pos)
        self.canvas.bind("<ButtonRelease-1>", self.take_screenshot)
        self.rect = None
        self.start_x = None
        self.start_y = None

    def start_pos(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect = self.canvas.create_rectangle(self.x, self.y, 1, 1, fill="gray50")

    def final_pos(self, event):
        self.final_x, self.final_y = event.x, event.y
        # Draw the rectangle as you move the mouse
        self.canvas.coords(self.rect, self.start_x, self.start_y, self.final_x, self.final_y)

    def take_screenshot(self, event):
        global screenshot_open
        # Get date and time for filename

        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        str_current_datetime = str(current_datetime)

        # For the crop to work, both start_x and start_y need to be lower than final_x and final_y
        # Depending on how the user takes the screenshot, this is not always the case:
        # - Upper left to bottom right = ok
        # - Upper right to bottom left = error
        # - Bottom left to upper right = error
        # - Bottom right to upper left = error

        # Finding which coordinate is the minimum and maximum solves this

        self.xmin = min(self.start_x, self.final_x)
        self.xmax = max(self.start_x, self.final_x)
        self.ymin = min(self.start_y, self.final_y)
        self.ymax = max(self.start_y, self.final_y)

        self.img = ImageGrab.grab(bbox=(self.xmin, self.ymin, self.xmax, self.ymax))  # Take the screenshot

        self.destroy()
        screenshot_open = False

        self.img.save(f"tests/IMG_{str_current_datetime}.png")

    def quit(self):
        global screenshot_open
        screenshot_open = False
        self.destroy()

if __name__=="__main__":
    main()