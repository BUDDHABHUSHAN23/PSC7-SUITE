import os
import json
import base64
from cryptography.fernet import Fernet
from hashlib import sha256
from datetime import datetime
import platform
import uuid
import hashlib
import sys  

# Constants
PROJECT_ROOT = os.getenv("PROJECT_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
LICENSE_DIR = os.path.join(PROJECT_ROOT, "license")
LICENSE_PATH = os.path.join(LICENSE_DIR, "license.dat")

# Encryption setup
SECRET_KEY = sha256(b"consulta_secret_key").digest()
FERNET_KEY = base64.urlsafe_b64encode(SECRET_KEY[:32])
fernet = Fernet(FERNET_KEY)



def get_runtime_path(path=""):
    if getattr(sys, 'frozen', False):  # running in bundle
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, path)

def get_machine_id():
    components = [
        platform.node(),
        platform.system(),
        platform.release(),
        platform.machine(),
        str(uuid.getnode()),
        os.getenv("PROCESSOR_IDENTIFIER", "")
    ]
    raw_id = "-".join(components)
    return hashlib.sha256(raw_id.encode()).hexdigest()


def save_encrypted_license(data):
    try:
        if not os.path.exists(LICENSE_DIR):
            os.makedirs(LICENSE_DIR, exist_ok=True)  # <- safer

        json_str = json.dumps(data)
        encrypted = fernet.encrypt(json_str.encode())

        with open(LICENSE_PATH, "wb") as f:
            f.write(encrypted)
        
        print(f"[License Saved] Encrypted license saved to: {LICENSE_PATH}")
        return True
    except Exception as e:
        print("[License Save Error]", e)
        return False



def load_encrypted_license():
    try:
        if os.path.exists(LICENSE_PATH):
            with open(LICENSE_PATH, "rb") as f:
                encrypted = f.read()
            decrypted = fernet.decrypt(encrypted)
            return json.loads(decrypted)
        return None
    except Exception as e:
        print("[License Load Error]", e)
        return None


def validate_license_file(license_data):
    try:
        required_keys = ["machine_id", "valid_till", "features"]
        if not all(k in license_data for k in required_keys):
            return False, "Missing fields in license"

        if license_data["machine_id"] != get_machine_id():
            return False, "Machine ID mismatch"

        expiry = datetime.strptime(license_data["valid_till"], "%Y-%m-%d")
        if expiry < datetime.now():
            return False, "License has expired"

        return True, license_data
    except Exception as e:
        return False, f"Validation error: {e}"


def delete_saved_license():
    if os.path.exists(LICENSE_PATH):
        os.remove(LICENSE_PATH)


def get_valid_license_on_start():
    data = load_encrypted_license()
    if data:
        valid, result = validate_license_file(data)
        if valid:
            return data, True, result["features"], result["valid_till"]
        else:
            return data, False, [], ""
    return None, False, [], ""

def get_license_path():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)  # folder where exe lives
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    license_dir = os.path.join(base_dir, "license")
    if not os.path.exists(license_dir):
        os.makedirs(license_dir, exist_ok=True)

    return os.path.join(license_dir, "license.dat")

LICENSE_PATH = get_license_path()
