import os

import pythoncom
import win32com
from flask import flash, redirect, url_for

import blackscreen
import static

ppt_path = static.FILE_PATH


class Controller:
    def start(self):
        """Startet eine PowerPoint-Präsentation im Vollbildmodus."""
        # Initialize COM at the start of the function
        pythoncom.CoInitialize()

        static.RUNNING = True

        try:
            if os.path.exists(ppt_path):
                ppt = win32com.client.Dispatch("PowerPoint.Application")
                ppt.Visible = True
                presentation = ppt.Presentations.Open(ppt_path)
                slide_show = presentation.SlideShowSettings
                slide_show.ShowWithAnimation = True
                slide_show.AdvanceMode = 2  # Automatische Folienumstellung
                slide_show.Run()  # Präsentation starten
                blackscreen.hide()
            else:
                print("upload.pptx wurde nicht gefunden")
        except Exception as e:
            print(f"Fehler beim Starten der Präsentation: {e}")
        finally:
            # Clean up COM initialization
            pythoncom.CoUninitialize()

    def end(self):
        """Beendet die PowerPoint-Präsentation."""
        # Initialize COM before interacting with PowerPoint
        pythoncom.CoInitialize()

        static.RUNNING = False

        try:
            blackscreen.show()
            ppt = win32com.client.Dispatch("PowerPoint.Application")
            ppt.Quit()
        except Exception as e:
            print(e)
            flash(f"Fehler: {e}", "error")
        finally:
            # Clean up COM initialization
            pythoncom.CoUninitialize()

    def change_slide(action):
        """Wechselt zur nächsten oder vorherigen Folie basierend auf der Aktion."""
        # Initialize COM before interacting with PowerPoint
        pythoncom.CoInitialize()

        try:
            ppt = win32com.client.Dispatch("PowerPoint.Application")
            if ppt.Presentations.Count > 0:
                presentation = ppt.Presentations.Item(1)
                slide_show_window = presentation.SlideShowWindow
                if slide_show_window:
                    if action == "next":
                        slide_show_window.View.Next()
                    elif action == "previous":
                        slide_show_window.View.Previous()
                else:
                    flash("Keine Präsentation wird derzeit angezeigt.", "error")
            else:
                flash("Keine Präsentation ist geöffnet.", "error")
        except Exception as e:
            flash(f"Fehler: {e}", "error")
        finally:
            # Clean up COM initialization
            pythoncom.CoUninitialize()
