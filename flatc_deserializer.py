"""
    Десериализация выбранных бинарных файлов Flatbuffers по выбранной схеме.
"""
# pylint: disable=import-error
import os
import sys
import argparse
from i18n import t

from main import prepare_app, get_flatc_path, execute_deserialize

if __name__ == "__main__":
    prepare_app("images/flatbuffers-logo-clean.png")
    parser = argparse.ArgumentParser(prog=t("main.flatc_deserializer_name"),
                                     description=t("main.flatc_deserializer_desc"))
    parser.add_argument("-s", "--schema_path", type=str, default="", help=t("main.schema_file_arg"))
    parser.add_argument("-b", "--binary_paths", nargs="+", default=[],
                        help=t("main.binary_files_arg"))
    parser.add_argument("-o", "--output_path", type=str, default="",
                        help=t("main.output_directory_arg"))
    parser.add_argument("-f", "--flatc_path", type=str, default="", help=t("main.flatc_path_arg"))
    args = parser.parse_args()
    sys.exit(execute_deserialize(
        get_flatc_path(os.getcwd(), True) if args.flatc_path == "" else args.flatc_path,
        args.schema_path, args.binary_paths, args.output_path))
