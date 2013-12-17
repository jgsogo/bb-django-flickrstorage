import httplib
from urlparse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import Storage

from .flickrhack import FlickrAPIhack


IMAGE_TYPES = {
    'square': 'Square',
    'thumbnail': 'Thumbnail',
    'small': 'Small',
    'medium': 'Medium',
    'large': 'Large'
}


class FlickrStorageException(Exception):
    pass


class FlickrStorage(Storage):

    def __init__(self, options=None):
        self.options = {
            'cache': True,
        }
        self.options.update(options or settings.FLICKR_STORAGE_OPTIONS)
        self.flickr = FlickrAPIhack(self.options['api_key'],
                                    self.options['api_secret'],
                                    cache=self.options['cache'])
        if self.options['cache']:
            self.flickr.cache = cache
        (self.token, frob) = self.flickr.get_token_part_one(perms='delete')
        #TODO: move to management command
        if not self.token:
            raw_input('Press Enter...')
        self.flickr.get_token_part_two((self.token, frob))

    def _check_response(self, resp):
        if resp.attrib['stat'] != 'ok':
            err = resp.find('err')
            raise FlickrStorageException, "Error %s: %s" % (err.attrib['code'], err.attrib['msg'])

    def delete(self, name):
        resp = self.flickr.photos_delete(photo_id=name)

    def size(self, name):
        url = self.url(name)
        u = urlparse(url)
        conn = httplib.HTTPConnection(u.hostname)
        conn.request('HEAD', u.path)
        resp = conn.getresponse()
        fsize = int(resp.getheader('content-length'))
        return fsize

    def _save(self, name, content):
        content.seek(0)             #ImageField read first 1024 bytes
        name = name.encode('utf-8')
        resp = self.flickr.upload(name, content.file)
        self._check_response(resp)
        name = resp.find('photoid').text
        content.close()
        # Add to album
        if self.options.get('photoset_id', None):
            resp = self.flickr.photosets_addPhoto(photoset_id=self.options.get('photoset_id'), photo_id=name)
            self._check_response(resp)
        return name

    def exists(self, name):
        return False

    def url(self, name, img_type=None):
        resp = self.flickr.photos_getSizes(photo_id=name)
        self._check_response(resp)
        label = IMAGE_TYPES.get(img_type, 'Large')
        for size in resp.findall('sizes/size'):
            if size.attrib['label'] == label:
                return size.attrib['source']
        raise FlickrStorageException, "Can't get URL"
