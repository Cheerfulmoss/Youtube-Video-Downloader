from pytube import Playlist
from pytube import YouTube
from subprocess import call
from os import getcwd, rename, replace, path
import os
import string
from threading import Thread
from pytube.exceptions import VideoRegionBlocked, VideoPrivate, MembersOnly, AgeRestrictedError, LiveStreamError

# Pytube file altered ( the captions file ) so captions can be generated

class VideoDownloader:
    def __init__(self, music_folder):
        self.current_folder = getcwd()
        self.music_folder = music_folder
        self.intermediate_filename = "output"
        
    def video_check(self, video_url):
        try:
            video_object = YouTube(video_url)
            return video_object
        except VideoRegionBlocked:
            print(f"Video {video_url} region locked")
            return False
        except VideoPrivate:
            print(f"Video {video_url} privated")
            return False
        except AgeRestrictedError:
            print(f"Video {video_url} age restricted")
            return False
        except MembersOnly:
            print(f"Video {video_url} members only")
            return False
        except LiveStreamError:
            print(f"Video {video_url} is a livestream")
            return False

    def cleanup(self):
        possible_files = ["audio_input.mp4", "video_input.mp4", "captions.srt", "output.mp4", "output_captions.mp4"]
        for file in possible_files:
            if path.exists(file):
                remove(file)

    def audio_only_download(self, video_object, download_path, for_merger=False):
        audio = video_object.streams.filter(file_extension="mp4", type="audio", only_audio=True).order_by("abr")[-1]
        if for_merger:
            audio.download(output_path=download_path, filename="audio_input.mp4")
        else:
            audio.download(output_path=download_path)
        return audio

    def video_only_download(self, video_object):
        video = video_object.streams.filter(file_extension="mp4", type="video", only_video=True).order_by("resolution")[-1]
        video.download(output_path=self.current_folder, filename="video_input.mp4")
        return video
    
    def captions_download(self, video_object):
        caption_codes = ["en", "a.en"]
        captions_exist = False
        subtitles = video_object.captions
        for code in caption_codes:
            if subtitles[code] != KeyError:
                # generate_srt_captions() is the edited part of the captions file 
                subtitle = subtitles[code].generate_srt_captions()
                captions_exist = True
                break
        if not captions_exist:
            return False
        printable_characters = string.printable
        # removes problematic letters
        clean_subtitle = "".join(filter(lambda x: x in printable_characters, subtitle))
        srt_file = open("captions.srt", "w")
        srt_file.write(clean_subtitle)
        srt_file.close()
        return True

    def download_video(self, video_object, audio_only, high_quality):
        if audio_only:
            self.audio_only_download(video_object, download_path=self.music_folder)
            print(f"{video_object.title} downloaded: audio only")
        else:
            if high_quality:
                self.cleanup()
                video_name = str(video_object.title)
                video_author = str(video_object.author)
                video_year = str(video_object.publish_date)
                # Video names sometimes have characters that aren't allowed in filenames
                filename = ""
                disallowed_character_set = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]
                for letter in video_name:
                    if letter not in disallowed_character_set:
                        filename = filename + letter
                # removes multiple spaces caused by character replacement above
                for n in range(20, 1, -1):
                    filename = filename.replace(" "*n, " ")
                threads = list()
                threads.append(Thread(target=self.audio_only_download, args=(video_object, self.current_folder, True)))
                threads.append(Thread(target=self.video_only_download, args=(video_object,)))
                # this is not multithreaded due to the need for a return value
                captions_exist = self.captions_download(video_object=video_object)
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()
                cmd = f'ffmpeg -i video_input.mp4 -i audio_input.mp4 -c:v copy -c:a aac -metadata author="{video_author}" -metadata year="{video_year}" -metadata title="{filename}" {self.intermediate_filename}.mp4'
                call(cmd, shell=False, creationflags=0x00000008)
                captions_added = False
                if captions_exist:
                    cmd = f'ffmpeg -i {self.intermediate_filename}.mp4 -i captions.srt -c copy -c:s mov_text {self.intermediate_filename}_captions.mp4'
                    call(cmd, shell=False, creationflags=0x00000008)
                    remove("captions.srt")
                    remove("output.mp4")
                    captions_added = True
                remove("video_input.mp4")
                remove("audio_input.mp4")
                # this is due to FFMPEG not being able to rename in place
                if captions_added:
                    self.intermediate_filename = "output_captions"
                n = 0
                if os.path.exists(self.music_folder + f"\\{filename}.mp4"):
                    while os.path.exists(self.music_folder + f"\\{filename}-({n}).mp4"):
                        n += 1
                    replace(self.music_folder + f"\\{self.intermediate_filename}-{n}.mp4", self.music_folder + f"\\{filename}-({n}).mp4")
                else:
                    replace(self.music_folder + f"\\{self.intermediate_filename}-{n}.mp4", self.music_folder + f"\\{filename}.mp4")
                print(f"{filename} downloaded: ffmpeg")
                self.cleanup()
            else:
                video_object.streams.filter(file_extension="mp4", progressive=True).order_by("resolution")[-1].download(output_path=self.music_folder)
                print(f"{video_object.title} downloaded: progressive")

    def download_playlist(self, url, audio_only, high_quality):
        for video_url in Playlist(url):
            video_object = self.video_check(video_url=video_url)
            if not video_object:
                continue
            self.download_video(video_object, audio_only=audio_only, high_quality=high_quality)

    def auto_download(self, video_url, audio_set, high_quality_set):
        if "list=" in video_url:
            self.download_playlist(video_url, audio_only=audio_set, high_quality=high_quality_set)
            print(f"Finished downloading playlist: {Playlist(video_url).title}")
        else:
            video_object = self.video_check(video_url=video_url)
            if not video_object:
                continue
            self.download_video(video_object, audio_only=audio_set, high_quality=high_quality_set)

    def list_input(self, video_list, audio_only):
        for video_url in video_list:
            video_object = self.video_check(video_url=video_url)
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
