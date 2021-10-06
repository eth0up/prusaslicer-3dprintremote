from flask import Flask, request, render_template
from models.view import View
from octorest import OctoRest
from os import path, remove, getcwd, system
from urllib.parse import urlparse
import glob
import re
import requests
import subprocess

app = Flask(__name__, static_url_path='', static_folder='static')

# Global Variables

FLASK_HOST = "0.0.0.0" # Server will be accessible on specified IP or hostname
FLASK_PORT = "5000" # Server will be accessible on this port
FLASK_DEBUG = False # Flask server debug mode

STLPATH = "STL" # Path to STL folder
ROOTPROFILESPATH = "PROFILES" # Path to Profiles folder

PRUSASLICERPATH = "C:\Program Files\Prusa3D\PrusaSlicer" # Path to prusa-slicer-console.exe and PrusaSlicer.dll
CURRENTPATH = getcwd()

OCTO_ENABLED = True # If enabled, we will connect to Octoprint server specified
# NOTE: If OCTO_ENABLED is True, sliced gcode files will be uploaded to Octoprint and then deleted from local disk.
OCTO_HOST = "https://192.168.XXX.XXX" # Octoprint address including http/https
OCTO_APIKEY = "1234567890ABCDEFGHIJKLMNOPQRSTUV" # Octoprint API key found in Settings -> Application Keys

# Controller functions

@app.route('/')
def downloadprint_form(): # "Home" tab
    view_model = View("index", "STL Fetch & Slice", description="Fetch, Slice, Upload, and Print", bag={'startprint': True, 'profiles': get_profiles(), 'OCTO_ENABLED': OCTO_ENABLED})

    return render_template('index.html', model=view_model)

@app.route('/', methods=['POST']) # "Home" tab POST handling
def downloadprint_form_post():
    startprint = False if request.form.get('startprint') is None else True
    url = request.form['url']
    profile = request.form['profile']
    
    if not profile:
        view_model = View("index", "STL Fetch & Slice", "Fetch, Slice, Upload, and Print", '',
                        {'startprint': startprint, 'url': url, 'profile': profile, 'profiles': get_profiles(), 'OCTO_ENABLED': OCTO_ENABLED}, 'Error: Invalid form data')

    if not is_url(url):
        view_model = View("index", "STL Fetch & Slice", "Fetch, Slice, Upload, and Print", '',
                        {'startprint': startprint, 'url': url, 'profile': profile, 'profiles': get_profiles(), 'OCTO_ENABLED': OCTO_ENABLED}, 'Error: Invalid URL')

        return render_template('index.html', model=view_model)
        
    uri = urlparse(url)
    filename = path.basename(uri.path)

    if not filename:
        view_model = View("index", "STL Fetch & Slice", "Fetch, Slice, Upload, and Print", '',
                        {'startprint': startprint, 'url': url, 'profile': profile, 'profiles': get_profiles(), 'OCTO_ENABLED': OCTO_ENABLED}, 'Error: Could not determine filename from the provided URL')

        return render_template('index.html', model=view_model)

    stl_file = download_stl(url, f'{STLPATH}\{filename}')
           
    gcode_fullpath, completed_process = send_stl_to_slicer(stl_file, profile)

    if gcode_fullpath is None:
        view_model = View("index", "STL Fetch & Slice", "Fetch, Slice, Upload, and Print", '',
                            {'startprint': startprint, 'url': url, 'profile': profile, 'profiles': get_profiles(), 'OCTO_ENABLED': OCTO_ENABLED}, 'Slicer Error: Gcode filename detection failed. Confirm that the source is a functional STL file.')
                            
        return render_template('index.html', model=view_model)
        
    if completed_process.returncode != 0:
        view_model = View("index", "STL Fetch & Slice", "Fetch, Slice, Upload, and Print", '',
                            {'startprint': startprint, 'url': url, 'profile': profile, 'profiles': get_profiles(), 'OCTO_ENABLED': OCTO_ENABLED}, error = f'Slicer Error: STL slicing failed. {completed_process.stdout.decode("ascii")}... {completed_process.stderr.decode("ascii")}')
                            
        return render_template('index.html', model=view_model)
        
    if OCTO_ENABLED: # Only send sliced gcode to Octoprint when Global var is True
        try:
            octoprint_status = send_gcode_to_octoprint(gcode_fullpath, startprint)
        except Exception as e:
            view_model = View("index", "STL Fetch & Slice", "Fetch, Slice, Upload, and Print", '',
                                {'startprint': startprint, 'url': url, 'profile': profile, 'profiles': get_profiles(), 'OCTO_ENABLED': OCTO_ENABLED}, f'Octoprint Exception: {type(e)}: {e}')
        else:
            view_model = View("index", "STL Fetch & Slice", "Fetch, Slice, Upload, and Print", f'Octoprint Response: {octoprint_status}',
                                {'startprint': startprint, 'url': url, 'profile': profile, 'profiles': get_profiles(), 'OCTO_ENABLED': OCTO_ENABLED}, '')    
        
        cleanup_gcode(gcode_fullpath) # Delete the gcode file
    else:
        view_model = View("index", "STL Fetch & Slice", "Fetch, Slice, Upload, and Print", f'Sliced {filename} to: {gcode_fullpath}',
                            {'startprint': startprint, 'url': url, 'profile': profile, 'profiles': get_profiles(), 'OCTO_ENABLED': OCTO_ENABLED}, '')        
    
    return render_template('index.html', model=view_model)
    
