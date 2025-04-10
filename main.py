# ----------------------
#        Imports
# ----------------------
import json
import os
import time
from io import BytesIO

import pythoncom
from flask import Flask, request, render_template, redirect, url_for, session, send_file, flash
import pyautogui
import win32com.client
from win32comext.shell import shellcon, shell
from functools import wraps

from control import Controller
import static
import blackscreen

# Initialize the presentation controller
c = Controller()

# ----------------------
#      Flask Setup
# ----------------------
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate a random secret key for sessions

# Load upload paths from static config
print("Upload folder path:", static.UPLOAD_FOLDER)
print("Upload file path:", static.FILE_PATH)

# Ensure upload folder exists
os.makedirs(static.UPLOAD_FOLDER, exist_ok=True)


# ----------------------
#     Auth Decorator
# ----------------------
def login_required(f):
    """Decorator that ensures a user is authenticated before accessing a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ----------------------
#         Routes
# ----------------------

# Home route, redirects to /control
@app.route('/')
@login_required
def index():
    return render_template('index.html')


# ----------------------
#        UI Routes
# ----------------------

@app.route('/control')
@login_required
def control():
    """Main control panel for the presentation."""
    return render_template('control.html', version=static.VERSION, name=static.INSTANCE_NAME)

@app.route('/config')
@login_required
def config():
    """Configuration panel."""
    return render_template('config.html', name=static.INSTANCE_NAME, version=static.VERSION)

@app.route('/system')
@login_required
def system():
    """System settings panel."""
    return render_template('system.html', name=static.INSTANCE_NAME, version=static.VERSION, config=config)

@app.route('/view-only')
def viewonly():
    """View-only route for observers."""
    if static.VIEW_ONLY_HIDDEN:
        return "View-Only has been disabled in the config."
    return render_template('view-only.html')

@app.route('/resetpassword')
def resetpassword():
    return render_template('resetpassword.html', config=config)


# ----------------------
#      Auth Routes
# ----------------------

@app.route('/logout')
@login_required
def logout():
    """Logout route to clear session."""
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login route with password authentication."""
    if request.method == 'POST':
        password = request.form['password']
        if password == static.LOGIN_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            flash("Wrong password. Please try again.", "error")
    return render_template('login.html', name=static.INSTANCE_NAME, vo=static.VIEW_ONLY_HIDDEN, config=config)


# ----------------------
#  PowerPoint Controls
# ----------------------

@app.route('/return')
@login_required
def return_slide():
    """Go back one slide."""
    Controller.change_slide("previous")
    return redirect(url_for('control'))

@app.route('/skip')
@login_required
def skip_slide():
    """Advance to the next slide."""
    Controller.change_slide("next")
    return redirect(url_for('control'))

@app.route('/end')
@login_required
def end_route():
    """End the PowerPoint presentation."""
    c.end()
    return redirect(url_for('control'))

@app.route('/start')
@login_required
def start_presentation_route():
    """Start the PowerPoint presentation."""
    try:
        c.start()
    except Exception as e:
        flash(f"Error starting presentation: {e}", "error")
    return redirect(url_for('control'))

@app.route('/restart')
@login_required
def restart():
    """Restart the presentation."""
    try:
        c.end()
        c.start()
    except Exception as e:
        print("error: " + e)
    return redirect(url_for('control'))


# ----------------------
#   Black Screen (Pause)
# ----------------------

@app.route('/pause')
@login_required
def pause_route():
    """Pause (black screen) the presentation."""
    blackscreen.show()
    return redirect(url_for('control'))

@app.route('/resume')
@login_required
def pause():
    """Resume the presentation from pause."""
    blackscreen.hide()
    return redirect(url_for('control'))


# ----------------------
#    Information APIs
# ----------------------

@app.route('/screen')
def capture_screenshot():
    """Capture and return a screenshot as PNG."""
    screenshot_img = pyautogui.screenshot()
    img_bytes = BytesIO()
    screenshot_img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return send_file(img_bytes, mimetype='image/png')

@app.route('/slide_info')
def slide_info():
    """Return current slide number and total slides."""
    pythoncom.CoInitialize()
    try:
        ppt = win32com.client.Dispatch("PowerPoint.Application")
        if ppt.Presentations.Count > 0:
            presentation = ppt.Presentations.Item(1)
            total_slides = presentation.Slides.Count
            current_slide = presentation.SlideShowWindow.View.Slide.SlideIndex
            return {"total_slides": total_slides, "current_slide": current_slide}
        return {"total_slides": 0, "current_slide": 0}
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        pythoncom.CoUninitialize()


