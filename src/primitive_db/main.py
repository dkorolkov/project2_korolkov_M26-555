#!/usr/bin/env python3

import json

from .engine import run, welcome
from .utils import init_meta


def main():
    try:
        init_meta()
    except (KeyError, TypeError, ValueError, OSError,
        UnicodeDecodeError, json.JSONDecodeError) as exc:
        print(f"Ошибка при инициализации: {exc!s}")
        return

    welcome()
    run()
    
if __name__ == '__main__':
    main()
