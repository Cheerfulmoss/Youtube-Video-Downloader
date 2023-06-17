import os
import threading
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


def check_range_vars(start: int, stop: int, step: int, array_len: int,
                     debug: bool, class_name: str, func_name: str) -> None:
    """Checks to see if start, stop and step are valid when specifying a
        custom range.

    Parameters:
        start (int): The starting index.
        stop (int): The ending index.
        step (int): The increment per iteration.
        array_len (int): The length of the array being sliced.
        debug (bool): True to display debug prints False to hide them.
        class_name (str): The class name (used in the debug prints).
        func_name (str): The function name (used in the debug prints).
    """
    if debug:
        print(f"{class_name} - {func_name} - check_range_vars: Started")
    if start < 0:
        raise ValueError(f"start cannot be < 0, {start=}")
    if stop is not None and stop > array_len:
        raise ValueError(f"stop cannot be greater than the length of the "
                         f"playlist, {stop=}, "
                         f"{array_len=}")
    if step <= 0:
        raise ValueError(f"step cannot be <= 0, {step=}")
    if debug:
        print(f"{class_name} - {func_name} - check_range_vars: Completed!")


def move_output_file(filename: str, directory: str, class_name: str,
                     func_name: str, debug: bool) -> None:
    """Moves the specified file to the specified directory.

    Preconditions:
        Files must be in the CWD (current working directory)

    Parameters:
        filename (str): The name of the file.
        directory (str): The complete or relative directory path.
        debug (bool): True to display debug prints False to hide them.
        class_name (str): The class name (used in the debug prints).
        func_name (str): The function name (used in the debug prints).
    """
    if debug:
        print(f"{class_name} - {func_name}: "
              f"Moving output file")

    try:
        replace(
            f"{filename}.mp4",
            f"{directory}\\{filename}.mp4"
        )
    except FileNotFoundError:
        remove(f"{os.getcwd()}\\{filename}.mp4")
        if os.path.exists(f"{os.getcwd()}\\{directory}"):
            raise FileNotFoundError
        else:
            raise NotADirectoryError


