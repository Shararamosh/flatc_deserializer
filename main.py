"""
    Десериализация бинарных файлов Flatbuffers по заданной схеме.
"""
import os
import sys
from sys import stdout
from logging import basicConfig, INFO
from warnings import filterwarnings
from locale import getdefaultlocale
from tkinter import Tk
from tkinter.filedialog import askopenfilename, askopenfilenames, askdirectory
import i18n
from PIL.ImageTk import PhotoImage
from tqdm import tqdm
from flatc_funcs import deserialize  # pylint: disable=import-error


def get_resource_path(filename: str) -> str:
    """
    Получение пути к файлу или директории, если используется PyInstaller.
    :param filename: Изначальный путь к файлу или директории.
    :return: Изменённый путь к файлу или директории.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(getattr(sys, "_MEIPASS"), filename)
    return filename


basicConfig(stream=stdout, format="%(message)s", level=INFO)
filterwarnings("ignore", category=DeprecationWarning)
i18n.set("locale", getdefaultlocale()[0])  # pylint: disable=deprecated-method
i18n.set("fallback", "en_US")
i18n.load_path.append(get_resource_path("localization"))
i18n.set("file_format", "yml")
i18n.set("filename_format", "{namespace}.{format}")
i18n.set("skip_locale_root_data", True)
i18n.set("use_locale_dirs", True)
root = Tk()
root.withdraw()
root.iconphoto(True, PhotoImage(file=get_resource_path("images/flatbuffers-logo-clean.png")))


def main() -> int:
    """
    Десериализация бинарных файлов Flatbuffers по заданной схеме.
    :return: Код ошибки.
    """
    flatc_path = askopenfilename(title=i18n.t("main.tkinter_flatc_select"),
                                 filetypes=[(i18n.t("main.exe_filetype"), "*.exe")])
    if flatc_path == "":
        return os.EX_OK
    schema_path = askopenfilename(title=i18n.t("main.tkinter_fbs_select"),
                                  filetypes=[(i18n.t("main.fbs_filetype"), "*.fbs")])
    if schema_path == "":
        return os.EX_OK
    schema_name = os.path.splitext(os.path.basename(schema_path))[0]
    binary_paths = askopenfilenames(title=i18n.t("main.tkinter_binaries_select"),
                                    filetypes=[
                                        (i18n.t("main.flatc_binary_filetype"), "*." + schema_name)])
    output_path = askdirectory(title=i18n.t("flatc_funcs.tkinter_output_select"))
    full_size = sum(os.stat(binary_path).st_size for binary_path in binary_paths)
    pbar = tqdm(total=full_size, position=0, unit="B", unit_scale=True, desc=i18n.t("main.files"))
    for binary_path in binary_paths:
        pbar.set_postfix_str(binary_path)
        pbar.clear()
        deserialize(flatc_path, schema_path, binary_path, output_path)
        pbar.update(os.stat(binary_path).st_size)
    pbar.set_postfix_str("")
    pbar.close()
    return os.EX_OK


if __name__ == "__main__":
    sys.exit(main())
