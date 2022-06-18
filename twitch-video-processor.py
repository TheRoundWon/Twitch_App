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

from StreamMaster import *


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

def createMobileVideo(logo, baseclip, rng, height ):
    mask = color_split((rng, height), col1=1, col2=0, y=300)
                    
    mask_clip = ImageClip(mask, ismask=True)
    clip_top = logo.set_mask(mask_clip)

    mask = color_split((rng, height), col1=0, col2=1, y=1)
                    
    mask_clip = ImageClip(mask, ismask=True)

    clip_bottom = baseclip.set_mask(mask_clip)

    return CompositeVideoClip([clip_top.set_pos((0, 20)), clip_bottom.set_pos((0, 300))], size=(rng, height))
def main(args, engine):
    with Session(engine) as session:
        if args.cycles > 0:
            for fil, ft_pc, mb_pc in session.query(Clip_Tracker.video_name, Clip_Tracker.full_screen_videos_processed, Clip_Tracker.mobiles_videos_processed).where(Clip_Tracker.mobiles_videos_processed == False).order_by(Clip_Tracker.view_count.desc()).all()[:args.cycles]:
                with VideoFileClip(os.path.join(clips_folder, fil)) as video:
                    width, height = video.size
                    x_center = width //2
                    rng = int(height*(9/16))
                    x1 = x_center - (rng//2)
                    x2 = x_center + (rng//2)
                    with ImageClip("/Users/abhirathchowdhury1/Library/Mobile Documents/com~apple~CloudDocs/Twitch Resources/Twitch Clips/Assets/Sm_Logo.png").set_duration(video.duration).set_pos('top').set_fps(30) as logo:
                        with HiddenPrints():
                            if not bool(mb_pc):
                                with createMobileVideo(logo, video.resize(.32), rng, height) as mobile:
                                    mobile.to_videofile(os.path.join(mobile_folder, fil),codec="mpeg4", temp_audiofile = f"twitch1_audio_tmp.m4a", remove_temp=True, audio_codec='aac', threads=2)
                                    session.execute(update(Clip_Tracker).where(Clip_Tracker.video_name == fil).values({"mobiles_videos_processed": True}))
                                    session.commit()
                            # if not bool(ft_pc):
                            #     with CompositeVideoClip([video, logo.set_position(('left', 'top'))]) as fullVideo:
                            #         fullVideo.to_videofile(os.path.join(fullscreen_folder, fil),codec="mpeg4", temp_audiofile = f"twitch2_audio_tmp.m4a", remove_temp=True, audio_codec='aac', threads=2 )
                            #         session.execute(update(Clip_Tracker).where(Clip_Tracker.video_name == fil).values({"full_screen_videos_processed": True}))
                            #         session.commit()
                        print("Finished", fil)
        else:
            for fil, ft_pc, mb_pc in session.query(Clip_Tracker.video_name, Clip_Tracker.full_screen_videos_processed, Clip_Tracker.mobiles_videos_processed).where(or_(Clip_Tracker.full_screen_videos_processed == False, Clip_Tracker.mobiles_videos_processed == False)).order_by(Clip_Tracker.view_count.desc()).all():
                with VideoFileClip(os.path.join(clips_folder, fil)) as video:
                    width, height = video.size
                    x_center = width //2
                    rng = int(height*(9/16))
                    x1 = x_center - (rng//2)
                    x2 = x_center + (rng//2)
                    with ImageClip("/Users/abhirathchowdhury1/Library/Mobile Documents/com~apple~CloudDocs/Twitch Resources/Twitch Clips/Assets/Sm_Logo.png").set_duration(video.duration).set_pos('top').set_fps(30) as logo:
                        with HiddenPrints():
                            if not bool(mb_pc):
                                with createMobileVideo(logo, video.resize(.32)) as mobile:
                                    mobile.to_videofile(os.path.join(mobile_folder, fil),codec="mpeg4", temp_audiofile = f"twitch1_audio_tmp.m4a", remove_temp=True, audio_codec='aac', threads=2)
                                    session.execute(update(Clip_Tracker).where(Clip_Tracker.video_name == fil).values({"mobiles_videos_processed": True}))
                                    session.commit()
                            if not bool(ft_pc):
                                with CompositeVideoClip([video, logo.set_position(('left', 'top'))]) as fullVideo:
                                    fullVideo.to_videofile(os.path.join(fullscreen_folder, fil),codec="mpeg4", temp_audiofile = f"twitch2_audio_tmp.m4a", remove_temp=True, audio_codec='aac', threads=2 )
                                    session.execute(update(Clip_Tracker).where(Clip_Tracker.video_name == fil).values({"full_screen_videos_processed": True}))
                                    session.commit()
                        print("Finished", fil)

if __name__ == '__main__':
    main(args, engine)