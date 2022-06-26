"""
The following script is designed to access the Youtube Data API and confirm which Youtube videos
have already been uploaded and whether all the videos are accounted for and correctly mapped to the right playlists

"""


#Import necessary documents
import argparse
import http.client
import httplib2
import os
import random
import time
import datetime
from datetime import datetime, timedelta
from Google import *
import os
from dotenv import load_dotenv
from sqlalchemy import *
import datetime
import re
from StreamMaster import *


load_dotenv()

parser = argparse.ArgumentParser()

parser.add_argument("videos", type=int, nargs = "?", const=1, default=1, help="number of videos to upload")

args = parser.parse_args()


engine = create_engine(f"mysql+mysqlconnector://{os.environ['USER_NAME']}:{os.environ['PASSWORD']}@{os.environ['PI']}/{os.environ['MAIN_DB']}" )


clips_folder = os.environ['CLIPS_FOLDER']
mobile_folder = os.environ['MOBILE_FOLDER']
fullscreen_folder = os.environ['FULLSCREEN_FOLDER']
ml_folder = os.environ['ML_FOLDER']
assets = os.environ['ASSETS']

CLIENT_SECRET_FILE = 'client_secrets.json'
API_NAME = 'youtube'
API_VERSION = 'v3'
# recommend pulling as much access as possible since the Create_Service function will create a pickle token of your authentication allow single authentication for extended period.
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", 'https://www.googleapis.com/auth/youtube']

# Code that initiates connection to the Google API - pulled from Google.py. Difference from using Google's built-in service is the following script creates convenience of storing pickle with necessary authentication
service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)



def main(engine, service, args):
    with Session(engine)as session:
        for clip_id, game_title, clip_creator, console, clip_title, video_name, clip_url, publishing_status in session.query(Clip_Tracker.id, Game_Meta.game_name, Clip_Tracker.creator_name, Game_Meta.platform, Clip_Tracker.title, Clip_Tracker.video_name, Clip_Tracker.url, Clip_Tracker.published).select_from(join(Game_Meta,Clip_Tracker)).where(and_(Clip_Tracker.published != None,  Clip_Tracker.mobiles_videos_processed == True, Clip_Tracker.published != PublishingStatus.f)).order_by(Clip_Tracker.view_count.desc()).all()[:args.videos]:
            # print(game_title, clip_creator, console, clip_title, video_name)
            request_body = {
                'snippet': {
                    'categoryI': 20,
                    'title': " | ".join([console, game_title+" Gameplay", clip_title]),
                    'tags': ["Video Games", game_title, console, "Gaming"]
                    },
                    'status': {
                        'privacyStatus': 'public',
                        'selfDeclaredMadeForKids': False, 
                        'madeForKids': False,
                    },
                    'notifySubscribers': True
                }
            try:
                # First upload the full screen
                if publishing_status == PublishingStatus.d:
                    request_body['description'] = createDescription(game_title, os.environ['YT_CHANNEL_ID'], clip_creator, console, os.environ['CHANNEL'], clip_url, mode='shorts')
                    mediaFile = MediaFileUpload(os.path.join(mobile_folder, video_name))
                    playlistId = session.query(PlayList_yt.id).where(PlayList_yt.title.ilike(f'%short%')).first()[0]
                else:
                    request_body['description'] = createDescription(game_title, os.environ['YT_CHANNEL_ID'], clip_creator, console, os.environ['CHANNEL'], clip_url)
                    mediaFile = MediaFileUpload(os.path.join(clips_folder, video_name))
                    playlistId = session.query(PlayList_yt.id).where(PlayList_yt.title.ilike(f'%{game_title}%')).first()[0]
                reponse_upload = service.videos().insert(
                    part='snippet,status',
                    body=request_body,
                    media_body=mediaFile
                ).execute()
            except Exception as e:
                print("Upload failed", clip_title, e)