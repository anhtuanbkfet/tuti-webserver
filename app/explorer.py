from flask import Flask, Blueprint, make_response, request, session, render_template, send_file, Response, redirect, url_for
from flask.views import MethodView
from werkzeug import secure_filename
from datetime import datetime
import os
import humanize
import re
import stat
import json
import mimetypes
import sys
from pathlib2 import Path
from app import app, basedir
from flask_login import login_required, current_user

from PIL import Image, ImageOps
from io import BytesIO
import base64
import piexif
from flask_fontawesome import FontAwesome
from flask_dropzone import Dropzone


fa = FontAwesome(app)
image_types = ['.jpg', '.jpeg', '.png', '.mp4'] #images with preview


# Dropzone settings (it can be overwriting with HTML/JS)
app.config.update(
    DROPZONE_ALLOWED_FILE_TYPE='image',
    DROPZONE_MAX_FILE_SIZE=10,
    DROPZONE_MAX_FILES=50,
    DROPZONE_PARALLEL_UPLOADS=3,  # set parallel amount
    DROPZONE_UPLOAD_MULTIPLE=True,  # enable upload multiple
)

dropzone = Dropzone(app)
image_types = ['.jpg', '.jpeg', '.png', '.mp4'] #images with preview
rootDir = os.path.join(basedir, 'data')
explorer = Blueprint('explorer', __name__)


def image_preview(img_path):
    """ Load image, make preview with corrected exif orientation
    """
    img = Image.open(img_path)
    t_size = 256, 256

    try:
        if "exif" in img.info:
            exif_dict = piexif.load(img.info["exif"])
            if piexif.ImageIFD.Orientation in exif_dict["0th"]:
                orientation = exif_dict["0th"].pop(piexif.ImageIFD.Orientation)
                #exif_bytes = piexif.dump(exif_dict)
                if orientation == 2:
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 3:
                    img = img.rotate(180)
                elif orientation == 4:
                    img = img.rotate(180).transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 5:
                    img = img.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 6:
                    img = img.rotate(-90, expand=True)
                elif orientation == 7:
                    img = img.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
    except:
        print('exif data problem in', img_path)

    new_image = Image.new(img.mode, t_size,  color=(255,255,255))
    img.thumbnail(t_size, Image.ANTIALIAS) # in-place
    x_offset= (new_image.size[0] - img.size[0]) // 2
    y_offset= (new_image.size[1] - img.size[1]) // 2
    new_image.paste(img, (x_offset, y_offset))
    img = new_image

    # in memory image -> bytes -> base64_string
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_preview = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return img_preview


def get_dir_and_file_list(path):
    """ Get list of directories and files in 'path' directory exclude hidden elements
        for image_types make a preview
    """
    dList = os.listdir(path)
    dirList = []
    fileList = []

    for item in dList:
        
        if os.path.isdir(os.path.join(path, item)):
            dirList.append(item)
        elif os.path.isfile(os.path.join(path, item)):
            if any(image_type in item.lower() for image_type in image_types):
                preview = image_preview(os.path.join(path, item))
                fileList.append((item, preview))
            else:
                fileList.append((item, None))

    return dirList, fileList


@explorer.route('/expr')
@explorer.route('/expr/<path:subpath>')
def show_directory(subpath=''):

    if subpath.startswith('%'):
        subpath = subpath[1:]    
    subpath = subpath.replace('%', '/')

    abs_folder_path = os.path.join(rootDir, subpath)

    # Invalid Directory
    if not os.path.isdir(abs_folder_path):
        print("Directory Doesn't Exist", abs_folder_path)
        return render_template('404.html')

    try:
        dirList, fileList = get_dir_and_file_list(abs_folder_path)
    except:
        return render_template('404.html')
    print(f'prview directory: {subpath}')
    return render_template('explorer.html',
                            dirList=dirList,
                            fileList=fileList,
                            currentDir=subpath)

    

@explorer.route('/view/<path:subpath>')
def view_file(subpath):
    
    if subpath.startswith('%'):
        subpath = subpath[1:]   
    subpath = subpath.replace('%', '/')

    filePath = os.path.join(rootDir, subpath)
    fileName = subpath.split('/')[-1]
    print(f'prview image: {filePath}')
    return send_file(filePath, attachment_filename=fileName)
    try:
        return send_file(filePath, attachment_filename=fileName)
    except:
        return render_template('404.html')

@app.route('/upload-file/', methods = ['GET', 'POST'])
@app.route('/upload-file/<path:subpath>', methods = ['GET', 'POST'])
@login_required
def upload_file(subpath=''):
   
    text = ""
    if request.method == 'POST':
        if subpath.startswith('%'):
            subpath = subpath[1:]   
            subpath = subpath.replace('%', '/')

        filePath = os.path.join(rootDir, subpath)
    
        fileNumOk = 0
        fileNumAll = 0
        for key, file in request.files.items():
            fupload = os.path.join(filePath, file.filename)
            fileNumAll += 1

            if secure_filename(file.filename) and not os.path.exists(fupload):
                try:
                    file.save(fupload)    
                    print(file.filename + ' Uploaded')
                    text = text + file.filename + ' Uploaded<br>'
                    fileNumOk += 1
                except Exception as e:
                    print(file.filename + ' Failed with Exception '+ str(e))
                    text = text + file.filename + ' Failed with Exception '+ str(e) + '<br>'

                    continue
            else:
                print(file.filename + ' Failed because File Already Exists or File Type Issue')
                text = text + file.filename + ' Failed because File Already Exists or File Type not secure <br>'