@app.route('/profiles') # "Profiles" tab
def profiles_form():
    view_model = View("profiles", "Slicer Profiles", "Available Profiles", bag={'profiles': get_profiles(), 'OCTO_ENABLED': OCTO_ENABLED})
    return render_template('profiles.html', model=view_model)

@app.route('/stls') # "Archived STL Printer" tab
def stls_form():
    view_model = View("stls", "Archived STL Printer", "Slice previously-downloaded STLs, Upload, and Print", bag={'stls': get_stls(), 'startprint': True, 'profiles': get_profiles(), 'OCTO_ENABLED': OCTO_ENABLED})
    return render_template('stls.html', model=view_model)
    
@app.route('/stls', methods=['POST']) # "Archived STL Printer" tab POST handling
def stlprint_form_post():
    startprint = False if request.form.get('startprint') is None else True
    stl = request.form['stl']
    profile = request.form['profile']
   
    # validate form input
    if not stl or not profile:
        view_model = View("stls", "Archived STL Printer", "Slice previously-downloaded STLs, Upload, and Print", '',
                            {'stl': stl, 'stls': get_stls(), 'profile': profile, 'profiles': get_profiles(), 'OCTO_ENABLED': OCTO_ENABLED}, "Error: Invalid form data")
        
        return render_template('stls.html', model=view_model)

    if not path.isfile(stl):
        view_model = View("stls", "Archived STL Printer", "Slice previously-downloaded STLs, Upload, and Print", '',
                            {'stl': stl, 'stls': get_stls(), 'profile': profile, 'profiles': get_profiles(), 'OCTO_ENABLED': OCTO_ENABLED}, f'Error: {stl} not found in STL directory')
        
        return render_template('stls.html', model=view_model)
        
    stl_file = stl

    gcode_fullpath, completed_process = send_stl_to_slicer(stl_file, profile)

    if gcode_fullpath is None:
        view_model = View("stls", "Archived STL Printer", "Slice previously-downloaded STLs, Upload, and Print", '',
                            {'startprint': startprint, 'stl': stl, 'stls': get_stls(), 'profile': profile, 'profiles': get_profiles(), 'OCTO_ENABLED': OCTO_ENABLED}, error = 'Slicer Error: Gcode filename detection failed. Confirm that the source is a functional STL file.')

        return render_template('stls.html', model=view_model)
    
    if completed_process.returncode != 0:
        view_model = View("stls", "Archived STL Printer", "Slice previously-downloaded STLs, Upload, and Print", '',
                            {'startprint': startprint, 'stl': stl, 'stls': get_stls(), 'profile': profile, 'profiles': get_profiles(), 'OCTO_ENABLED': OCTO_ENABLED}, error = f'Error: STL slicing failed! {completed_process.stdout.decode("ascii")}... {completed_process.stderr.decode("ascii")}')

        return render_template('stls.html', model=view_model)

    if OCTO_ENABLED: # Only send sliced gcode to Octoprint when Global var is True
        try:
            octoprint_status = send_gcode_to_octoprint(gcode_fullpath, startprint)
        except Exception as e:
            view_model = View("stls", "Archived STL Printer", "Slice previously-downloaded STLs, Upload, and Print", '',
                                {'startprint': startprint, 'stl': stl, 'stls': get_stls(), 'profile': profile, 'profiles': get_profiles(), 'OCTO_ENABLED': OCTO_ENABLED}, f'Octoprint Exception: {type(e)}: {e}')
        else:
            view_model = View("stls", "Archived STL Printer", "Slice previously-downloaded STLs, Upload, and Print",
                                f'Octoprint Response: {octoprint_status}', {'startprint': startprint, 'stl': stl, 'stls': get_stls(), 'profile': profile, 'profiles': get_profiles(), 'OCTO_ENABLED': OCTO_ENABLED}, '')
        
        cleanup_gcode(gcode_fullpath) # Delete the gcode file
    else:
        view_model = View("stls", "Archived STL Printer", "Slice previously-downloaded STLs, Upload, and Print",
                            f'Sliced {filename} to: {gcode_fullpath}', {'startprint': startprint, 'stl': stl, 'stls': get_stls(), 'profile': profile, 'profiles': get_profiles(), 'OCTO_ENABLED': OCTO_ENABLED}, '')

    return render_template('stls.html', model=view_model)
    
