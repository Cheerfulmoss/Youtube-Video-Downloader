import os
import threading
import pytube
from pytube import YouTube
from pytube import Playlist
import re
from util import cprint, move_output_file
from subprocess import call
from os import remove
import shutil


class PlaylistDownloader:
    def __init__(self, url: str, download_dir: str,
                 download_type: str, debug: bool = False,
                 threads: int = 0):
        (self.url, self.download_dir, self.download_type,
         self.debug) = (url, download_dir, download_type, debug)

        self.threads = 1 if threads == 0 else threads

        self._playlist_obj = Playlist(url=url)

    def download_range(self, start: int = None, stop: int = None,
                       step: int = 1):
        threads = list()
        ide = 0

        if stop is None:
            stop = len(self._playlist_obj)
        if start is None:
            start = 0

        download_complete = False
        index = start

        while not download_complete:
            if len(self._playlist_obj) <= index or index >= stop:
                download_complete = True
                continue

            active_count = len([thread for thread in threading.enumerate()
                                if "download" in thread.name])

            if active_count < self.threads:
                thread = threading.Thread(target=self._single_download,
                                          args=(index, ide), name="download")
                threads.append(thread)
                thread.start()
                index += step
                ide += 1

        for thread in threads:
            thread.join()

    def _single_download(self, index: int, ide: int):
        VideoDownloader(
            url=self._playlist_obj[index], download_dir=self.download_dir,
            download_type=self.download_type, ide=ide, debug=self.debug,
            threads=(True if self.threads else False)
        ).download_auto()
        # TODO(Alexander Burow): Make this use .auto_download


class VideoDownloader:
    AUDIO_NAME = "audio"
    VIDEO_NAME = "video"
    EXTENSION = "webm"

    FILENAME_CHAR_EXCLUSION = {
        "<": "", ">": "", ":": "-",
        '"': "", "/": "", "\\": "",
        "|": "-", "?": "", '*': ""
    }

    def __init__(self, url: str, download_dir: str,
                 download_type: str, ide: int, debug: bool = False,
                 threads: bool = False):
        (self.url, self.download_dir, self.download_type,
         self.debug, self.threads) = (url, download_dir, download_type, debug,
                                      threads)
        self._video_obj = YouTube(url=url)
        self.ide = ide
        print(f"Video object: ID = {self.ide}")
        self._filename = self.make_filename()

        self._INTER_VIDEO_NAME = (f"{self.VIDEO_NAME}-{self.ide}"
                                  f".{self.EXTENSION}")
        self._INTER_AUDIO_NAME = (f"{self.AUDIO_NAME}-{self.ide}"
                                  f".{self.EXTENSION}")

    def make_filename(self) -> str:
        filename = "".join(
            self.FILENAME_CHAR_EXCLUSION[char]
            if char in self.FILENAME_CHAR_EXCLUSION else
            char for char in self._video_obj.title
        )
        filename = re.sub(r"\s+", " ", filename)
        return filename

    def audio_download(self, intermediate: bool = True):
        a_tube = self._video_obj.streams.filter(
            only_audio=True, file_extension="webm").order_by("abr")[-1]

        a_tube.download(
            filename=self._INTER_AUDIO_NAME)
        if not intermediate:
            command = (f'ffmpeg -i "{self._INTER_AUDIO_NAME}" -c:a copy '
                       f'"{self._filename}.mp4"')

            call(command.strip(), shell=False, creationflags=0x00000008)
            remove(self._INTER_AUDIO_NAME)

            move_output_file(self._filename,
                             self.download_dir)

        return (a_tube.itag, a_tube.mime_type, a_tube.abr,
                a_tube.codecs[0], a_tube.is_progressive)

    def video_download(self, intermediate: bool = True):
        v_tube = self._video_obj.streams.filter(
            only_video=True, file_extension="webm"
        ).order_by("resolution")[-1]

        if intermediate:
            v_tube.download(
                filename=self._INTER_VIDEO_NAME)
        else:
            v_tube.download(self.download_dir,
                            filename=f"{self._filename}.{self.EXTENSION}")

        return (v_tube.itag, v_tube.mime_type,
                v_tube.resolution, v_tube.fps, v_tube.codecs[0],
                v_tube.is_progressive)

    def progressive_download(self):
        p_tube = self._video_obj.streams.filter(
            progressive=True).order_by("resolution")[-1]

        p_tube.download(self.download_dir,
                        filename=f"{self._filename}.{self.EXTENSION}")

        return (p_tube.itag, p_tube.mime_type,
                p_tube.resolution, p_tube.fps, *p_tube.codecs,
                p_tube.is_progressive)

    def av_download(self):
        a_tub = self.audio_download()
        v_tub = self.video_download()

        return a_tub, v_tub

    def download_auto(self):
        if self.download_type == "audio":
            return self.audio_download(intermediate=False)
        elif self.download_type == "video":
            return self.video_download(intermediate=False)
        elif self.download_type == "progressive":
            return self.progressive_download()
        elif self.download_type == "adaptive":
            av = self.av_download()

            command = (f'ffmpeg -i "{self._INTER_VIDEO_NAME}" -i '
                       f'"{self._INTER_AUDIO_NAME}" '
                       f'-c:v copy -c:a copy "{self._filename}.mp4"')

            call(command.strip(), shell=False, creationflags=0x00000008)
            remove(self._INTER_VIDEO_NAME)
            remove(self._INTER_AUDIO_NAME)

            move_output_file(self._filename, self.download_dir)
        else:
            raise ValueError(f"{self.download_type} is invalid.")

        return av


if __name__ == "__main__":
    url = ("https://www.youtube.com/playlist?"
           "list=PL-7D40vV1XjPWfRiVz8xRCkjLRucl17h-")
    down_dir = "D:\\OneDrive\\Music\\TESTING"
    x = PlaylistDownloader(url, down_dir, "audio",
                           threads=5)
    x.download_range(0)
