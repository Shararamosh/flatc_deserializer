"""
    Модуль, включающий в себя функции для работы с Flatbuffers (flatc.exe).
"""
# pylint: disable=too-many-branches, too-many-statements, too-many-arguments, too-many-locals
import os
import shutil
from json import loads
from logging import info
from subprocess import run, CalledProcessError

from i18n import t


def deserialize(flatc_path: str, schema_path: str, binary_path: str, output_path: str = "",
                additional_params=None, return_dict=True) -> dict:
    """
    Десериализация бинарного файла, используя схему Flatbuffers.
    :param flatc_path: Путь к компилятору схемы.
    :param schema_path: Путь к файлу схемы.
    :param binary_path: Путь к бинарному файлу.
    :param output_path: Путь к директории или файлу вывода.
    :param additional_params: Дополнительный список параметров для компилятора схемы.
    :param return_dict: Если True, возвращать словарь из прочитанного файла. Иначе - путь к файлу.
    :return: Десериализованный бинарный файл в виде словаря.
    """
    if additional_params is None:
        additional_params = []
    if not os.path.isfile(flatc_path) or not os.path.isfile(schema_path) or not os.path.isfile(
            binary_path):
        return {} if return_dict else ""
    flatc_path = os.path.abspath(flatc_path)
    schema_path = os.path.abspath(schema_path)
    binary_path = os.path.abspath(binary_path)
    binary_name = os.path.splitext(os.path.basename(binary_path))[0]
    output_path = os.path.abspath(output_path)
    if output_path == "":
        output_path = os.path.dirname(binary_path)
        json_path = os.path.join(output_path, binary_name + ".json")
    elif os.path.splitext(output_path)[1].lower() == ".json":
        output_path = os.path.dirname(output_path)
        json_path = output_path
    elif os.path.isfile(output_path):
        return {} if return_dict else ""
    else:
        json_path = os.path.join(output_path, binary_name + ".json")
    output_path += os.sep
    args = [flatc_path]
    args += ["--raw-binary"]
    args += ["-o", output_path]
    args += additional_params
    args += ["-t", schema_path]
    args += ["--", binary_path]
    output_json_path = os.path.join(output_path, binary_name + ".json")
    previous_json_contents = None
    if os.path.isfile(output_json_path):
        with open(output_json_path, "rb") as file:
            previous_json_contents = file.read()
    try:
        proc = run(args, shell=False, capture_output=True, text=True, check=True)
    except CalledProcessError as cpe:
        info(t("flatc_funcs.run_error"), " ".join(cpe.cmd), cpe.returncode)
        if cpe.stderr is not None and cpe.stderr != "":
            info(cpe.stderr)
        return {} if return_dict else ""
    if proc.stdout is not None and proc.stdout != "":
        info(t("flatc_funcs.run_ok"), " ".join(args))
        info(proc.stdout)
    if not os.path.isfile(output_json_path):
        info(t("flatc_funcs.json_error"), binary_path)
        return {} if return_dict else ""
    if previous_json_contents is not None and not os.path.samefile(output_json_path, json_path):
        shutil.copy(output_json_path, json_path)
        with open(output_json_path, "wb") as file:
            file.write(previous_json_contents)
    try:
        with open(json_path, "rb") as json_file:
            current_json_contents = json_file.read()
    except OSError:
        info(t("main.file_failed_to_open"), json_path)
        return {} if return_dict else ""
    if current_json_contents != previous_json_contents:
        info(t("flatc_funcs.json_ok"), binary_path, json_path)
    return loads(current_json_contents.decode("utf-8")) if return_dict else json_path
