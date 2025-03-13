"""
    Десериализация бинарных файлов Flatbuffers в выбранной директории по всем схемам в другой
    выбранной директории.
"""
# pylint: disable=import-error, wrong-import-position
import os
import sys
import argparse
from i18n import t

sys.path.append(os.path.join(os.path.dirname(__file__), "."))

from general_funcs import init_app, get_flatc_path, execute_deserialize_batch


def main() -> int | str:
    """
    Запуск скрипта.
    :return: Код ошибки или строка об ошибке.
    """
    init_app(os.path.join("images", "flatbuffers-batch-logo-clean.png"))
    parser = argparse.ArgumentParser(prog=t("main.flatc_deserializer_batch_name"),
                                     description=t("main.flatc_deserializer_batch_desc"))
    parser.add_argument("-s", "--schemas_path", type=str, default="",
                        help=t("main.schemas_directory_arg"))
    parser.add_argument("-b", "--binaries_path", type=str, default="",
                        help=t("main.binaries_directory_arg"))
    parser.add_argument("-o", "--output_path", type=str, default="",
                        help=t("main.output_directory_arg"))
    parser.add_argument("-f", "--flatc_path", type=str, default="", help=t("main.flatc_path_arg"))
    args = parser.parse_args()
    return execute_deserialize_batch(
        get_flatc_path(os.getcwd(), True, False) if args.flatc_path == "" else args.flatc_path,
        args.schemas_path, args.binaries_path, args.output_path)


if __name__ == "__main__":
    sys.exit(main())
