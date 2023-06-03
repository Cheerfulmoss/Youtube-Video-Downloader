import os
import pytube
from pytube import YouTube
from pytube import Playlist
from subprocess import call
from os import remove, replace

audio_ret = tuple[int, str, str, str, bool]
video_ret = tuple[int, str, str, int, str, bool]
prog_ret = tuple[int, str, str, int, str, str, bool]
av_ret = tuple[audio_ret, video_ret]
down_sing_ret = video_ret | audio_ret | prog_ret | av_ret


class PlaylistDownloader:
    def __init__(self, url: str, download_dir: str | None,
                 video_only: bool = False, audio_only: bool = False,
                 progressive: bool = True, debug: bool = False) -> None:
        self._playlist_obj = Playlist(url=url)
        self._download_dir = download_dir
        self._video_only = video_only
        self._audio_only = audio_only
        self._progressive = progressive
        self._debug = debug
        if self._debug:
            print(f"{self.__class__.__name__}: Initialised\n"
                  f"\t{self._playlist_obj=}\n"
                  f"\t{self._download_dir=}\n"
                  f"\t{self._video_only=}\n"
                  f"\t{self._audio_only=}\n"
                  f"\t{self._progressive=}\n"
                  f"\t{self._debug=}"
                  )

    def download_all(self) -> tuple[down_sing_ret]:
        if self._debug:
            print(f"{self.__class__.__name__} - download_all: Started\n"
                  "\tCalling helper function download_range")
        all_ret = self.download_range()
        if self._debug:
            print(f"{self.__class__.__name__} - download_all: Complete!")
        return all_ret

    def download_range(self,
                       start: int = 0,
                       stop: int = None,
                       step: int = 1) -> tuple[down_sing_ret]:
        if self._debug:
            print(f"{self.__class__.__name__} - download_range: Started\n"
                  "\tStarting var checks")
        if start < 0:
            raise ValueError(f"start cannot be < 0, {start=}")
        if stop is not None and stop > len(self._playlist_obj):
            raise ValueError(f"stop cannot be greater than the length of the "
                             f"playlist, {stop=}, "
                             f"{len(self._playlist_obj)=}")
        if step <= 0:
            raise ValueError(f"step cannot be <= 0, {step=}")
        if self._debug:
            print("\tVar checks complete")
        video_stats = list()
        if stop is None:
            stop = len(self._playlist_obj)
        for i in range(start, stop, step):
            if self._debug:
                print("\tCalling class VideoDownloader.download_auto")
            s_return = VideoDownloader(
                url=self._playlist_obj[i], download_dir=self._download_dir,
                video_only=self._video_only, audio_only=self._audio_only,
                progressive=self._progressive,
                debug=self._debug).download_auto()
            if self._debug:
                print(f"{self.__class__.__name__} - download_range: "
                      f"Download complete\n"
                      f"\tAppending return values to video_stats")
            video_stats.append(s_return)
        if self._debug:
            print(f"{self.__class__.__name__} - download_range: Complete!")
        return tuple(video_stats)

