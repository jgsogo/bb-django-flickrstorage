from django.db.models.fields.files import ImageField, ImageFieldFile
from .flickr import FlickrStorage, IMAGE_TYPES

__all__ = ['FlickrField']

class ImageURL(object):
    def __init__(self, url):
        self.url = url

class FlickrFieldFile(ImageFieldFile):

    def __init__(self, *args, **kwargs):
        super(FlickrFieldFile, self).__init__(*args, **kwargs)
        self.storage = FlickrStorage()

    def __getattr__(self, name):
        if name in IMAGE_TYPES:
            img_url = self.storage.url(self.name, name)
            image = ImageURL(img_url)
            return image
        else:
            return super(FlickrFieldFile, self).__getattr__(name)



class FlickrField(ImageField):
    attr_class = FlickrFieldFile

    def __init__(self, *args, **kwargs):
        kwargs['upload_to'] = 'unused'
        super(FlickrField, self).__init__(*args, **kwargs)