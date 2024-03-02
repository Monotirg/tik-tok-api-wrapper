import re
from tt_upload.upload_sync import TTUpload
from tt_upload.regions import Region


tt_upload = TTUpload()
d = tt_upload.get_trending_video(Region.UNITED_STATES, count=10, author_info=False, hashtag_info=True)
print(len(d))
# print(tt_upload.get_hashtag_by_keywords(keywords=["cats"], count=5, hashtag_info=True))
# print(tt_upload.get_video_by_hashtag_id(5216))
# print(tt_upload.get_hashtag_by_trending_video(Region.RUSSIA, hashtag_info=True))
# print(tt_upload.get_video_by_keywords(["cats"]))
# print(tt_upload.get_user_details("pet_babylover2284"))
# print(tt_upload.get_video_by_user("kotogallery", author_info=True, hashtag_info=True))
# print(tt_upload.get_hashtag_details("cats"))
