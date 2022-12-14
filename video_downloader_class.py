from pytube import Playlist
from pytube import YouTube
from subprocess import call
from os import getcwd, remove, replace, path
import os
import string
from threading import Thread

# Pytube file altered ( the captions file ) so captions can be generated


# --- Cleans up the text from filenames or captions --- #
def clean_text(text, is_filename: bool = False):
    if is_filename:
        filename = ""
        disallowed_character_set = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
        for letter in text:
            if letter not in disallowed_character_set:
                filename = filename + letter
        for n in range(20, 1, -1):
            filename = filename.replace(" " * n, " ")
        return filename
    printable_characters = string.printable
    clean_text = "".join(filter(lambda x: x in printable_characters, text))
    for n in range(20, 1, -1):
        clean_text = clean_text.replace(" " * n, " ")
    return clean_text


# --- Gets rid of the temp files --- #
def cleanup(degree=None, less_than=True):
    # --- Each value is to differentiate what to delete when cleaning up --- #
    possible_files = {"test.mp4": 0, "audio_input.mp4": 1, "video_input.mp4": 1, "captions.srt": 1, "output.mp4": 2,
                      "output_captions.mp4": 3}
    if degree is None:
        degree = max(possible_files.values())
    for file in possible_files:
        if less_than:
            if possible_files[file] <= degree and path.exists(file):
                remove(file)
        else:
            if possible_files[file] == degree and path.exists(file):
                remove(file)


def audio_only_download(video_object, download_path, for_merger=False):
    # --- When ordering the possible downloads it goes from worst -> best --- #
    audio = video_object.streams.filter(file_extension="mp4", type="audio", only_audio=True).order_by("abr")[-1]
    if for_merger:
        audio.download(output_path=download_path, filename="audio_input.mp4")
    else:
        audio.download(output_path=download_path)
    return audio


def captions_download(video_object):
    # --- a.en is automatic english --- #
    caption_codes = ["en", "a.en"]
    captions_exist = False
    subtitles = video_object.captions
    for code in caption_codes:
        try:
            subtitle = subtitles[code].generate_srt_captions()
            captions_exist = True
            break
        except KeyError:
            pass
    if not captions_exist:
        return False
    clean_subtitle = clean_text(text=subtitle)
    srt_file = open("captions.srt", "w")
    srt_file.write(clean_subtitle)
    srt_file.close()
    return True


# --- Checks if the video can be downloaded --- #
def video_check(video_url):
    video_object = YouTube(video_url)
    try:
        video_object.streams.filter(file_extension="mp4", only_audio=True).order_by("abr")[0].download(
            filename="test.mp4")
        cleanup(degree=0, less_than=False)
        return video_object
    except KeyError:
        return False


class VideoDownloader:
    def __init__(self, music_folder):
        self.current_folder = getcwd()
        self.music_folder = music_folder

    def video_only_download(self, video_object):
        # --- When ordering the possible downloads it goes from worst -> best --- #
        video = video_object.streams.filter(file_extension="mp4", type="video", only_video=True).order_by("resolution")[-1]
        video.download(output_path=self.current_folder, filename="video_input.mp4")
        return video

    # --- Despite the backwards naming this downloads both video and audio --- #
    def download_video(self, video_object, audio_only, high_quality):
        if audio_only:
            audio_only_download(video_object, download_path=self.music_folder)
            print(f"{video_object.title} downloaded: audio only")
            return
        if high_quality:
            intermediate_filename = "output"
            cleanup()
            video_name, video_author, video_year = str(video_object.title), str(video_object.author), str(video_object.publish_date)
            # Video names sometimes have characters that aren't allowed in filenames
            filename = clean_text(text=video_name, is_filename=True)
            threads = list()
            threads.append(Thread(target=audio_only_download, args=(video_object, self.current_folder, True)))
            threads.append(Thread(target=self.video_only_download, args=(video_object,)))
            captions_exist = captions_download(video_object=video_object)
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            cmd = f'ffmpeg -i video_input.mp4 -i audio_input.mp4 -c:v copy -c:a aac -metadata author="{video_author}" -metadata year="{video_year}" -metadata title="{filename}" {intermediate_filename}.mp4'
            call(cmd, shell=False, creationflags=0x00000008)
            captions_added = False
            if captions_exist:
                cmd = f'ffmpeg -i {intermediate_filename}.mp4 -i captions.srt -c copy -c:s mov_text {intermediate_filename}_captions.mp4'
                call(cmd, shell=False, creationflags=0x00000008)
                captions_added = True

            cleanup(degree=1)

            if captions_added:
                intermediate_filename = "output_captions"
            file_iterator = 0
            if os.path.exists(f"{self.music_folder}\\{filename}.mp4"):
                while os.path.exists(f"{self.music_folder}\\{filename}-({file_iterator}).mp4"):
                    file_iterator += 1
                replace(self.current_folder + f"\\{intermediate_filename}.mp4", self.music_folder + f"\\{filename}-({file_iterator}).mp4")
                return
            replace(self.current_folder + f"\\{intermediate_filename}.mp4", self.music_folder + f"\\{filename}.mp4")
            print(f"{filename} downloaded: ffmpeg")
            cleanup()
            return
        video_object.streams.filter(file_extension="mp4", progressive=True).order_by("resolution")[-1].download(
            output_path=self.music_folder)
        print(f"{video_object.title} downloaded: progressive")

    def download_playlist(self, url, audio_only, high_quality):
        for video_url in Playlist(url):
            video_object = video_check(video_url=video_url)
            if not video_object:
                continue
            self.download_video(video_object, audio_only=audio_only, high_quality=high_quality)

    def auto_download(self, video_url, audio_set, high_quality_set):
        if "list=" in video_url:
            self.download_playlist(video_url, audio_only=audio_set, high_quality=high_quality_set)
            print(f"Finished downloading playlist: {Playlist(video_url).title}")
        else:
            video_object = video_check(video_url=video_url)
            if not video_object:
                return
            self.download_video(video_object, audio_only=audio_set, high_quality=high_quality_set)

    def list_input(self, video_list, audio_only):
        for video_url in video_list:
            video_object = video_check(video_url=video_url)
            if not video_object:
                continue
            self.download_video(video_object, audio_only=audio_only, high_quality=False)

    def threaded_download(self, video_url, audio_set, num_threads=5):
        if "list=" in video_url:
            playlist_object = Playlist(video_url)
            playlist_list = list(playlist_object)
            split_list = [playlist_list[i::num_threads] for i in range(num_threads)]
            threads = list()
            for index in range(num_threads):
                t = Thread(target=self.list_input, args=(split_list[index], audio_set))
                threads.append(t)
            for thread in threads:
                thread.start()
        else:
            self.auto_download(video_url=video_url, audio_set=audio_set, high_quality_set=False)
