from .utils import (
    delete_table,
    read_meta,
    #read_table,
    write_meta,
    write_table,
)


def _read_meta(command):
    try:
        return read_meta()
    except OSError as exc:
        message = f"level:sql;operation:{command};error:Не удалось получить метаданные"
        raise OSError(exc.errno, f"message\n{exc.strerror}")
    except (TypeError, ValueError) as exc:
        message = f"level:sql;operation:{command};error:Не удалось получить метаданные"
        raise ValueError(f"{message}\n{exc!s}")

def _write_meta(command, meta):
    try:
        write_meta(meta)
    except OSError as exc:
        message = f"level:sql;operation:{command};error:Не удалось получить метаданные"
        raise OSError(exc.errno, f"message\n{exc.strerror}")
    except (TypeError, ValueError) as exc:
        message = f"level:sql;operation:{command};error:Не удалось получить метаданные"
        raise ValueError(f"{message}\n{exc!s}")

COLUMN_TYPES = {
    'int': int,
    'str': str,
    'bool': bool,
}
ID_COLUNM_NAME = 'id'
ID_COLUNM_TYPE = 'int'

def create_table(metadata: dict, table_name: str, columns: list) -> dict:
    # Проверить наличие столбца id
    id_idx = None
    for idx, (col_name, col_type) in enumerate(columns):
        if col_name == ID_COLUNM_NAME:
            id_idx = idx
            break
        else:
            if col_type not in COLUMN_TYPES:
                raise TypeError(
                    "level:sql;command:create_table;" +\
                    f"error:Недопустимый тип {col_type} в столбце {col_name}")

    # Удалить столбец id, если есть
    if id_idx is not None:
        del columns[id_idx]

    # Добавить столбец id в начало списка
    columns.insert(0, (ID_COLUNM_NAME, ID_COLUNM_TYPE))
    
    if table_name in metadata["tables"]:
        raise KeyError("level:sql;command:create_table;" +\
                       f"error:Таблица {table_name} уже существует")
    table = {
        "name": table_name,
        "columns": columns,
    }

    metadata["tables"][table_name] = table
    
    return metadata

def drop_table(metadata: dict, table_name: str) -> dict:
    if table_name in metadata["tables"]:
        del metadata["tables"][table_name]
    else:
        raise KeyError("level:sql;command:drop_table;" +\
                       f"error:Таблица {table_name} не найдена")

    return metadata

# Обработчики команд
def create_table_handler(table_name: str, columns: list):
    meta = _read_meta("create_table")
    meta = create_table(meta, table_name, columns)
    _write_meta("create_table", meta)
    write_table(table_name, [])
    return f"Таблица {table_name} успешно создана"

def drop_table_handler(table_name: str):
    meta = _read_meta("drop_table")
    drop_table(meta, table_name)
    _write_meta("drop_table", meta)
    delete_table(table_name)
    return f"Таблица {table_name} успешно удалена"

def list_tables_handler():
    meta = _read_meta("list_tables")

    if meta["tables"]:
        return "\n".join(meta["tables"])
    else:
        return "База данных не содержит ни одной таблицы"