class PlaylistDownloader:
    """Used when downloading playlists instead of single files.
    """

    def __init__(self, url: str, download_dir: str | None,
                 video_only: bool = False, audio_only: bool = False,
                 progressive: bool = True, debug: bool = False,
                 threaded: bool = False, threads: int = 5) -> None:
        """Initialises the PlaylistDownloader object.

        Parameters:
            url (str): The playlist url (Youtube only).
            download_dir (str): The directory to place the files into.
            video_only (bool): Only download videos (limited to webm format)
            audio_only (bool): Only download audio files (Defaults to webm
                               format).
            progressive (bool): A specific type of video format that combines
                                audio and video into one download (limited to
                                720p).
            debug (bool): True to display debug prints False to hide them.
            threaded (bool): True to make the download threaded.
            threads (int): Max number of threads to utilise when `threaded` is
                            True
        """
        self._playlist_obj = Playlist(url=url)
        self._download_dir = download_dir
        self._video_only = video_only
        self._audio_only = audio_only
        self._progressive = progressive
        self._debug = debug
        self._threaded = threaded

        self._threads = threads

        if self._debug:
            print(f"{self.__class__.__name__}: Initialised\n"
                  f"\t{self._playlist_obj=}\n"
                  f"\t{self._download_dir=}\n"
                  f"\t{self._video_only=}\n"
                  f"\t{self._audio_only=}\n"
                  f"\t{self._progressive=}\n"
                  f"\t{self._debug=}"
                  )

    def download_all_threaded(self) -> None:
        """Downloads the entire playlist using the number of threads given on
            initialisation."""
        if self._debug:
            print(f"{self.__class__.__name__} - download_all_threaded: "
                  f"Started\n"
                  "\tCalling helper function download_range_threaded")
        self.download_range_threaded()
        if self._debug:
            print(f"{self.__class__.__name__} - download_all_threaded: "
                  f"Complete!")

    def download_range_threaded(
            self,
            start: int = 0,
            stop: int = None,
            step: int = 1) -> None:
        """Downloads from the playlist starting at `start` and ending at
        `stop` using the step of `step`, utilizing all the available threads
        given on initialisation.

        Parameters:
            start (int): The index to start downloading from.
            stop (int): The index to stop at (non-inclusive).
            step (int): The step per iteration.
        """
        if self._debug:
            print(f"{self.__class__.__name__} - download_range_threaded: "
                  f"Started")

        check_range_vars(start, stop, step, len(self._playlist_obj),
                         self._debug, self.__class__.__name__,
                         "download_range_threaded")

        download_complete = False
        index = start
        stop = (len(self._playlist_obj) if stop is None else stop)
        threads = list()

        while not download_complete:
            if len(self._playlist_obj) <= index or index >= stop:
                download_complete = True
                continue

            # The number of threads includes all threads including the main
            # thread (and in the case of incorporating GUI into this it would
            # also include the thread that the GUI is running in) so to get an
            # accurate count of the number of threads being used for actual
            # downloading we loop through the currently running threads (
            # using threading.enumerate()) and check if "download" is in
            # their name, if so it's a downloading thread, and we can count it
            # as an "active thread".
            active_count = len([thread for thread in threading.enumerate()
                                if "download" in thread.name])

            if active_count < self._threads:
                if self._debug:
                    print(f"{self.__class__.__name__} - "
                          f"download_range_threaded: "
                          f"Starting thread, {index}, TC "
                          f"{active_count} :"
                          f" {self._playlist_obj[index]}")

                # Here we initialise a thread object, we then append it to a
                # list of threads (I will get to why in a later comment) and
                # then we start the thread. Here we also name the thread
                # "download". (Threads can have the same name as it's not
                # "used" for anything per se)
                thread = threading.Thread(target=self._single_download,
                                          args=(index,), name="download")
                threads.append(thread)
                thread.start()
                index += step

        # Here we loop through the list of threads, what this does is if it
        # runs into a thread that is still running it will wait for that
        # thread to finish before moving on.
        for thread in threads:
            thread.join()
        if self._debug:
            print(f"{self.__class__.__name__} - download_range_threaded: "
                  f"Complete!")
        # You'll notice that I throw away the output from the VideoDownloader
        # class this is just because I'm lazy and can't work out how to get
        # the output back from the thread. :)

    def _single_download(self, index: int) -> None:
        """Download a single video, used in multithreading as a hacky
        solution"""
        VideoDownloader(
            url=self._playlist_obj[index], download_dir=self._download_dir,
            video_only=self._video_only, audio_only=self._audio_only,
            progressive=self._progressive,
            debug=self._debug, thread_num=index).download_auto()

    def download_all(self) -> tuple[down_sing_ret] | None:
        """Downloads the entire playlist, if threading is enabled calls the
        `download_all_threaded` function, this is the main interface for the
        PlaylistDownloader class however the others can be used, this one
        simply handles some of the logic.
        ."""
        if self._debug:
            print(f"{self.__class__.__name__} - download_all: Started\n"
                  "\tCalling helper function download_range")
        all_ret = None
        if self._threaded:
            self.download_all_threaded()
        else:
            all_ret = self.download_range()
        if self._debug:
            print(f"{self.__class__.__name__} - download_all: Complete!")
        return all_ret

    def download_range(self,
                       start: int = 0,
                       stop: int = None,
                       step: int = 1) -> tuple[down_sing_ret]:
        """Downloads from the playlist starting at `start` and ending at
        `stop` using the step of `step`.

        Parameters:
            start (int): The index to start downloading from.
            stop (int): The index to stop at (non-inclusive).
            step (int): The step per iteration.
        """
        if self._debug:
            print(f"{self.__class__.__name__} - download_range: Started")

        check_range_vars(start, stop, step, len(self._playlist_obj),
                         self._debug, self.__class__.__name__,
                         "download_range")
        video_stats = list()
        stop = (len(self._playlist_obj) if stop is None else stop)

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
    """Used when downloading singular videos.
    """
    AUDIO_NAME = "audio"
    VIDEO_NAME = "video"

    EXTENSION = "webm"

    def __init__(self, url: str, download_dir: str | None,
                 filename: str = None, video_only: bool = False,
                 audio_only: bool = False, progressive: bool = True,
                 debug: bool = False, thread_num: int = 0) -> None:
        self._youtube_obj = YouTube(url=url)
        self._download_dir = download_dir
        self._filename = self._make_filename(filename)
        self._video_only = video_only
        self._audio_only = audio_only
        self._progressive = progressive
        self._debug = debug

        self._audio_name = f"{self.AUDIO_NAME}_{thread_num}.{self.EXTENSION}"
        self._video_name = f"{self.VIDEO_NAME}_{thread_num}.{self.EXTENSION}"

        if self._debug:
            print(f"{self.__class__.__name__}: Initialised\n"
                  f"\t{self._youtube_obj=}\n"
                  f"\t{self._download_dir=}\n"
                  f"\t{self._filename=}\n"
                  f"\t{self._video_only=}\n"
                  f"\t{self._audio_only=}\n"
                  f"\t{self._progressive=}\n"
                  f"\t{thread_num=}\n"
                  f"\t{self._audio_name=}\n"
                  f"\t{self._video_name=}\n"
                  )

    def _make_filename(self, filename: str | None) -> str:
        """Makes a filename following Windows filename convention.

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
        # Remove any repeated spaces caused by removing disallowed characters.
        for num_spaces in range(10, 0, -1):
            filename = filename.replace(" " * num_spaces, " ")
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

        # Gets the greatest abr (audio bit rate) webm audio file.
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

        # Gets the highest resolution webm video file.
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

        # Gets the highest resolution progressive video.
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
        """Downloads the audio and video files."""
        if self._debug:
            print(f"{self.__class__.__name__} - audio_video_download: Started")
            print(f"{self.__class__.__name__} - audio_video_download: Calling "
                  "audio_download")

        a_tub = self.audio_download(filename=self._audio_name)

        if self._debug:
            print(f"{self.__class__.__name__} - audio_video_download: Calling "
                  f"video_download")

        v_tub = self.video_download(filename=self._video_name)

        if self._debug:
            print(f"{self.__class__.__name__} - audio_video_download: "
                  f"complete!")
        return a_tub, v_tub

    def download_auto(
            self
    ) -> down_sing_ret:
        """This is the main interface to use the VideoDownloader class when
        downloading videos (also the only interface that allows for the
        highest quality downloads), all others can be used this one just does
        all the logic for you.
        """
        if self._debug:
            print(f"{self.__class__.__name__} - download_auto: Started")

        if self._video_only:
            if self._debug:
                print("\tVideo only mode")

            return self.video_download(intermediate=False)
        elif self._audio_only:
            if self._debug:
                print("\tAudio only mode")

            a_ret = self.audio_download(intermediate=True,
                                        filename=self._audio_name)

            # All this does is convert the webm format to mp4.
            command = f"""
            ffmpeg -i "{self._audio_name}" -c:a copy "{self._filename}.mp4"
            """
            if self._debug:
                print(f"{self.__class__.__name__} - download_auto: "
                      f"Calling ffmpeg | {command.strip()}")

            call(command.strip(), shell=False, creationflags=0x00000008)
            remove(self._audio_name)

            move_output_file(self._filename, self._download_dir,
                             self.__class__.__name__, "download_auto",
                             self._debug)
            return a_ret
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

        # Combines the individual audio and video streams into a single file
        # using ffmpeg.
        command = f"""
        ffmpeg -i "{self._video_name}" -i "{self._audio_name}" -c:v copy -c:a copy "{self._filename}.mp4"
        """
        if self._debug:
            print(f"{self.__class__.__name__} - download_auto: "
                  f"Calling ffmpeg | {command.strip()}")
        
        call(command.strip(), shell=False, creationflags=0x00000008)
        remove(self._audio_name)
        remove(self._video_name)

        move_output_file(self._filename, self._download_dir,
                         self.__class__.__name__, "download_auto",
                         self._debug)

        if self._debug:
            print(f"{self.__class__.__name__} - download_auto: Complete!")
        return av
