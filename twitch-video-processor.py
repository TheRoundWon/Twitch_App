import os
import sys
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope
import pandas as pd
import numpy as np
import subprocess
# import cv2
import uuid
from moviepy.editor import *
import moviepy.video as mpy
import time
from dotenv import load_dotenv
from moviepy.video.tools.drawing import color_split
load_dotenv()
from collections import defaultdict
from sqlalchemy import *
from sqlalchemy.orm import declarative_base, relationship, Session, aliased
from datetime import datetime, timedelta, date
import argparse
from sqlalchemy.util._collections import immutabledict
import ffmpeg
from StreamMaster import *
from _utils import *

# Initialize starting variables of key folders needed for this process
clips_folder = os.environ['CLIPS_FOLDER']
mobile_folder = os.environ['MOBILE_FOLDER']
fullscreen_folder = os.environ['FULLSCREEN_FOLDER']
ml_folder = os.environ['ML_FOLDER']
assets = os.environ['ASSETS']


# Connecting to a rasberry pi sql data base, mysql was in this instance

parser = argparse.ArgumentParser()
parser.add_argument("cycles", type=int, nargs = "?", const=1, default=5, help="number of videos to process")

args = parser.parse_args()


def main(args, engine):
    with Session(engine) as session:
        if args.cycles > 0:
            for fil, ft_pc, mb_pc in session.query(Clip_Tracker.video_name, Clip_Tracker.full_screen_videos_processed, Clip_Tracker.mobiles_videos_processed).where(or_(Clip_Tracker.mobiles_videos_processed == False, Clip_Tracker.full_screen_videos_processed == False)).order_by(Clip_Tracker.view_count.desc()).all()[:args.cycles]:
                with VideoFileClip(os.path.join(clips_folder, fil)) as video:
                    width, height = video.size
                    x_center = width //2
                    rng = int(height*(9/16))
                    x1 = x_center - (rng//2)
                    x2 = x_center + (rng//2)
                if not bool(mb_pc):
                    create_mobile_video(os.environ['LOGO'], os.path.join(clips_folder, fil), os.path.join(mobile_folder, fil), x_center,614, height)
                    session.execute(update(Clip_Tracker).where(Clip_Tracker.video_name == fil).values({"mobiles_videos_processed": True}))
                    session.commit()
                if not bool(ft_pc):
                    create_full_video(os.environ['LOGO'], os.path.join(clips_folder, fil), os.path.join(fullscreen_folder, fil))
                    session.execute(update(Clip_Tracker).where(Clip_Tracker.video_name == fil).values({"full_screen_videos_processed": True}))
                    session.commit()
               
                print("Finished", fil)
        else:
            for fil, ft_pc, mb_pc in session.query(Clip_Tracker.video_name, Clip_Tracker.full_screen_videos_processed, Clip_Tracker.mobiles_videos_processed).where(or_(Clip_Tracker.full_screen_videos_processed == False, Clip_Tracker.mobiles_videos_processed == False)).order_by(Clip_Tracker.view_count.desc()).all():
                with VideoFileClip(os.path.join(clips_folder, fil)) as video:
                    width, height = video.size
                    x_center = width //2
                    rng = int(height*(9/16))
                    x1 = x_center - (rng//2)
                    x2 = x_center + (rng//2)
                if not bool(mb_pc):
                    create_mobile_video(os.environ['LOGO'], os.path.join(clips_folder, fil), os.path.join(mobile_folder, fil), x_center,614, height)
                    session.execute(update(Clip_Tracker).where(Clip_Tracker.video_name == fil).values({"mobiles_videos_processed": True}))
                    session.commit()
                if not bool(ft_pc):
                    create_full_video(os.environ['LOGO'], os.path.join(clips_folder, fil), os.path.join(fullscreen_folder, fil))
                    session.execute(update(Clip_Tracker).where(Clip_Tracker.video_name == fil).values({"full_screen_videos_processed": True}))
                    session.commit()
                print("Finished", fil)

if __name__ == '__main__':
    main(args, engine)