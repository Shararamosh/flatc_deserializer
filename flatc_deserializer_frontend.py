"""
    GUI app for deserializing flatbuffers files.
"""
# pylint: disable=import-error, too-many-instance-attributes, too-many-statements
import os
from tkinter import ttk
from PIL.ImageTk import PhotoImage
from PIL import Image
from i18n import t
import customtkinter as CTk
from CTkMenuBar import CTkMenuBar
from CTkMessagebox import CTkMessagebox
import pywinstyles
from main import init_localization, get_resource_path, execute_download, get_flatc_path, \
    get_binary_tuples
from flatc_funcs import deserialize


class Deserializer(CTk.CTk):
    """
    GUI for batch deserialization of flatbuffers files.
    """

    def __init__(self):
        super().__init__()
        width = int(self.winfo_screenwidth() / 2)
        height = int(self.winfo_screenheight() / 2)
        self.geometry(f"{width}x{height}")
        self.title(t("main.flatc_deserializer_name"))
        self.wm_iconbitmap()
        img = Image.open(get_resource_path("images/flatbuffers-logo-clean.png"))
        self.iconphoto(True, PhotoImage(img))
        self.top_menu = CTkMenuBar(self, bg_color=None)
        img = Image.open(get_resource_path("images/flatbuffers-downloader-logo-clean.png"))
        self.flatc_button = self.top_menu.add_cascade(image=CTk.CTkImage(img))
        self.flatc_button.configure(text=t("frontend.download_flatc"))
        self.flatc_button.configure(command=self.flatc_button_pressed)
        self.main_frame = CTk.CTkFrame(self)
        self.main_frame.pack(expand=True, fill="both")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.files_frame = CTk.CTkFrame(self.main_frame)
        self.files_frame.grid_rowconfigure(0, weight=1)
        self.files_frame.grid_columnconfigure(0, weight=1)
        self.files_frame.grid_columnconfigure(1, weight=1)
        self.files_frame.grid(row=0, sticky=CTk.NSEW)
        self.src_files_frame = ttk.LabelFrame(self.files_frame, text=t("frontend.source_files"))
        self.src_files_frame.grid_rowconfigure(0, weight=1)
        self.src_files_frame.grid_rowconfigure(1, weight=1)
        self.src_files_frame.grid_columnconfigure(0, weight=1)
        self.src_files_frame.grid(row=0, column=0, sticky=CTk.NSEW)
        self.src_binaries_frame = ttk.LabelFrame(self.src_files_frame,
                                                 text=t("frontend.source_binaries"))
        self.src_binaries_frame.grid(row=0, column=0, padx=10, pady=10, sticky=CTk.NSEW)
        self.src_binaries_table = ttk.Treeview(self.src_binaries_frame,
                                               columns=("file", "file_size"), show="headings")
        self.src_binaries_table.heading("file", text=t("frontend.source_file_loc"))
        self.src_binaries_table.heading("file_size", text=t("frontend.file_size"))
        self.src_binaries_table.pack(fill=CTk.BOTH, expand=True, padx=10, pady=10)
        pywinstyles.apply_dnd(self.src_binaries_table.winfo_id(), self.on_binary_dropped)
        self.src_schemas_frame = ttk.LabelFrame(self.src_files_frame,
                                                text=t("frontend.source_schemas"))
        self.src_schemas_frame.grid(row=1, column=0, padx=10, pady=10, sticky=CTk.NSEW)
        self.src_schemas_table = ttk.Treeview(self.src_schemas_frame, columns="file", show="")
        self.src_schemas_table.pack(fill=CTk.BOTH, expand=True, padx=10, pady=10)
        pywinstyles.apply_dnd(self.src_schemas_table.winfo_id(), self.on_schema_dropped)
        self.dest_files_frame = ttk.LabelFrame(self.files_frame,
                                               text=t("frontend.destination_files"))
        self.dest_files_frame.grid_rowconfigure(0, weight=1)
        self.dest_files_frame.grid_rowconfigure(1, weight=1)
        self.dest_files_frame.grid_columnconfigure(0, weight=1)
        self.dest_files_frame.grid(row=0, column=1, sticky=CTk.NSEW)
        self.dest_binaries_frame = ttk.LabelFrame(self.dest_files_frame,
                                                  text=t("frontend.destination_binaries"))
        self.dest_binaries_frame.grid(row=0, column=0, padx=10, pady=10, sticky=CTk.NSEW)
        self.dest_binaries_table = ttk.Treeview(self.dest_binaries_frame,
                                                columns=("file", "result", "file_size"),
                                                show="headings")
        self.dest_binaries_table.heading("file", text=t("frontend.destination_file_loc"))
        self.dest_binaries_table.heading("result", text=t("frontend.result"))
        self.dest_binaries_table.heading("file_size", text=t("frontend.file_size"))
        self.dest_binaries_table.pack(fill=CTk.BOTH, expand=True, padx=10, pady=10)
        self.dest_options_frame = ttk.LabelFrame(self.dest_files_frame,
                                                 text=t("frontend.destination_options"))
        self.dest_options_frame.grid(row=1, column=0, padx=10, pady=10, sticky=CTk.NSEW)
        self.bottom_menu = CTkMenuBar(self, bg_color=None)
        img = Image.open(get_resource_path("images/flatbuffers-batch-logo-clean.png"))
        self.deserialize_button = self.bottom_menu.add_cascade(image=CTk.CTkImage(img))
        self.deserialize_button.configure(text=t("frontend.deserialize"))
        self.deserialize_button.configure(command=self.deserialize_button_pressed)
        self.bottom_menu.pack(side=CTk.RIGHT)

    @staticmethod
    def flatc_button_pressed():
        """
        Triggered to download flatc.
        """
        execute_download(os.getcwd())

    def on_binary_dropped(self, paths: list[str]):
        """
        Triggered when binary files or directories are added to table.
        :param paths: List of paths to added files or directories
        """
        for path in paths:
            if os.path.isdir(path):
                for subdir, _, files in os.walk(path):
                    for file in files:
                        self.add_src_binary(os.path.abspath(os.path.join(subdir, file)))
            elif os.path.isfile(path):
                self.add_src_binary(path)

    def add_src_binary(self, file: str):
        """
        Adds file to binary source table.
        :param file: Path to file.
        """
        binary_path = os.path.abspath(file)
        if os.path.splitext(binary_path)[1].lower() == ".json":
            return
        src_values = (binary_path, t("frontend.size_kb") % (os.path.getsize(binary_path) / 1024))
        output_path = os.path.splitext(binary_path)[0] + ".json"
        if os.path.isfile(output_path):
            dest_values = (output_path, t("frontend.file_already_exists"),
                           t("frontend.size_kb") % (os.path.getsize(output_path) / 1024))
        else:
            dest_values = (output_path, "", "")
        if self.src_binaries_table.exists(binary_path.casefold()):
            return
        self.src_binaries_table.insert("", "end", binary_path.casefold(), values=src_values)
        self.dest_binaries_table.insert("", "end", binary_path.casefold(), values=dest_values)

    def on_schema_dropped(self, paths: list[str]):
        """
        Triggered when schema files or directories are added to table.
        :param paths: List of paths to added files or directories
        """
        for path in paths:
            if os.path.isdir(path):
                for subdir, _, files in os.walk(path):
                    for file in files:
                        self.add_src_schema(os.path.abspath(os.path.join(subdir, file)))
            elif os.path.isfile(path):
                self.add_src_schema(path)

    def add_src_schema(self, file: str):
        """
        Adds file to schema source table.
        :param file: Path to file.
        """
        schema_path = os.path.abspath(file)
        if os.path.splitext(schema_path)[1].lower() != ".fbs":
            return
        if self.src_schemas_table.exists(schema_path.casefold()):
            return
        self.src_schemas_table.insert("", "end", schema_path.casefold(), values=[schema_path])

    def deserialize_button_pressed(self):
        """
        Triggered to deserialize source binary files.
        :return:
        """
        flatc_path = get_flatc_path(os.getcwd(), False, True)
        if flatc_path == "":
            CTkMessagebox(title=t("frontend.error"), message=t("frontend.flatc_not_found"),
                          icon="cancel")
            return
        binary_paths = [self.src_binaries_table.set(i, 0) for i in
                        self.src_binaries_table.get_children("")]
        output_paths = [os.path.dirname(self.dest_binaries_table.set(i, 0)) for i in
                        self.dest_binaries_table.get_children("")]
        schema_paths = [self.src_schemas_table.set(i, 0) for i in
                        self.src_schemas_table.get_children("")]
        binary_tuples = get_binary_tuples(binary_paths, schema_paths)
        for i, binary_tuple in enumerate(binary_tuples):
            self.deserialize_and_update_table(flatc_path, binary_tuple[1], binary_tuple[0],
                                              output_paths[i])

    def deserialize_and_update_table(self, flatc_path: str, schema_path: str, binary_path: str,
                                     output_path: str):
        """
        Deserializes flatbuffers binary and updates destination table.
        :param flatc_path: Schema compiler path.
        :param schema_path: Schema file path.
        :param binary_path: Binary file path.
        :param output_path: Output directory path.
        """
        json_path = deserialize(flatc_path, schema_path, binary_path, output_path, False)
        for i in self.dest_binaries_table.get_children(""):
            if os.path.samefile(i, binary_path):
                if json_path != "":
                    self.dest_binaries_table.set(i, 1, t("frontend.result_done"))
                    self.dest_binaries_table.set(i, 2, t("frontend.size_kb") % (
                                os.path.getsize(json_path) / 1024))
                else:
                    self.dest_binaries_table.set(i, 1, t("frontend.result_error"))
                    self.dest_binaries_table.set(i, 2, "")


if __name__ == "__main__":
    init_localization()
    CTk.set_appearance_mode("System")
    CTk.set_default_color_theme("blue")
    Deserializer().mainloop()
