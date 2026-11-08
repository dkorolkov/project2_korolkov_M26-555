#!/usr/bin/env python3

from .engine import run, welcome
from .utils import init_meta


def main():
    init_meta()
    welcome()
    run()
    
if __name__ == '__main__':
    main()
