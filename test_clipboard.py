import pystray
import tkinter as tk
import threading
from tkinter import ttk
from PIL import Image, ImageGrab
from json import load
from datetime import datetime
import copykitten

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

        self.img = None
    def minimize_to_tray(self):
        self.withdraw()
        image = Image.open("app.ico")
        menu = (pystray.MenuItem('Quit', self.quit_window), 
                pystray.MenuItem('Show',self.show_window))
        thread= threading.Thread(daemon= True, target= lambda: pystray.Icon("name", image, "My App", menu).run())
        thread.start()

        copykitten.clear()

        thread2 = threading.Thread(daemon=True, target= self.ocr_model)
        thread2.start()
        
        self.after(1000, self.check_img)

    def ocr_model(self):
        from paddleocr import TextRecognition

        self.model = TextRecognition(model_name = "PP-OCRv5_server_rec")


    def check_img(self):
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            #img.show()
            self.save_img(img)
            copykitten.clear()

        self.after(1000, self.check_img)

    def save_img(self, img):
        current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
        str_current_datetime = str(current_datetime)

        path = f"test_clip/IMG_{str_current_datetime}.png"
        json_path = f"output/IMG_{str_current_datetime}_res.json"
        img.save(f"{path}")
        self.scan_ocr(path)
        TopLevelOCR(json_path)

    def scan_ocr(self, path):
        if self.model is None:
            raise RuntimeError("OCR model not loaded yet")
        output = self.model.predict(input=path, batch_size=1)
        for res in output:
            res.save_to_json("output")
        


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


class TopLevelOCR(tk.Toplevel):
    def __init__(self, path):
        super().__init__()
        self.title("OCR")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.ocrframe = FrameOCR(self, path)
        self.ocrframe.grid(row= 0, column=0, sticky="nsew")
        #self.ocrframe.columnconfigure(0, weight=1)
        #self.ocrframe.rowconfigure(0, weight=1)


class FrameOCR(ttk.Frame):
    def __init__(self, parent, path):
        super().__init__(parent)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.jp_text = tk.StringVar()
        self.txt = tk.Text(self, font= ("Noto Sans JP", 20), width= 20, height=5, wrap= 'word')
        self.load_json(path)

        #ttk.Entry(self, textvariable=self.jp_text, state="readonly", font=("Noto Sans JP", 20)).grid(sticky=("w, e"))
        #self.txt = tk.Text(self, state="disabled", font= ("Noto Sans JP", 20)).grid(sticky=("w, e"))
        self.txt['state'] = 'disabled'
        self.txt.grid(sticky=("w, e"))

        self.selected_text()
    def selected_text(self):
        ranges = self.txt.tag_ranges(tk.SEL)
        if ranges:
            print('SELECTED Text is %r' % self.txt.get(*ranges))
        else:
            print('NO Selected Text')
        self.after(1000, self.selected_text)
        

    def load_json(self, path):
        with open(path, mode="r", encoding="utf-8") as f:
            data = load(f)
        ocr_text = data['rec_text']
        self.jp_text.set(ocr_text)
        self.txt.insert('1.0', ocr_text)

if __name__ == "__main__":
    main()
