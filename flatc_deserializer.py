"""
    Десериализация бинарных файлов Flatbuffers по заданной схеме c открытием диалогового окна для
    поиска компилятора схемы при его отсутствии в рабочей директории.
"""
import os
import sys

from main import prepare_app, get_flatc_path, execute_deserialize  # pylint: disable=import-error

if __name__ == "__main__":
    prepare_app("images/flatbuffers-logo-clean.png")
    sys.exit(execute_deserialize(get_flatc_path(True, os.getcwd(), True)))
