import json
import os
import os.path


def load_data(filepath):
    try:
        with open(filepath) as f:
            return json.load(f)
    except OSError as exc:
        message = f"level:file;operation:read;path:{filepath};error:{exc.strerror}"
        raise OSError(exc.errno, message)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        message = f"level:json;operation:load;error:{exc}"
        raise ValueError(message)
    
def save_data(filepath, data):
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f)
            return True
    except OSError as exc:
        message = f"level:file;operation:write;path:{filepath};error:{exc.strerror}"
        raise OSError(exc.errno, message)
    except (TypeError, ValueError) as exc:
        message = f"level:json;operation:dump;error:{exc}"
        raise ValueError(message)
        
DATA_DIR = "data"
META_FILE_NAME = "db_meta.json"
META_PATH = os.path.join(DATA_DIR, META_FILE_NAME)

def init_meta():
    if not os.path.isfile(META_PATH):
        save_data(META_PATH, {"tables":{}})

def read_meta() -> dict:
    return load_data(META_PATH)

def write_meta(meta: dict):
    save_data(META_PATH, meta)
    
def make_table_path(table_name: str) -> str:
    return os.path.join(DATA_DIR, f"{table_name}.json")

def read_table(table_name: str) -> list:
    path = make_table_path(table_name)
    return load_data(path)

def write_table(table_name: str, data: list):
    path = make_table_path(table_name)
    return save_data(path, data)

def delete_table(table_name: str):
    path = make_table_path(table_name)
    os.remove(path)
