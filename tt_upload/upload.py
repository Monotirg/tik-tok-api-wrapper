import requests
import pprint

from .regions import Region
from .exceptions import TTError
from .component import TT_Component


class TT_Upload:
    component = TT_Component

    @classmethod
    def get_trending_video(cls, region: Region, count: int = 1, offset: int = 0):
        resp = requests.get(
            "/".join([
                cls.component.host,
                cls.component.trending_video
            ]),
            params={
                "region": region.value,
                "count": count,
                "cursor": offset
            }
        )
        
        if not resp.ok:
            raise TTError(f"Http error: {resp.status_code}")
        
        data = resp.json()

        if data['code'] != 0:
            msg = f"{data['msg']}: {region.value}"
            raise Exception(msg)

        return [
            {
                "title": video['title'].strip(),
                "video_url": video['play'],
                "audio_url": video['music'],
                "views": video['play_count'],
                "duration": video['duration'],
                "author": "@" + video["author"]['unique_id']
            }
            for video in data['data']
        ]
    

