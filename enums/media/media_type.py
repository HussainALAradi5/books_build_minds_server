from enum import Enum

class MediaType(str, Enum):
    BOOK_COVER = "book_cover"
    BOOK_GALLERY = "book_gallery"
    PROFILE_PICTURE = "profile_picture"
