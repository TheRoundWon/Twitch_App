import os
import sys

import pandas as pd
import numpy as np
import subprocess
# import cv2
import uuid


import time
from dotenv import load_dotenv

load_dotenv()
from collections import defaultdict
from sqlalchemy import *
from sqlalchemy.orm import declarative_base, relationship, Session, aliased
from datetime import datetime, timedelta, date
import argparse
from sqlalchemy.util._collections import immutabledict
from StreamMaster import *
from _utils import *

# Initialize starting variables of key folders needed for this process
clips_folder = os.environ['CLIPS_FOLDER']
mobile_folder = os.environ['MOBILE_FOLDER']
inprocess_folder = os.environ['IN_PROCESS_HIGHLIGHTS']
highlight_folder = os.environ['HIGHLIGHT_FOLDER']
ml_folder = os.environ['ML_FOLDER']
assets = os.environ['ASSETS']


# Connecting to a rasberry pi sql data base, mysql was in this instance

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--limits", type=int, nargs = "?", const=1, default=5, help="number of videos to process")
parser.add_argument("-m", "--mode", type=str, nargs = "?", default='a', help="Options are 'a' for all, 'h' for highlights or 'c' for clips")
args = parser.parse_args()


def twitch_shorts_processing(args, session_engine):
    with Session(session_engine) as session:
        if args.limits > 0:
            for fil, mb_pc in session.query(TwitchVideos.video_name, TwitchVideos.mobiles_videos_processed).where(and_(TwitchVideos.mobiles_videos_processed == False, TwitchVideos.video_type == TwitchVideoStyle.CLIP )).order_by(TwitchVideos.view_count.desc()).all()[:args.limits]:
                with VideoFileClip(os.path.join(clips_folder, fil)) as video:
                    width, height = video.size
                    x_center = width //2
                    rng = int(height*(9/16))
                    x1 = x_center - (rng//2)
                    x2 = x_center + (rng//2)
                if not bool(mb_pc):
                    create_mobile_video(os.environ['LOGO'], os.path.join(clips_folder, fil), os.path.join(mobile_folder, fil), x_center,614, height)
                    session.execute(update(TwitchVideos).where(TwitchVideos.video_name == fil).values({"mobiles_videos_processed": True}))
                    session.commit()
                # if not bool(ft_pc):
                #     create_full_video(os.environ['LOGO'], os.path.join(TwitchVideos_folder, fil), os.path.join(fullscreen_folder, fil))
                #     session.execute(update(TwitchVideos).where(TwitchVideos.video_name == fil).values({"full_screen_videos_processed": True}))
                #     session.commit()
               
                print("Finished", fil)
        else:
            for fil, mb_pc in session.query(TwitchVideos.video_name,  TwitchVideos.mobiles_videos_processed).where(and_(TwitchVideos.mobiles_videos_processed == False, TwitchVideos.video_type == TwitchVideoStyle.CLIP )).order_by(TwitchVideos.view_count.desc()).all():
                with VideoFileClip(os.path.join(clips_folder, fil)) as video:
                    width, height = video.size
                    x_center = width //2
                    rng = int(height*(9/16))
                    x1 = x_center - (rng//2)
                    x2 = x_center + (rng//2)
                if not bool(mb_pc):
                    create_mobile_video(os.environ['LOGO'], os.path.join(clips_folder, fil), os.path.join(mobile_folder, fil), x_center,614, height)
                    session.execute(update(TwitchVideos).where(TwitchVideos.video_name == fil).values({"mobiles_videos_processed": True}))
                    session.commit()
                # if not bool(ft_pc):
                #     create_full_video(os.environ['LOGO'], os.path.join(TwitchVideos_folder, fil), os.path.join(fullscreen_folder, fil))
                #     session.execute(update(TwitchVideos).where(TwitchVideos.video_name == fil).values({"full_screen_videos_processed": True}))
                #     session.commit()
                print("Finished", fil)


def twitch_highlights_processing(args, session_engine):
    with Session(session_engine) as session:
        if args.limits > 0:
            for fil, mb_pc in session.query(TwitchVideos.video_name, TwitchVideos.mobiles_videos_processed).where(and_(TwitchVideos.mobiles_videos_processed == False, TwitchVideos.video_type == TwitchVideoStyle.HIGHLIGHT )).order_by(TwitchVideos.view_count.desc()).all()[:args.limits]:
           
            
                if not bool(mb_pc):
                    create_full_video(os.environ['LOGO'], os.path.join(highlight_folder, fil), os.path.join(inprocess_folder, fil))
                    session.execute(update(TwitchVideos).where(TwitchVideos.video_name == fil).values({"mobiles_videos_processed": True}))
                    session.commit()
               
                print("Finished", fil)
        else:
            for fil, mb_pc in session.query(TwitchVideos.video_name,  TwitchVideos.mobiles_videos_processed).where(and_(TwitchVideos.mobiles_videos_processed == False, TwitchVideos.video_type == TwitchVideoStyle.HIGHLIGHT )).order_by(TwitchVideos.view_count.desc()).all():
               
        
                if not bool(mb_pc):
                    create_full_video(os.environ['LOGO'], os.path.join(highlight_folder, fil), os.path.join(inprocess_folder, fil))
                    session.execute(update(TwitchVideos).where(TwitchVideos.video_name == fil).values({"mobiles_videos_processed": True}))
                    session.commit()
                print("Finished", fil)

if __name__ == '__main__':
    if args.mode == 'a':
        twitch_shorts_processing(args, mysql_engine)
        twitch_highlights_processing(args, mysql_engine)
    elif args.mode == 'c':
        twitch_shorts_processing(args, mysql_engine)
    else:
        twitch_highlights_processing(args, mysql_engine)