@app.route('/download')
def download():
    """Allow downloading the current presentation file."""
    if config.get("VIEW_ONLY", {}).get("download", False) or 'authenticated' in session:
        return send_file(static.FILE_PATH, as_attachment=True)
    flash("You must be logged in to download the file.")
    return redirect(url_for('login'))

@app.route('/status')
def presentation_status():
    """Check if a presentation is running."""
    return {"running": static.RUNNING}


# ----------------------
#      File Upload
# ----------------------

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Upload a new PowerPoint file and optionally restart the presentation."""
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    if file.filename == "":
        flash("Please select a file to upload.", "error")
        return redirect(request.url)

    if not file.filename.endswith(".pptx"):
        flash("Invalid file format. Please upload a .pptx file.", "error")
        return redirect(request.url)

    restart = request.form.get('restart', 'false').lower() == 'true'

    try:
        c.end()
        file.save(static.FILE_PATH)
        time.sleep(1)  # Small delay to ensure the file is written to disk
        if restart:
            c.start()
        flash("File uploaded successfully!", "success")
        return redirect(url_for('config'))
    except Exception as e:
        flash(f"File processing failed: {e}", "error")
        return e
    finally:
        pythoncom.CoUninitialize()  # Uninitialize COM resources



# ----------------------
#  System Control Routes
# ----------------------

@app.route('/shutdown')
@login_required
def shutdown():
    """Shutdown the host system."""
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    shutdown_message = f"User {user_ip} has initiated system shutdown"
    os.system(f'shutdown -s -t 60 -c "{shutdown_message}"')
    return render_template('shutdown.html')

@app.route('/reboot')
@login_required
def reboot():
    """Reboot the host system."""
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    shutdown_message = f"User {user_ip} has initiated a reboot"
    os.system(f'shutdown -r -t 10 -c "{shutdown_message}"')
    return "System is rebooting..."

@app.route('/cancelshutdown')
@login_required
def cancelshutdown():
    """Cancel scheduled shutdown."""
    os.system('shutdown -a')
    return redirect(url_for('control'))


# ----------------------
#  Configuration Routes
# ----------------------

from static import config  # import configuration dictionary

@app.route('/pushconfig', methods=['POST'])
@login_required
def edit_config():
    """Update system configuration from the form."""
    config['HOST'] = request.form.get('HOST', config['HOST'])
    config['PORT'] = int(request.form.get('PORT', config['PORT']))
    config['DEBUG_MODE'] = 'DEBUG_MODE' in request.form
    config['INSTANCE_NAME'] = request.form.get('INSTANCE_NAME', config['INSTANCE_NAME'])
    config['VIEW_ONLY']['hidden'] = 'VIEW_ONLY_hidden' in request.form
    config['VIEW_ONLY']['download'] = 'VIEW_ONLY_download' in request.form

    with open(static.CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

    flash("Configuration saved!")
    static.reload_config()

    return redirect(url_for('system'))

@app.route('/change-password', methods=['POST'])
def changepassword():
    """Change the user login password."""
    old_password = request.form.get('OLD_PASSWORD')
    new_password = request.form.get('NEW_PASSWORD')

    if old_password != config['LOGIN_PASSWORD']: # Check if old password is correct
        print("Old password is incorrect.")
        return redirect(url_for('system'))

    if new_password != request.form.get('CONFIRM_NEW_PASSWORD'): # Check if the password confirm matches
        print("New passwords do not match.", "error")
        return redirect(url_for('system'))

    config['LOGIN_PASSWORD'] = new_password # Set new Password
    with open(static.CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

    print("Password changed successfully!", "success")
    static.reload_config()
    return redirect(url_for('system'))

@app.route('/admin-change-password', methods=['POST'])
def adminchangepassword():
    """Change the user login password."""
    admin_password = request.form.get('ADMIN_PASSWORD')
    new_password = request.form.get('NEW_PASSWORD')

    if admin_password != config['ADMIN_PASSWORD']: # Check if old password is correct
        print("Admin password is incorrect.")
        return redirect(url_for('system'))


    config['LOGIN_PASSWORD'] = new_password # Set new Password
    with open(static.CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

    print("Password changed successfully!", "success")
    static.reload_config()
    return redirect(url_for('system'))




# ----------------------
#     Main Entrypoint
# ----------------------

if __name__ == '__main__':
    c.start()  # Auto-start presentation on app launch
    app.run(debug=static.DEBUG_MODE, host=static.HOST, port=static.PORT, ssl_context='adhoc') # Dummy SSL Certificate
