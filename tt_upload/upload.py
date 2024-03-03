import os
import re
import warnings
import requests
import datetime as dt

from .regions import Region
from .component import TTComponent
from .models import User
from .models import Video, VideoList
from .models import Hashtag, HashtagList
from .exceptions import TTError, TTWarning, TTHashtagNotFound


class TTUpload:
    component = TTComponent
    search_hashtag = re.compile(r"#([^#]+)")
    dir_name_created = "tiktok"
    chunk_size = 1024*1024
    max_count = 30
    

    def __get_response(self, url: str, params: dict):
        resp = requests.get(url, params=params)

        if not resp.ok:
            raise TTError(f"HTTP error: {resp.status_code}")
        
        data = resp.json()

        if data['code'] != 0:
            msg = data['msg'].title()
            err_value = {
                k: v 
                for k, v in params.items()
                if k not in ["count", "cursor"]
            }
            raise TTError("%s: %s" % (msg, err_value))
    
        return data['data']

    def __get_data(self, url:str, params: dict):
        count = params.get("count", None)
        offset = params.get("cursor", None)

        if count is None:
            return self.__get_response(url, params)

        data = None
        cnt = 0
        params.update(count=self.max_count, cursor=offset)

        while cnt < count:
            resp = self.__get_response(url, params)
            
            if data is None:
                data = resp

                if isinstance(data, dict):
                    first_key = list(data.keys())[0]

            else:
                if isinstance(data, list):
                    data.extend(resp)
                    cnt = len(data)
                    offset += len(data)
                    
                else:
                    data[first_key].extend(resp[first_key])
                    
                    if not resp['hasMore']:
                        break
                    
                    cnt += len(data[first_key])
                    offset = resp['cursor']

            params.update(cursos=offset)

        if isinstance(data, list):
            return data[:count]

        data[first_key] = data[first_key][:count]
        return data
    
    def __extract_videos(
        self, 
        data: dict | list, 
        author_info: bool = False, 
        hasgtag_info: bool = False
    ):
        videos = []
        
        for video in data:
            hashtag = hashtag=self.__extract_hashtags(video['title'], hasgtag_info)
            author = User(nickname=video['author']['unique_id'])
            
            if author_info:
                author = self.get_user_details(video['author']['unique_id'])
            
            videos.append(
                Video(
                    title=video['title'].strip(),
                    video_url=video['play'],
                    audio_url=video['music'],
                    date=dt.date.fromtimestamp(video['create_time']),
                    views=video['play_count'],
                    duration=video['duration'],
                    author=author,
                    hashtag=hashtag
                )
            )

        return VideoList(videos)

    def __extract_hashtags(self, text: str, hashtag_info: bool):
        hashtag_list = []
        hashtag = self.search_hashtag.findall(text)
        hashtag = map(lambda item: item.strip(), hashtag)
        hashtag = list(filter(lambda item: item, hashtag))
        
        if not hashtag:
            return HashtagList([])

        hashtag[-1] = hashtag[-1].split(" ")[-1]
        
        if not hashtag_info:
            return HashtagList([
                Hashtag(title=item)
                for item in hashtag
            ])

        for item in hashtag:            
            try:
                hashtag_list.append(self.get_hashtag_details(item))
            except:
                warnings.warn(item, TTHashtagNotFound)
                continue 

        return HashtagList(hashtag_list)

    def __create_dir(self, nickname: str, title: str | None, date: dt.date):
        path = os.path.join(self.dir_name_created, nickname)
        
        if not os.path.exists(path):
            os.makedirs(path)

        if title is None:
            path = os.path.join(path, "%s.mp4" % date.strftime("%Y-%m-%d"))
        else:
            path = os.path.join(path, "%s  %s.mp4" % (
                title, date.strftime("%Y-%m-%d")
            ))
            
        if os.path.exists(path):
            msg = "File %s alredy exists and be overwritten" % path
            warnings.warn(msg, TTWarning)

        return path

    def get_user_details(self, user: str):
        data = self.__get_data(
            "/".join([
                self.component.host,
                self.component.user_info
            ]),
            params={
                "unique_id": user,
            }
        )
        return User(
            tiktok_id=data['user']['id'],
            nickname=data['user']['uniqueId'],
            signature=data['user']['signature'],
            twitter_id = data['user']['twitter_id'],
            youtube_channel_id = data['user']['youtube_channel_id'],
            subscribers=data['stats']['followerCount'],
            video_count=data['stats']['videoCount'],
            likes=data['stats']['heart']
        )
    
    def get_trending_video(
        self, 
        region: Region,
        author_info: bool = False,
        hashtag_info: bool = False,
        count: int = 1, 
        offset: int = 0
    ):
        data = self.__get_data(
            "/".join([
                self.component.host,
                self.component.trending_video
            ]),
            params={
                "region": region.value,
                "count": count,
                "cursor": offset
            }
        )
        return self.__extract_videos(data, author_info, hashtag_info)
    
    def get_video_by_user(
        self, 
        user: str,
        author_info: bool = False,
        hashtag_info: bool = False, 
        count: int = 1, 
        offset: int = 0
    ):
        data = self.__get_data(
            "/".join([
                self.component.host,
                self.component.video_by_user
            ]),
            params={
                "unique_id": user,
                "count": count,
                "cursor": offset
            }
        )
        return self.__extract_videos(data['videos'], author_info, hashtag_info)

    def get_video_by_keywords(
        self, 
        keywords: list[str], 
        author_info: bool = False,
        hashtag_info: bool = False,
        count: int = 1,
        offset: int = 0
    ):
        data = self.__get_data(
             "/".join([
                self.component.host,
                self.component.video_by_keywords
            ]),
            params={
                "keywords": keywords,
                "count": count,
                "cursor": offset
            }
        )
        return self.__extract_videos(data['videos'], author_info, hashtag_info)

    def get_video_by_hashtag_id(
        self, 
        hashtag_id: int, 
        author_info: bool = False,
        hashtag_info: bool = False,
        count: int = 1, 
        offset: int = 0
    ):
        data = self.__get_data(
             "/".join([
                self.component.host,
                self.component.video_by_hashtag
            ]),
            params={
                "challenge_id": hashtag_id,
                "count": count,
                "cursor": offset
            }
        )
        return self.__extract_videos(data['videos'], author_info, hashtag_info)

    def get_hashtag_details(self, hashtag: str):
        data = self.__get_data(
            "/".join([
                self.component.host,
                self.component.hashtag_info
            ]),
            params={
                "challenge_name": hashtag
            }
        )
        return Hashtag(
            id=data["id"], 
            title=data["cha_name"], 
            views=data["view_count"]
        )
         
    def get_hashtag_by_keywords(
        self, 
        keywords: list[str],
        hashtag_info: bool = False,
        count: int = 1, 
        offset: int = 0
    ):
        data = self.__get_data(
            "/".join([
                self.component.host,
                self.component.hashtag_by_keywords
            ]),
            params={
                "keywords": keywords,
                "count": count,
                "cursor": offset
            }
        )

        if not hashtag_info:
            return HashtagList([
                Hashtag(
                    title = hashtag["cha_name"]
                ) 
                for hashtag in data['challenge_list']
            ])

        return HashtagList([
            Hashtag(
                id = hashtag["id"], 
                title = hashtag["cha_name"], 
                views = hashtag["view_count"]
            ) 
            for hashtag in data['challenge_list']
        ])

    def get_hashtag_by_trending_video(
        self, 
        region: Region, 
        hashtag_info: bool = False,
        count: int = 1, 
        offset: int = 0
    ):
        data = self.__get_data(
            "/".join([
                self.component.host,
                self.component.trending_video
            ]),
            params={
                "region": region.value,
                "count": count,
                "cursor": offset
            }
        )
        
        hashtag_list = []
        
        for video in data:
            hashtag = self.__extract_hashtags(video['title'], hashtag_info)
            hashtag_list.extend(hashtag.root)

        return HashtagList(root=hashtag)

    def download_video(self, video: Video, path: str | None = None):
        if path is not None and os.path.exists(path):
            raise TTError("Path alredy exists: %s" % path)
        else:
            path = self.__create_dir(
                video.author.nickname,
                video.title,
                video.date
            )

        raw = requests.get(video.video_url, stream=True)
        
        with open(path, "wb") as f:
            for chunk in raw.iter_content(chunk_size=self.chunk_size):
                if chunk:
                    f.write(chunk)
