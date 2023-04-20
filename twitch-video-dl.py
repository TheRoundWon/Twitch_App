from dotenv import load_dotenv
from datetime import datetime, timedelta, date
import time
from StreamMaster import *
from _utils import *
load_dotenv()
import argparse

import subprocess

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--limits", type=int, nargs = "?", help="number of videos to process, default None for All undownloaded videos")
parser.add_argument("-m", "--mode", type=str, nargs = "?", default='a', help="Options are 'a' for all, 'h' for highlights or 'c' for clips")

args = parser.parse_args()


def twitch_video_pull(session_engine, mode, limits):
        clips_folder = os.environ['CLIPS_FOLDER']
        mobile_folder = os.environ['MOBILE_FOLDER']
        highlight_folder = os.environ['HIGHLIGHT_FOLDER']

        folder_mapper = {TwitchVideoStyle.HIGHLIGHT: highlight_folder, TwitchVideoStyle.CLIP: clips_folder}

        with Session(session_engine) as session:


                # Download the undownloaded videos
                if not bool(limits):
                        for video_name, url, ID in session.query(TwitchVideos.video_name, TwitchVideos.url, TwitchVideos.id).where(TwitchVideos.downloaded == False).where(TwitchVideos.video_type == mode).all():

                                try:
                                        subprocess.call(['twitch-dl', 'download', '-q', 'source', url, '-o', os.path.join(folder_mapper[mode], video_name)])
                                        session.execute(update(TwitchVideos).where(TwitchVideos.id == ID).values(downloaded=True))
                                        session.commit()
                                except Exception as e:
                                        print(url)
                                print("All Done!")
                else:
                        for video_name, url, ID in session.query(TwitchVideos.video_name, TwitchVideos.url, TwitchVideos.id).where(TwitchVideos.downloaded == False).where(TwitchVideos.video_type == mode).all()[:limits]:

                                try:
                                        subprocess.call(['twitch-dl', 'download', '-q', 'source', url, '-o', os.path.join(folder_mapper[mode], video_name)])
                                        session.execute(update(TwitchVideos).where(TwitchVideos.id == ID).values(downloaded=True))
                                        session.commit()
                                except Exception as e:
                                        print(url)
                                print("All Done!")

if __name__ == '__main__':

        if args.mode == 'a':
                twitch_video_pull(mysql_engine, TwitchVideoStyle.CLIP, args.limits)
                twitch_video_pull(mysql_engine, TwitchVideoStyle.HIGHLIGHT, args.limits)
        elif args.mode == 'c':
                twitch_video_pull(mysql_engine, TwitchVideoStyle.CLIP, args.limits)
        else:
                twitch_video_pull(mysql_engine, TwitchVideoStyle.HIGHLIGHT, args.limits)