import argparse
import http.client
import httplib2
import os
import random
import time
import datetime
from datetime import datetime, timedelta
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import Flow, InstalledAppFlow
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request
import os
from dotenv import load_dotenv
from sqlalchemy import *
import datetime
from Google import *
import re
from IPython.display import Image


from twitchAPI.twitch import Twitch
from copy import copy, deepcopy
from matplotlib.colors import *
import random

from dash import Dash, dcc, html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
from StreamMaster import *
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

load_dotenv()

mysql_engine = create_engine(f"mysql+mysqlconnector://{os.environ['USER_NAME']}:{os.environ['PASSWORD']}@{os.environ['PI']}/{os.environ['MAIN_DB']}" )


clips_folder = os.environ['CLIPS_FOLDER']
mobile_folder = os.environ['MOBILE_FOLDER']
fullscreen_folder = os.environ['FULLSCREEN_FOLDER']
ml_folder = os.environ['ML_FOLDER']
assets = os.environ['ASSETS']

SCOPES = ['https://www.googleapis.com/auth/yt-analytics.readonly']

API_SERVICE_NAME = 'youtubeAnalytics'
API_VERSION = 'v2'
CLIENT_SECRET_FILE = 'client_secrets_desktop.json'
CHANNEL = os.environ['CHANNEL']

# Code that initiates connection to the Google API - pulled from Google.py. Difference from using Google's built-in service is the following script creates convenience of storing pickle with necessary authentication
youtubeAnalytics = Create_Service(CLIENT_SECRET_FILE, API_SERVICE_NAME, API_VERSION, SCOPES)


twitch = Twitch(os.environ['TWITCH_APP_ID'], os.environ['TWITCH_APP_SECRET'])



color_sample = px.colors.sequential.YlOrBr + px.colors.sequential.ice
random.seed(333)
random.shuffle(color_sample)
game_colors = {}
games = {}
cnt = 0
with Session(mysql_engine) as session:
    for game_id, game_name in session.query(Game_Meta.game_id,func.max(Game_Meta.game_name)).select_from(join(Game_Meta,Clip_Tracker)).group_by(Game_Meta.game_id).all():
        games[game_id] = game_name 
        game_colors[game_name] = color_sample[cnt]
        cnt += 1

color_sample = px.colors.sequential.Viridis

with Session(mysql_engine) as session:
    creators = {creator[0]: color_sample[i] for i, creator in enumerate(session.query(distinct(Clip_Tracker.creator_name)).all())}

