# config.py
import os

class Config:
    SECRET_KEY = os.urandom(24)
    MySQL_HOST = 'localhost'
    MYSQL_USER = 'root'                                                  # MySQL username
    MYSQL_PASSWORD = 'c@s&w1ch'                             # MySQL password
    MYSQL_DB = 'gamerverse'                                           # MySQL Database name
    UPLOAD_FOLDER = 'uploads'                                       # Folder for storing images
    ALLOWED_EXTENSIONS = {'png', 'jpeg', 'jpg', 'gif'}      # Allowed image formats