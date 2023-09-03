from datetime import datetime
import shutil
import os


def cprint(content: str, end: str = None) -> None:
    if end is None:
        print(f"{datetime.now()} :: {content}")
        return
    print(f"{datetime.now()} :: {content}", end=end)


def move_output_file(filename: str, directory: str) -> None:
    try:
        shutil.move(filename + ".mp4",
                    os.path.join(directory, filename + ".mp4"))
    except FileNotFoundError:
        os.remove(f"{os.getcwd()}\\{filename}.mp4")
        if os.path.exists(f"{os.getcwd()}\\{directory}"):
            raise FileNotFoundError
        else:
            raise NotADirectoryError
