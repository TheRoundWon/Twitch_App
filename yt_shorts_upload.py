"""
The following script is designed to access the Youtube Data API and confirm which Youtube videos
have already been uploaded and whether all the videos are accounted for and correctly mapped to the right playlists

"""


#Import necessary documents
import argparse
import http.client
# import httplib2
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
from _utils import *

load_dotenv()

parser = argparse.ArgumentParser()

parser.add_argument("-v","--videos", type=int, nargs = "?", const=1, default=1, help="number of videos to upload")

args = parser.parse_args()





mobile_folder = os.environ['MOBILE_FOLDER']
highlights_folder = os.environ['PROCESSED_HIGHLIGHTS']
ml_folder = os.environ['ML_FOLDER']
assets = os.environ['ASSETS']

CLIENT_SECRET_FILE = 'client_secrets.json'
API_NAME = 'youtube'
API_VERSION = 'v3'
# recommend pulling as much access as possible since the Create_Service function will create a pickle token of your authentication allow single authentication for extended period.
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", 'https://www.googleapis.com/auth/youtube']

# Code that initiates connection to the Google API - pulled from Google.py. Difference from using Google's built-in service is the following script creates convenience of storing pickle with necessary authentication
service = Create_Service(CLIENT_SECRET_FILE, API_NAME, API_VERSION, SCOPES)


def upload_yt_shorts(session_engine, service, args):
    with Session(session_engine)as session:
        for clip_id, game_title, clip_creator, console, clip_title, video_name, clip_url in session.query(TwitchVideos.id, Game_Meta.game_name, TwitchVideos.creator_name, Game_Meta.platform, TwitchVideos.title, TwitchVideos.video_name, TwitchVideos.url).select_from(join(Game_Meta,TwitchVideos)).where(and_(or_(TwitchVideos.published == None, TwitchVideos == PublishingStatus.d), TwitchVideos.mobiles_videos_processed == True, TwitchVideos.video_type == TwitchVideoStyle.CLIP)).order_by(TwitchVideos.view_count.desc()).all()[:args.videos]:
            # print(game_title, clip_creator, console, clip_title, video_name)
            try:
                # First upload the full screen
                request_body = {
                    'snippet': {
                        'categoryId': 20,
                        'title': " | ".join([console, game_title+" Gameplay", clip_title]),
                        'description': createDescription(game_title, os.environ['YT_CHANNEL_ID'], clip_creator, console, os.environ['CHANNEL'], clip_url),
                        'tags': ["Video Games", game_title, console, "Gaming"]
                        },
                        'status': {
                            'privacyStatus': 'public',
                            'selfDeclaredMadeForKids': False, 
                            'madeForKids': False,
                        },
                        'notifySubscribers': True
                    }
                # mediaFile = MediaFileUpload(os.path.join(fullscreen_folder, video_name))
                # normal_response_upload = service.videos().insert(
                #     part='snippet,status',
                #     body=request_body,
                #     media_body=mediaFile
                # ).execute()
                # # pause after upload
                # print("Normal Upload complete", clip_title)
                # time.sleep(5)
                # playlistId = session.query(PlayList_yt.id).where(PlayList_yt.title.ilike(f'%{game_title}%')).first()[0]
                # service.playlistItems().insert(part = "snippet", body = {"snippet": {'playlistId': playlistId, 'resourceId': {'videoId': normal_response_upload.get('id'), 'kind': "youtube#video"}}}).execute()

                #upload the short
                request_body['description'] = createDescription(game_title, os.environ['YT_CHANNEL_ID'], clip_creator, console, os.environ['CHANNEL'], clip_url, mode='shorts')
                mediaFile = MediaFileUpload(os.path.join(mobile_folder, video_name))
                mobile_response_upload = service.videos().insert(
                    part='snippet,status',
                    body=request_body,
                    media_body=mediaFile
                ).execute()
                time.sleep(5)
                playlistId = session.query(PlayList_yt.id).where(PlayList_yt.title.ilike(f'%short%')).first()[0]
                service.playlistItems().insert(part = 'snippet', body = {"snippet": {'playlistId': playlistId, 'resourceId': {'videoId': mobile_response_upload.get('id'), 'kind': "youtube#video"}}}).execute()
                session.execute(update(TwitchVideos).where(TwitchVideos.id == clip_id).values({'published' : PublishingStatus.m}))
                session.commit()
                print("Short Upload complete", clip_title)

            except Exception as e:
                print("Upload failed", clip_title, e)



if __name__ == "__main__":
    upload_yt_shorts(mysql_engine, service, args)