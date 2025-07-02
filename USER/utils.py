import pandas as pd
import json

def load_excel(file):
    """
    Load an Excel file and return a dict of sheet_name: DataFrame.
    'file' can be a file path or file-like object.
    """
    return pd.read_excel(file, sheet_name=None)

def load_sheet(file, sheet_name):
    """
    Load a specific sheet from an Excel file.
    """
    return pd.read_excel(file, sheet_name=sheet_name)

def load_csv(file):
    """
    Load a CSV file and return a DataFrame.
    """
    return pd.read_csv(file)

def load_json(file):
    """
    Load a JSON file and return Python object.
    'file' should be a file-like object or path.
    """
    if hasattr(file, "read"):
        return json.load(file)
    else:
        with open(file, 'r') as f:
            return json.load(f)
