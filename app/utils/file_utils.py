import os
import uuid

def ensure_upload_dir():
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    return upload_dir