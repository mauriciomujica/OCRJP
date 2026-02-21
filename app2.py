import threading
import keyboard
import pystray
import tkinter as tk
#from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageGrab
from datetime import datetime
from json import load
from queue import Queue

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

        #self.test = TopLevelOCR()

        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - self.winfo_reqwidth()) // 2
        y = (screen_height - self.winfo_reqheight()) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        self.thread2 = None
        self.thread3 = None
        self.open_ocr_pending = False
        self.filename = Queue()

    def minimize_to_tray(self):
        if self.thread2 and self.thread2.is_alive():
            self.withdraw()
        
        self.withdraw()
        image = Image.open("app.ico")
        menu = (pystray.MenuItem('Quit', self.quit_window), 
                pystray.MenuItem('Show',self.show_window))
        thread= threading.Thread(daemon= True, target= lambda: pystray.Icon("name", image, "My App", menu).run())
        thread.start()
        
        #if screenshot_open:
        #    return messagebox.showinfo("Error", "A screenshot window is already opened.")

        if self.thread2 and self.thread2.is_alive():
            return
        
        self.screenshot_taken_event = threading.Event()

        self.thread2 = threading.Thread(daemon= True, target=lambda: self.screenshot(self.screenshot_taken_event, self.filename))
        self.thread2.start()

        self.thread3 = threading.Thread(daemon= True, target=lambda: self.ocr(self.screenshot_taken_event))
        self.thread3.start()

        self.after(100, self.check_open_ocr)

    def screenshot(self, event, filename):
        global screenshot_open
        keyboard.add_hotkey("ctrl+z", lambda: self.after(0, lambda: TakeScreenshot(event, filename)) if not screenshot_open else None)
        keyboard.wait()

    def ocr(self, event):
        while True:
            event.wait()
            self.open_ocr_pending = True
            event.clear()

    def check_open_ocr(self):
        if self.open_ocr_pending and not self.filename.empty():
            filename = self.filename.get()
            TopLevelOCR(filename)
            self.open_ocr_pending = False
        self.after(100, self.check_open_ocr)

    def quit_window(self, icon):
        icon.stop()
        self.destroy()

    def show_window(self, icon):
        icon.stop()
        self.after(0, self.deiconify)
    

class MainFrame(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, height= "200p", width= "400p", padding= 5)
        
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.button = ttk.Button(self, text="To tray", command= lambda:Application.minimize_to_tray(parent))
        self.button.grid(sticky="se")

class TakeScreenshot(tk.Toplevel):
    def __init__(self, event, filename):
        global screenshot_open
        screenshot_open = True
        # TopLevel window where the canvas is going to be placed in
        
        super().__init__()
        self.attributes('-alpha', 0.5)
        self.attributes('-fullscreen', True)
        self.width = self.winfo_screenwidth()
        self.height = self.winfo_screenheight()
        self.protocol("WM_DELETE_WINDOW", self.exit)
        self.event = event
        self.filename = filename

        self.canvas = ScreenshotCanvas(self, self.width, self.height, cursor = "cross", bg= "black", event= self.event, filename = self.filename)
        self.canvas.grid()

    def exit(self):
        global screenshot_open
        screenshot_open = False
        self.destroy()

class ScreenshotCanvas(tk.Canvas):
    def __init__(self, parent, width, height, cursor, bg, event, filename):

        super().__init__(parent, width=width, height=height, cursor=cursor, bg=bg)

        self.parent = parent
        self.x = self.y = 0
        self.bind("<ButtonPress-1>", self.start_pos)
        self.bind("<B1-Motion>", self.final_pos)
        self.bind("<ButtonRelease-1>", self.take_screenshot)
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.event_thread = event
        self.filename = filename

    def start_pos(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect = self.create_rectangle(self.x, self.y, 1, 1, fill="gray50")

    def final_pos(self, event):
        self.final_x, self.final_y = event.x, event.y
        # Draw the rectangle as you move the mouse
        self.coords(self.rect, self.start_x, self.start_y, self.final_x, self.final_y)

    def take_screenshot(self, event):
        global screenshot_open

        self.current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.str_current_datetime = str(self.current_datetime)
        self.filename.put(self.str_current_datetime)

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

        self.parent.destroy()

        screenshot_open = False
        self.img.save(f"tests/IMG_{self.str_current_datetime}.png")

        self.event_thread.set()


    # def exit(self):
    #      global screenshot_open
    #      screenshot_open = False
    #      self.parent.destroy()

class TopLevelOCR(tk.Toplevel):
    def __init__(self, filename):
        super().__init__()
        self.title("OCR")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.filename = filename

        self.ocrframe = FrameOCR(self, filename)
        self.ocrframe.grid()
        self.ocrframe.columnconfigure(0, weight=1)
        self.ocrframe.rowconfigure(0, weight=1)


class FrameOCR(ttk.Frame):
    def __init__(self, parent, filename):
        super().__init__(parent)
        self.img_path = f"tests/IMG_{filename}.png"

        self.jp_text = tk.StringVar()
        self.txt = tk.Text(self, font= ("Noto Sans JP", 20), width= 20, height=5, wrap= 'word')
        self.ocr_test = self.ocr_scan(self.img_path)
        self.load_json(filename)

        #ttk.Entry(self, textvariable=self.jp_text, state="readonly", font=("Noto Sans JP", 20)).grid(sticky=("w, e"))
        #self.txt = tk.Text(self, state="disabled", font= ("Noto Sans JP", 20)).grid(sticky=("w, e"))
        self.txt['state'] = 'disabled'
        self.txt.grid(sticky=("w, e"))

    def ocr_scan(self, img_path):
        from paddleocr import TextRecognition
        # ocr = PaddleOCR(use_doc_orientation_classify=False,
        # use_doc_unwarping=False, use_textline_orientation=False)
        # result = ocr.predict(input= img_path)
        model = TextRecognition(model_name = "PP-OCRv5_server_rec")
        output = model.predict(input=img_path, batch_size=1)
        for res in output:
            res.save_to_json("output")

    def load_json(self, filename):
        path = f"output/IMG_{filename}_res.json"
        with open(path, mode="r", encoding="utf-8") as f:
            data = load(f)
        ocr_text = data['rec_text']
        self.jp_text.set(ocr_text)
        self.txt.insert('1.0', ocr_text)



        




# class DisplayOCR(tk.Toplevel):
#     def __init__(self):

#         self.title("OCR")
#         #style = ttk.Style()
#         #style.configure("custom.TFrame", foreground="white", background="black")
#         #style.configure("custom.TEntry", foreground="black", background="white")

#         mainframe = ttk.Frame(root, style= "custom.TFrame", padding=(3, 3, 12, 12))
#         mainframe.grid(column=0, row=0)

#         self.jp_text = tk.StringVar()
#         ttk.Entry(mainframe, style="custom.TEntry", textvariable=self.jp_text, state="readonly", font=("Noto Sans JP", 20)).grid(sticky=(W, E))

#         root.columnconfigure(0, weight=1)
#         root.rowconfigure(0, weight=1)	
#         mainframe.columnconfigure(2, weight=1)
#         for child in mainframe.winfo_children(): 
#             child.grid_configure(padx=5, pady=5)

#     def loadjson(self, path):
#         with open(path, mode="r", encoding="utf-8") as f:
#             data = load(f)
#         ocr_text = data['rec_texts']
#         self.jp_text.set(ocr_text)


if __name__=="__main__":
    main()