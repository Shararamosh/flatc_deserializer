"""
    Модуль, включающий в себя функции для работы с Flatbuffers (flatc.exe).
"""
import os
from json import loads
from logging import info
from subprocess import run, CalledProcessError

from i18n import t


def deserialize(flatc_path: str, schema_path: str, binary_path: str, output_path: str = "") -> dict:
    """
    Десериализация бинарного файла, используя схему Flatbuffers.
    :param flatc_path: Путь к компилятору схемы.
    :param schema_path: Путь к файлу схемы.
    :param binary_path: Путь к бинарному файлу.
    :param output_path: Путь к директории вывода.
    :return: Десериализованный бинарный файл в виде словаря.
    """
    flatc_path = os.path.abspath(flatc_path)
    schema_path = os.path.abspath(schema_path)
    binary_path = os.path.abspath(binary_path)
    binary_name = os.path.splitext(os.path.basename(binary_path))[0]
    output_path = os.path.abspath(output_path)
    json_path = os.path.abspath(output_path + os.sep + binary_name + ".json")
    previous_json_contents = None
    try:
        with open(json_path, "rb") as json_file:
            previous_json_contents = json_file.read()
    except OSError:
        pass
    args = [flatc_path]
    if output_path == "":
        output_path = binary_path
    output_path += os.sep
    args += ["--raw-binary"]
    args += ["-o", output_path]
    args += ["--strict-json"]
    args += ["-t", schema_path]
    args += ["--", binary_path]
    try:
        proc = run(args, shell=False, capture_output=True, text=True, check=True)
    except CalledProcessError as cpe:
        info(t("flatc_funcs.run_error"), " ".join(cpe.cmd), cpe.returncode)
        if cpe.stderr is not None and cpe.stderr != "":
            info(cpe.stderr)
        return {}
    if proc.stdout is not None and proc.stdout != "":
        info(t("flatc_funcs.run_ok"), " ".join(args))
        info(proc.stdout)
    if not os.path.isfile(json_path):
        info(t("flatc_funcs.json_error"), binary_path)
        return {}
    try:
        with open(json_path, "rb") as json_file:
            current_json_contents = json_file.read()
    except OSError:
        info(t("main.file_failed_to_open"), json_path)
        return {}
    if current_json_contents != previous_json_contents:
        info(t("flatc_funcs.json_ok"), binary_path, json_path)
    return loads(current_json_contents.decode("utf-8"))
