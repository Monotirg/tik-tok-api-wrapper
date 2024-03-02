import datetime as dt

from pydantic import BaseModel, RootModel
from pydantic import field_validator
from typing import Optional

class ModelStrMixin:
    def __str__(self) -> str:
        s = super().__str__().replace("root=", "")
        cls_name = self.__class__.__name__
        return f"{cls_name}({s})"

class ModelIterMixin:
    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, index):
        return self.root[index]
    
    def __len__(self):
        return len(self.root)

class User(ModelStrMixin, BaseModel):
    tiktok_id: Optional[int] = None
    nickname: str
    signature: Optional[str] = None
    twitter_id: Optional[str] = None
    youtube_channel_id: Optional[str] = None
    subscribers: Optional[int] = None
    video_count: Optional[int] = None
    likes: Optional[int] = None

    @field_validator("signature", "twitter_id", "youtube_channel_id")
    def has_empty(cls, val: str | int) -> None | str | int:
        if val:
            return val
        
        return None

class Hashtag(ModelStrMixin, BaseModel):
    id: Optional[int] = None
    title: str 
    views: Optional[int] = None 

class HashtagList(ModelStrMixin, ModelIterMixin, RootModel):
    root: list[Hashtag]

class Video(ModelStrMixin, BaseModel):
    title: str
    video_url: str
    audio_url: str
    date: dt.date
    views: int
    duration: float
    author: User
    hashtag: HashtagList

    @field_validator("title", "audio_url")
    def has_empty(cls, val: str):
        if val:
            return val
        
        return None

class VideoList(ModelStrMixin, ModelIterMixin, RootModel):
    root: list[Video]
