import os
import secrets
from PIL import Image
from flask import current_app

def save_profile_picture(form_picture):
    """
    Save the uploaded profile picture with a random filename
    and resize it to 150x150 pixels.
    """
    # Generate a random hex name for the file to avoid name collisions
    random_hex = secrets.token_hex(8)
    _, file_ext = os.path.splitext(form_picture.filename)
    picture_filename = random_hex + file_ext
    
    # Create the path where the file will be saved
    pictures_path = os.path.join(current_app.root_path, 'static/img/profile_pics')
    
    # Create directory if it doesn't exist
    if not os.path.exists(pictures_path):
        os.makedirs(pictures_path)
    
    picture_path = os.path.join(pictures_path, picture_filename)
    
    # Resize the image to save space and load faster
    output_size = (150, 150)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    
    # Save the file
    img.save(picture_path)
    
    return picture_filename 