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

parser.add_argument("-t","--title", type=str,  help="Input which title you want to upload")
parser.add_argument("-o","--options", type=bool, nargs="?", help="List out available titles")

args = parser.parse_args()

import socket
socket.setdefaulttimeout(60000)



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

strtString = func.substring_index(TwitchVideos.title, "|", 1)
endString = func.substring_index(TwitchVideos.title, "|", -1)
input_highlights = os.environ['IN_PROCESS_HIGHLIGHTS']
output_highlights = os.environ['PROCESSED_HIGHLIGHTS']
midString = func.trim(func.substring(
    TwitchVideos.title,
    func.length(strtString)+2,
    func.length(TwitchVideos.title) - func.length(strtString) - func.length(endString)-2
))

highlightMode = func.substring_index(midString, ' ', 1)
highlightModeIx = func.substring_index(midString, ' ', -1)

def yt_available_highlights(session_engine) -> list:
    with Session(session_engine) as session:
        return [ix[0]for ix in session.query(func.distinct(endString)).where(and_(TwitchVideos.video_type == TwitchVideoStyle.HIGHLIGHT, or_(TwitchVideos.published == None, TwitchVideos.published != PublishingStatus.d))).all()]

def upload_yt_highlights(session_engine, service, title):
    with Session(session_engine)as session:
        check_returns = session.query(TwitchVideos.id, Game_Meta.game_name, TwitchVideos.creator_name, Game_Meta.platform, TwitchVideos.title, endString, TwitchVideos.url).select_from(join(Game_Meta,TwitchVideos)).where(and_(or_(TwitchVideos.published == None, TwitchVideos == PublishingStatus.d),  TwitchVideos.video_type == TwitchVideoStyle.HIGHLIGHT, endString.ilike(f"%{title}"))).order_by(TwitchVideos.view_count.desc()).all()
        if bool(check_returns):

            clip_id, game_title, clip_creator, console, clip_title, video_name, clip_url = check_returns[0]
            # print(game_title, clip_creator, console, clip_title, video_name)

            # First upload the full screen
            request_body = {
                'snippet': {
                    'categoryId': 20,
                    'title': " | ".join([console, game_title+" Highlights", title]),
                    'description': createDescription(game_title, os.environ['YT_CHANNEL_ID'], clip_creator, console, os.environ['CHANNEL'], clip_url, mode=generate_timestamps(session_engine, video_name)),
                    'tags': ["Video Games", game_title, console, "Gaming"]
                    },
                    'status': {
                        'privacyStatus': 'public',
                        'selfDeclaredMadeForKids': False, 
                        'madeForKids': False,
                    },
                    'notifySubscribers': True
                }
            mediaFile = MediaFileUpload(os.path.join(highlights_folder, f"{video_name}.mp4"))
            normal_response_upload = service.videos().insert(
                part='snippet,status',
                body=request_body,
                media_body=mediaFile
            ).execute()
            # pause after upload
            print("Highlight Upload complete", title, normal_response_upload.get('id'))
            time.sleep(5)
            playlistId = session.query(PlayList_yt.id).where(PlayList_yt.title.ilike(f'%{game_title}%')).first()[0]
            service.playlistItems().insert(part = "snippet", body = {"snippet": {'playlistId': playlistId, 'resourceId': {'videoId': normal_response_upload.get('id'), 'kind': "youtube#video"}}}).execute()
            for clip_id, game_title, clip_creator, console, clip_title, video_name, clip_url in check_returns:
                session.execute(update(TwitchVideos).where(TwitchVideos.id == clip_id).values({'published' : PublishingStatus.d}))
                session.commit()
            print('playlist mapping complete')
        else:
            print("Invalid Title entry")
            print("Available highlights", yt_available_highlights(session_engine))

if __name__ == "__main__":
    if args.options == True:
        print(yt_available_highlights(mysql_engine))
    else:
        upload_yt_highlights(mysql_engine, service, args.title)