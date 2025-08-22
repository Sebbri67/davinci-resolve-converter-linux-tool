#!/usr/bin/python3
# VERSION 1.1

import libs.libui as libui
import libs.libtools as libtools


def main() -> None:
    if not libtools.check_ffmpeg():
        return

    root, notebook, input_files, output_dir, bold_font = libui.create_princ()

    #### ONGLET FICHIERS
    files_list, input_files, select_button, remove_button, clear_button, output_button, output_dir = libui.create_files_tab(notebook, input_files, output_dir)

    #### ONGLET OPTIONS
    conversion_option, num_threads = libui.create_options_tab(notebook, bold_font)

    #### ONGLET TRAITEMENT
    libui.create_processing_tab(root, notebook, input_files, output_dir, files_list,
                                select_button, remove_button, clear_button, output_button,
                                conversion_option, num_threads)

    #### ONGLET DEBUG
    debug_tab = libui.create_debug_tab(notebook)

    #### ONGLET AIDE
    libui.create_help_tab(notebook, bold_font)

    root.mainloop()

if __name__ == "__main__":
    main()
