""" The Following script contains the SQL Alchemy ORMs intended for creating tables in designaed MYSQL Database
"""

from operator import truediv
from sqlalchemy import *
from sqlalchemy.orm import declarative_base, relationship, Session, aliased
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

    m = mobile
    d = desktop
    f = full

    """
    m = 1 # Mobile only
    d = 2 # Desktop only
    f = 3 # Full complete

class Clip_Merits(Base):
    __tablename__ = 'clip_merits_tracker'
    id = Column(String(255), ForeignKey('clip_tracker.id'), primary_key=True)
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

class Clips(Base):
    """
    ORM to  track status of clips which have been downloaded and processed for youtube
    """
    __tablename__ = "clips_tracker"
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
    audio_filename = Column(String(255), nullable=True)
    created_at = Column(DATETIME)
    thumbnail_url = Column(String(255))    
    duration = Column(FLOAT)
    published = Column(Enum(PublishingStatus))
    downloaded = Column(BOOLEAN)
    audio_processed = Column(BOOLEAN) # Deprecated
    clip_style = Column(Enum(ClipStyle), nullable=True)
    mobiles_videos_processed = Column(Boolean)


class Clip_Speech(Base):
    __tablename__ = "clip_audio"
    idx = Column(BigInteger, primary_key=True)
    clip_id = Column(String(255), ForeignKey('clip_tracker.id'))
    speech = Column(String(255))
    time_block = Column(String(5))


        
# Table to handle Asssociation table between tags and streams
tag_stream_association = Table(
    "tag_stream_association",
    Base.metadata,
    Column('tag_mapper_id', ForeignKey('tag_mapper.id')),
    Column('stream_id', ForeignKey('stream_capture.id') )

)

class Tag_Mapper(Base):
    """ORM to track different tags and their meanings
    """
    __tablename__ = "tag_mapper"
    id = Column(Integer, primary_key=True)
    tag_id = Column(String(255))
    localization_name = Column(String(255))
    streams = relationship("Stream_Capture", secondary = tag_stream_association, back_populates='tags')
    


class Stream_Capture(Base):
    """Similar to Apache Kafka Topic - likely deprecated for a Topic on Apache Kafka Cluster

    # Currently under testing, not advised to be used

    """
    __tablename__ = "stream_capture"
    id = Column(Integer, primary_key = True)
    stream_id = Column(Integer)
    user_id = Column(Integer, ForeignKey('broadcaster.user_id'))
    game_id = Column(Integer, ForeignKey('game_meta.game_id'))
    stream_title = Column(String(180))
    viewer_count = Column(Integer)
    started_at = Column(DATETIME)
    language = Column(String(5))
    thumbnail_url = Column(String(255))
    is_mature = Column(Boolean)
    capture_time = Column(DATETIME)
    tags =  relationship("Tag_Mapper", secondary = tag_stream_association, back_populates="streams")



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

class PlayList(Base):
    __tablename__ = "yt_playlist_mapper"
    id = Column(String(255), primary_key=True) # yt playlist id
    title = Column(String(255))
    tb_default = Column(Integer, ForeignKey("thumbnail_mapper.id"))
    tb_medium = Column(Integer, ForeignKey("thumbnail_mapper.id"))
    tb_high = Column(Integer, ForeignKey("thumbnail_mapper.id"))
    tb_standard = Column(Integer, ForeignKey("thumbnail_mapper.id"))

class PlayList_yt(Base):
    __tablename__ = "yt_playlists"
    id = Column(String(255), primary_key=True) # yt playlist id
    title = Column(String(255))
    tb_default = Column(Integer, ForeignKey("thumbnail_mapper.id"))
    tb_medium = Column(Integer, ForeignKey("thumbnail_mapper.id"))
    tb_high = Column(Integer, ForeignKey("thumbnail_mapper.id"))
    tb_standard = Column(Integer, ForeignKey("thumbnail_mapper.id"))




class Video_yt(Base):
    __tablename__ = "yt_videos"
    id = Column(String(255), primary_key=True) # yt video id
    clip_id = Column(String(255), ForeignKey("clip_tracker.id"), nullable=True)
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
    Column('yt_video_id', ForeignKey('yt_videos.id') )
)



class YT_Video(Base):
    __tablename__ = "yt_video_mapper"
    id = Column(String(255), primary_key=True) # yt video id
    clip_id = Column(String(255), ForeignKey("clip_tracker.id"), nullable=True)
    title = Column(String(255))
    filename = Column(String(255))
    style = Column(Enum(VideoStyle))
    description = Column(String(5000))
    playlist_id = Column(String(255), ForeignKey("yt_playlist_mapper.id"))
    tb_default = Column(Integer, ForeignKey("thumbnail_mapper.id"))
    tb_medium = Column(Integer, ForeignKey("thumbnail_mapper.id"))
    tb_high = Column(Integer, ForeignKey("thumbnail_mapper.id"))
    tb_standard = Column(Integer, ForeignKey("thumbnail_mapper.id"))
    tags = Column(String(255))

class Thumbnails(Base):
    __tablename__= "thumbnail_mapper"
    id = Column(Integer, primary_key=True)
    asset = Column(String(255))
    width = Column(Integer)
    height = Column(Integer)

if __name__ == "__main___":
    # Create all tables if TwitchMaster is run as standalone script
    Base.metadata.create_all(mysql_engine)