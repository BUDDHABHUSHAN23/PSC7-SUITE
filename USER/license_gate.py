import uuid
from datetime import datetime

def get_machine_id():
    # Use MAC address as machine id
    return str(uuid.getnode())

def validate_license_file(license_data):
    try:
        machine_id = license_data.get("machine_id")
        valid_till = license_data.get("valid_till")
        features = license_data.get("features", [])

        # Check machine id matches current machine
        if machine_id != get_machine_id():
            return False, "License is not valid for this machine."

        # Check expiry date
        if valid_till is None:
            return False, "License missing expiry date."
        expiry_date = datetime.strptime(valid_till, "%Y-%m-%d")
        if expiry_date < datetime.now():
            return False, "License has expired."

        # Return valid with features list
        return True, features
    except Exception as e:
        return False, f"License validation error: {e}"