class VideoDownloader:
    AUDIO_NAME = "audio.webm"
    VIDEO_NAME = "video.webm"

    def __init__(self, url: str, download_dir: str | None,
                 filename: str = None, video_only: bool = False,
                 audio_only: bool = False, progressive: bool = True,
                 debug: bool = False) -> None:
        self._youtube_obj = YouTube(url=url)
        self._download_dir = download_dir
        self._filename = self._make_filename(filename)
        self._video_only = video_only
        self._audio_only = audio_only
        self._progressive = progressive
        self._debug = debug
        if self._debug:
            print(f"{self.__class__.__name__}: Initialised\n"
                  f"\t{self._youtube_obj=}\n"
                  f"\t{self._download_dir=}\n"
                  f"\t{self._filename=}\n"
                  f"\t{self._video_only=}\n"
                  f"\t{self._audio_only=}\n"
                  f"\t{self._progressive=}\n"
                  )

    def _make_filename(self, filename: str | None) -> str:
        """Makes a filename.

        Precondition:
            If `filename` is not None it follows proper syntax for the
            operating system.

        Parameters:
            filename (str): The filename to save the video to.
        """
        if filename is not None:
            return filename
        filename = "".join(
            char
            for char in self._youtube_obj.title
            if char not in ["<", ">", ":", '"', "/", "\\", "|", "?", '*']
        )
        for num_spaces in range(10, 0, -1):
            filename.replace(" " * num_spaces, " ")
        return filename

    def audio_download(
            self,
            filename: str = None, intermediate: bool = True
    ) -> audio_ret:
        """Downloads only the audio from a YouTube video.

        Returns:
            A tuple containing (itag, mime type, audio bitrate, codec,
            if it's progressive). Mime type says what type of file and if it's
            audio or video (if the video is progressive it always returns as
            video/filetype).
        """
        if self._debug:
            print(f"{self.__class__.__name__} - audio_download: Started")
        a_tube = self._youtube_obj.streams.filter(
            only_audio=True, file_extension="webm").order_by("abr")[-1]
        if self._debug:
            print("\tHighest quality audio file found\n\t\t"
                  f"{a_tube}\n\tDownload beginning...")
        if intermediate:
            a_tube.download(filename=filename)
        else:
            a_tube.download(self._download_dir, filename=filename)
        if self._debug:
            print("\tDownload complete!")
        return (a_tube.itag, a_tube.mime_type, a_tube.abr,
                a_tube.codecs[0], a_tube.is_progressive)

    def video_download(
            self,
            filename: str = None, intermediate: bool = True
    ) -> video_ret:
        """Downloads only the video from a YouTube video.

        Returns:
            A tuple containing (itag, mime type, resolution, fps, codec,
            if it's progressive). Mime type says what type of file and if it's
            audio or video (if the video is progressive it always returns as
            video/filetype).
        """
        if self._debug:
            print(f"{self.__class__.__name__} - video_download: Started")
        v_tube = self._youtube_obj.streams.filter(
            only_video=True, file_extension="webm"
        ).order_by("resolution")[-1]
        if self._debug:
            print("\tHighest quality video file found\n\t\t"
                  f"{v_tube}\n\tDownload beginning...")
        if intermediate:
            v_tube.download(filename=filename)
        else:
            v_tube.download(self._download_dir, filename=filename)
        if self._debug:
            print("\tDownload complete!")
        return (v_tube.itag, v_tube.mime_type,
                v_tube.resolution, v_tube.fps, v_tube.codecs[0],
                v_tube.is_progressive)

    def progressive_download(
            self,
            filename: str = None, intermediate: bool = True
    ) -> prog_ret:
        """Downloads progressive videos (capped at 720p), which bundles
            audio/video into one download.

        Returns:
            A tuple containing (itag, mime type, resolution, fps, aurdio
            code, video codec, if it's progressive). Mime type says what type
            of file and if it's audio or video (if the video is progressive
            it always returns as video/filetype).
        """
        if self._debug:
            print(f"{self.__class__.__name__} - progressive_download: Started")
        p_tube = self._youtube_obj.streams.filter(
            progressive=True).order_by("resolution")[-1]
        if self._debug:
            print("\tHighest quality progressive file found\n\t\t"
                  f"{p_tube}\n\tDownload beginning...")
        if intermediate:
            p_tube.download(filename=filename)
        else:
            p_tube.download(self._download_dir, filename=filename)
        if self._debug:
            print("\tDownload complete!")
        return (p_tube.itag, p_tube.mime_type,
                p_tube.resolution, p_tube.fps, *p_tube.codecs,
                p_tube.is_progressive)

    def audio_video_download(self) -> av_ret:
        if self._debug:
            print(f"{self.__class__.__name__} - audio_video_download: Started")
            print(f"{self.__class__.__name__} - audio_video_download: Calling "
                  "audio_download")
        a_tub = self.audio_download(filename=self.AUDIO_NAME)
        if self._debug:
            print(f"{self.__class__.__name__} - audio_video_download: Calling "
                  f"video_download")
        v_tub = self.video_download(filename=self.VIDEO_NAME)
        if self._debug:
            print(f"{self.__class__.__name__} - audio_video_download: "
                  f"complete!")
        return a_tub, v_tub

    def download_auto(
            self
    ) -> down_sing_ret:
        if self._debug:
            print(f"{self.__class__.__name__} - download_auto: Started")
        if self._video_only:
            if self._debug:
                print("\tVideo only mode")
            return self.video_download(intermediate=False)
        elif self._audio_only:
            if self._debug:
                print("\tAudio only mode")
            return self.audio_download(intermediate=False)
        elif self._progressive:
            if self._debug:
                print("\tProgressive mode")
            return self.progressive_download(intermediate=False)
        if self._debug:
            print("\tAdaptive mode\n\tCalling audio_video_download")
        av = self.audio_video_download()
        if self._debug:
            print(f"{self.__class__.__name__} - download_auto: "
                  f"audio_video_download complete")
        command = f"""
        ffmpeg -i "{self.VIDEO_NAME}" -i "{self.AUDIO_NAME}" -c:v copy -c:a copy "{self._filename}.mp4"
        """
        if self._debug:
            print(f"{self.__class__.__name__} - download_auto: "
                  f"Calling ffmpeg | {command.strip()}")
        call(command.strip(), shell=False, creationflags=0x00000008)
        remove(self.AUDIO_NAME)
        remove(self.VIDEO_NAME)
        if self._debug:
            print(f"{self.__class__.__name__} - download_auto: "
                  f"Moving output file")
        replace(
            f"{self._filename}.mp4",
            f"{self._download_dir}\\{self._filename}.mp4"
        )
        if self._debug:
            print(f"{self.__class__.__name__} - download_auto: Complete!")
        return av
    
