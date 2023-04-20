""" The Following script contains the SQL Alchemy ORMs intended for creating tables in designaed MYSQL Database
"""

from operator import truediv
from sqlalchemy import *
from sqlalchemy.orm import declarative_base, relationship, Session, aliased
from sqlalchemy import engine
from datetime import datetime, timedelta, date
import enum
import sys
import os

from dotenv import load_dotenv
load_dotenv()


# Initiate connection to SQL Database
Base = declarative_base()
mysql_engine = create_engine(f"mysql+mysqlconnector://{os.environ['USER_NAME']}:{os.environ['PASSWORD']}@{os.environ['PI']}/{os.environ['MAIN_DB']}" )



# Context method to help with heavy printing if there is too much console printing down the line
class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout


class PublishingStatus(enum.Enum):
    """Enumeration Type for Publishing status

    m = youtube
    d = instagram
    f = full

    """
    m = 1 
    d = 2 
    f = 3 

class Clip_Merits(Base):
    __tablename__ = 'clip_merits_tracker'
    id = Column(String(255), ForeignKey('twitch_video_tracker.id'), primary_key=True)
    clips_previous_reward = Column(Integer)
    yt_previous_reward = Column(Integer)

class Clip_Tracker(Base):
    """
    ORM to  track status of clips which have been downloaded and processed for youtube
    """
    __tablename__ = "clip_tracker"
    id = Column(String(255), primary_key=True)    
    url = Column(String(255))    
    embed_url = Column(String(255))     
    broadcaster_id = Column(Integer, ForeignKey('broadcaster.user_id'))    
    creator_id  = Column(Integer)   
    creator_name = Column(String(100))    
    video_id = Column(Integer, nullable=True)    
    game_id  = Column(Integer, ForeignKey('game_meta.game_id'))
    language  = Column(String(6))   
    title  = Column(String(255))   
    view_count = Column(BigInteger)
    video_name = Column(String(255), nullable=True)
    yt_filename = Column(String(255), nullable=True) # video_id which will link to youtube table
    created_at = Column(DATETIME)
    thumbnail_url = Column(String(255))    
    duration = Column(FLOAT)
    published = Column(Enum(PublishingStatus))
    downloaded = Column(BOOLEAN)
    full_screen_videos_processed = Column(BOOLEAN) # Deprecated
    mobiles_videos_processed = Column(Boolean)

class ClipStyle(enum.Enum):
    funny = 0
    info = 1
    action = 2
    skill = 3

class TwitchVideoStyle(enum.Enum):
    ARCHIVE = 0
    CLIP = 1
    HIGHLIGHT = 2


class TwitchVideos(Base):
    """
    ORM to  track status of videos which are pubished on Twitch which have been downloaded and processed for youtube
    """
    __tablename__ = "twitch_video_tracker"
    id = Column(String(255), primary_key=True) #twitch id
    url = Column(String(255)) # find the video
    embed_url = Column(String(255))     
    broadcaster_id = Column(Integer, ForeignKey('broadcaster.user_id'))    
    creator_id  = Column(Integer) # ID of the creator who made the video
    creator_name = Column(String(100))    
    video_id = Column(Integer, nullable=True) # Source Video (if exists)
    game_id  = Column(Integer, ForeignKey('game_meta.game_id'))
    language  = Column(String(6))   
    title  = Column(String(255))   
    view_count = Column(BigInteger)
    video_name = Column(String(255), nullable=True) # Video File Name
    video_type = Column(Enum(TwitchVideoStyle))
    yt_filename = Column(String(255), nullable=True) # video_title which will link to youtube table
    audio_filename = Column(String(255), nullable=True)
    created_at = Column(DATETIME)
    thumbnail_url = Column(String(255))    
    duration = Column(FLOAT) # Number of seconds of video
    published = Column(Enum(PublishingStatus))
    downloaded = Column(BOOLEAN)
    audio_processed = Column(BOOLEAN) 
    category = Column(Enum(ClipStyle), nullable=True)
    mobiles_videos_processed = Column(Boolean)



class Clip_Speech(Base):
    __tablename__ = "clip_audio"
    idx = Column(BigInteger, primary_key=True)
    video_id = Column(String(255), ForeignKey('twitch_video_tracker.id'))
    speech = Column(String(255))
    time_block = Column(String(5))


        
# Table to handle Asssociation table between tags and streams



class Broadcaster(Base):
    """ORM to capture the Metadata on twitch broadcasters. This table will likely be migrated to a different table if we need to accommodate other platforms in the future.
    """
    __tablename__ = 'broadcaster'
    user_id = Column(Integer, primary_key=True)
    user_login = Column(String(30))
    user_name = Column(String(30))



class Game_Meta(Base):
    """ Table to capture twitch game_ids along with platform designation, download status, status along other attributes
    """
    __tablename__ = 'game_meta'
    game_id = Column(Integer, primary_key=True)
    game_name = Column(String(100))
    platform = Column(String(20))
    downloaded = Column(Boolean)
    main_story= Column(Boolean)
    multiplayer = Column(Boolean)
    Purchased = Column(Boolean)


# Saved for reference
schema_mapper = {
    Integer: int,
    FLOAT: float,
    DATETIME: datetime,
    BigInteger: int


}



class VideoStyle(enum.Enum):
    m = 1 # mobile
    f = 2 # fullscreen video






class PlayList_yt(Base):
    __tablename__ = "yt_playlists"
    id = Column(String(255), primary_key=True) # yt playlist id
    title = Column(String(255))
    tb_default = Column(Integer, ForeignKey("thumbnail_mapper.id"))
    tb_medium = Column(Integer, ForeignKey("thumbnail_mapper.id"))
    tb_high = Column(Integer, ForeignKey("thumbnail_mapper.id"))
    tb_standard = Column(Integer, ForeignKey("thumbnail_mapper.id"))



class YT_Video(Base):
    __tablename__ = "yt_video_mapper"
    id = Column(String(255), primary_key=True) # yt video id
    clip_id = Column(String(255), ForeignKey("twitch_video_tracker.id"), nullable=True)
    title = Column(String(255))
    filename = Column(String(255))
    style = Column(Enum(VideoStyle))
    description = Column(String(5000))
    tb_default = Column(Integer, ForeignKey("thumbnail_mapper.id"))
    tb_medium = Column(Integer, ForeignKey("thumbnail_mapper.id"))
    tb_high = Column(Integer, ForeignKey("thumbnail_mapper.id"))
    tb_standard = Column(Integer, ForeignKey("thumbnail_mapper.id"))
    tags = Column(String(255))

yt_vid_pl_mapper = Table(
    "yt_video_playlist_mapper",
    Base.metadata,
    Column('yt_playlist_id', ForeignKey('yt_playlists.id')),
    Column('yt_video_id', ForeignKey('yt_video_mapper.id') )
)


class Thumbnails(Base):
    __tablename__= "thumbnail_mapper"
    id = Column(Integer, primary_key=True)
    asset = Column(String(255))
    width = Column(Integer)
    height = Column(Integer)

if __name__ == "__main__":
    # Create all tables if TwitchMaster is run as standalone script
    Base.metadata.create_all(mysql_engine)