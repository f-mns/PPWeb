import threading
import tkinter as tk

import static  # Ensure this module defines `BLACKSCREEN`

_black_screen_thread = None
_black_screen_root = None

def _on_escape(event=None):
    hide()

def _run_black_screen():
    global _black_screen_root
    _black_screen_root = tk.Tk()
    _black_screen_root.attributes('-fullscreen', True)
    _black_screen_root.configure(background='black')
    _black_screen_root.attributes('-topmost', True)
    _black_screen_root.protocol("WM_DELETE_WINDOW", lambda: None)
    _black_screen_root.bind('<Escape>', _on_escape)
    _black_screen_root.mainloop()

def show():
    global _black_screen_thread
    if _black_screen_thread is None or not _black_screen_thread.is_alive():
        _black_screen_thread = threading.Thread(target=_run_black_screen, daemon=True)
        static.BLACKSCREEN = True
        _black_screen_thread.start()

def hide():
    global _black_screen_root
    if _black_screen_root:
        _black_screen_root.destroy()
        _black_screen_root = None
        static.BLACKSCREEN = False
