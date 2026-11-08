import shlex
from collections.abc import Callable

import prompt

from .core import (
    create_table_handler,
    drop_table_handler,
    list_tables_handler,
)

first_message = "Первая попытка запустить проект!\n\n***"
command_prompt = "Введите команду: "

def welcome():
    print(first_message)
    print_help()
    
def run():
    while True:
        command_string = prompt.string(command_prompt)
        try:
            command, command_data, handler = parse(command_string)
        except KeyError:
            print(f"Неизвестная команда {command}")
            continue
        except (TypeError, ValueError) as exc:
            fields = parse_exceprion(str(exc))
            if fields is None:
                # Выбрасываем необработанное исключение
                raise
            print(fields.get('error', ''))
            continue

        if command == 'exit':
            break

        try:
            result = handler(**command_data)
            if result is not None:
                print(result)
        except (KeyError, TypeError, ValueError) as exc:
            fields = parse_exceprion(str(exc))
            print(f"Ошибка при выполнении команды {command}: {fields.get('error', '')}")

def parse_exceprion(message: str) -> dict:
    top = message.split('\n')[0]
    fields = {}
    for item in top.split(';'):
        try:
            key, val = item.split(':', 1)
            fields[key] = val
        except ValueError:
            return None
        
    return fields
    

def print_help():
    """Prints the help message for the current mode."""
   
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    for cmd in ("create_table", "list_tables", "drop_table"):
        print(f"<command> {cmd} {command_handlers[cmd][2]}")
    
    print("\nОбщие команды:")
    for cmd in ("exit", "help"):
        print(f"<command> {cmd} {command_handlers[cmd][2]}")
    
def parse(command_string: str) -> (str, dict, Callable):
    tokens = shlex.shlex(command_string, posix=True, punctuation_chars=":=!<>")
    tokens.whitespace_split = True
    tokens.commenters = ""
    tokens = list(tokens)
    command = tokens[0]
    if command not in command_handlers:
        raise KeyError(f"level:commands;error:Неизвестная команда {command}")

    parser, handler = command_handlers[command][:2]
    if parser is None:
        return command, {}, None
        
    try:
        return parser(tokens) + (handler,)
    except ValueError as exc:
        raise ValueError(
        f"level:commands;command:{command};error:Неверный формат команды {command}: {exc!s}")
        
keywords = {"create_table", "drop_table", "list_tables",
            "select", "insert", "update", "delete",
            "from", "where"
            }
def is_identtifier(word: str) -> bool:
    return word.isidentifier() and word not in keywords

def not_parse(tokens: list) -> dict:
    return tokens[0], {}

def create_table_parser(tokens: list) -> dict:
    command = tokens[0]
    if len(tokens) < 2:
        raise ValueError("укажите имя таблицы")
    table_name = tokens[1]
    if not is_identtifier(table_name):
        raise ValueError(f"имя таблицы {table_name}" +\
                         " не является допустимым идентификатором")
    idx = 2
    columns = []
    column_set = set()
    while True:
        if len(tokens) == idx:
            break
        if len(tokens) < idx + 3:
            raise ValueError("wrong columns list")
        col_name = tokens[idx]
        if tokens[idx+1] != ':':
            raise ValueError("wrong columns list")
        col_type = tokens[idx+2]
        if not is_identtifier(col_name):
            raise ValueError(f"Имя столбца {col_name}" +\
                             " не является допустимым идентификатором")
        if col_name in column_set:
            raise ValueError(f"Имя столбца {col_name} повторяется")
            
        columns.append((col_name.lower(), col_type.lower()))
        idx += 3

    return command, {
        "table_name": table_name.lower(),
        "columns": columns,
    }

def drop_table_parser(tokens: list) -> dict:
    command = tokens[0]
    if len(tokens) < 2:
        raise ValueError("укажите имя таблицы")
    table_name = tokens[1]
    if not is_identtifier(table_name):
        raise ValueError(f"Имя столбца {table_name}" +\
                         " не является допустимым идентификатором")

    return command, {
        "table_name": table_name.lower(),
    }

# Словарь команд.
# Ключ -- имя команды
# Значение -- кортеж из трёх элементов:
#             парсер команды, обработчик команды, описание команды
command_handlers = {
    "exit": (not_parse, None, "- выход из программы"),
    "help": (not_parse, print_help, "- справочная информация"),
    "create_table": (create_table_parser, create_table_handler,
                     "<имя_таблицы> <столбец1:тип> .. - создать таблицу"),
    "drop_table": (drop_table_parser, drop_table_handler,
                   "<имя_таблицы> - удалить таблицу"),
    "list_tables": (not_parse, list_tables_handler,
                   "- показать список всех таблиц"),
}