# Helper functions

def download_stl(url, filename):
# Download the STL file to the STL directory
    r = requests.get(url)
    with open(filename, 'wb') as f:
        f.write(r.content)

    return f.name

def send_stl_to_slicer(stl_file, profile):
# Slice the STL and extract the resultant path from the slicer output
    command = f'"{PRUSASLICERPATH}\prusa-slicer-console.exe" --gcode --load "{CURRENTPATH}\{profile}" "{CURRENTPATH}\{stl_file}"'
    completed_process = subprocess.run(command, shell=True, capture_output=True)
    gcode_fullpath = get_gcode_fullpath_from_prusa_slicer_output(completed_process.stdout.decode("utf-8"))

    return gcode_fullpath, completed_process

def get_gcode_fullpath_from_prusa_slicer_output(slicer_output):
# Extract the gcode path from the slicer output
    pattern = r"[a-zA-Z]:\\([a-zA-Z0-9() ]*\\)*\w*.*\w*.gcode" #full path
    match = re.search(pattern, slicer_output)
    if match is None:
        return
    return match.group()

def send_gcode_to_octoprint(gcode_fullpath, startprint):
# Using the OctoRest-generated Octoprint client, upload the gcode to Octoprint server
# 'startprint' bool is determined by the "Start printing after upload" switch in UI
    with open(gcode_fullpath, 'rb') as f:
        gcode_tuple = (path.basename(gcode_fullpath), f)
        try:
            client = make_octoprint_client(OCTO_HOST, OCTO_APIKEY)
        except Exception as e:
            raise e
        upload_process = client.upload(gcode_tuple, print=startprint)
        # NOTE: If you are NOT using the OctoRest branch specified in requirements.txt, print=True will fail here..
        # ..as a workaround, uncomment the 'client.select..' line below. This won't be necessary after OctoRest Release >0.4.
        #client.select(path.basename(gcode_fullpath), print=startprint)
    return upload_process
    
def make_octoprint_client(octoprintHost, octoprintApiKey):
# Create an Octoprint client using OctoRest module
    try:
        client = OctoRest(url=octoprintHost, apikey=octoprintApiKey)
        return client
    except Exception as e:
        raise e

def is_url(url):
  try:
    result = urlparse(url)
    return all([result.scheme, result.netloc])
  except ValueError:
    return False
    
def cleanup_gcode(filename):
# Delete gcode file that was generated by send_stl_to_slicer()
    remove(filename)
    
def get_stls():
# Get list of STLs for display/selection on "Archived STL Printer" tab
    return glob.glob(f'{STLPATH}/*.stl', recursive=False)

def get_profiles():
# Get list of profiles for display/selection within each tab
    return glob.glob(f'{ROOTPROFILESPATH}/*.ini', recursive=False)

app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
