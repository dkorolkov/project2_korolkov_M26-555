import json
from time import monotonic

import prompt


def handle_db_errors(func):
    def wrap(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OSError as exc:
            print(exc.args[1])
        except (KeyError, TypeError, ValueError, UnicodeDecodeError,
                json.JSONDecodeError) as exc:
            args = exc.args
            print(args[0] if len(args) == 1 else str(args))
    return wrap
    
def confirm_action(action_name):
    def deco(func):
        def wrap(*args, **kwargs):
            answer = prompt.string(
            'Вы уверены, что хотите выполнить "{action_name}"? [y/n]')
            if answer.lower() == 'y':
                return func(*args, **kwargs)
        return wrap
    return deco
    
def log_time(func):
    def wrap(*args, **kwargs):
        start_time = monotonic()
        result = func(*args, **kwargs)
        end_time = monotonic()
        print(f"Функция {func.__name__} выполнилась за" +\
              f" {end_time-start_time:0.3f} секунд")
        return result
    return wrap
    
def create_cacher():
    cache = {}

    def cache_result(key, value_func):
        if key in cache:
            print("Результат из кеша")
            return cache[key]
        else:
            result = value_func(key)
            if result != "Ошибка":
                cache[key] = result
                print("Результат из БД")
            return result
            
    return cache_result
