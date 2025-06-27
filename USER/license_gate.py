import hashlib
import platform
import uuid
import os
from datetime import datetime

def get_machine_id():
    """
    Generate a secure and stable machine ID using multiple system identifiers.
    Returns a SHA-256 hash string.
    """
    components = [
        platform.node(),                # Hostname
        platform.system(),              # OS type
        platform.release(),             # OS version
        platform.machine(),             # Machine type
        str(uuid.getnode()),            # MAC address
        os.getenv("PROCESSOR_IDENTIFIER", ""),  # Optional Windows-specific
    ]
    raw_id = "-".join(components)
    return hashlib.sha256(raw_id.encode()).hexdigest()

def validate_license_file(license_data):
    """
    Validates the uploaded license file.
    Checks for machine ID match and license expiry.
    Returns (True, dict(features, valid_till)) if valid.
    Returns (False, error_message) if invalid.
    """
    try:
        # Extract fields
        machine_id = license_data.get("machine_id")
        valid_till = license_data.get("valid_till")
        features = license_data.get("features", [])

        # Validate machine ID
        if machine_id != get_machine_id():
            return False, "License is not valid for this machine."

        # Validate expiry
        if not valid_till:
            return False, "License missing expiry date."

        expiry_date = datetime.strptime(valid_till, "%Y-%m-%d")
        if expiry_date < datetime.now():
            return False, "License has expired."

        # If all good, return features and expiry info
        return True, {
            "features": features,
            "valid_till": expiry_date.strftime("%Y-%m-%d")
        }

    except Exception as e:
        return False, f"License validation error: {str(e)}"
