"""
    Десериализация выбранных бинарных файлов Flatbuffers по выбранной схеме.
"""
# pylint: disable=import-error, wrong-import-position
import os
import sys
import argparse
from i18n import t

sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from general_funcs import init_app, get_flatc_path, execute_deserialize


def main() -> int | str:
    """
    Запуск скрипта.
    :return: Код ошибки или строка об ошибке.
    """
    init_app(os.path.join("images", "flatbuffers-logo-clean.png"))
    parser = argparse.ArgumentParser(prog=t("main.flatc_deserializer_name"),
                                     description=t("main.flatc_deserializer_desc"))
    parser.add_argument("-s", "--schema_path", type=str, default="", help=t("main.schema_file_arg"))
    parser.add_argument("-b", "--binary_paths", nargs="+", default=[],
                        help=t("main.binary_files_arg"))
    parser.add_argument("-o", "--output_path", type=str, default="",
                        help=t("main.output_directory_arg"))
    parser.add_argument("-f", "--flatc_path", type=str, default="", help=t("main.flatc_path_arg"))
    args = parser.parse_args()
    return execute_deserialize(
        get_flatc_path(os.getcwd(), True, False) if args.flatc_path == "" else args.flatc_path,
        args.schema_path, args.binary_paths, args.output_path)


if __name__ == "__main__":
    sys.exit(main())
