import httplib
from urlparse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import Storage

#from .flickrhack import FlickrAPIhack
from flickrapi import FlickrAPI as FlickrAPIhack
from flickrapi.exceptions import FlickrError


# Flickr API doc: https://www.flickr.com/services/api/flickr.photos.getSizes.htm
IMAGE_TYPES = {
    'square': 'Square',
    'large_square': 'Large Square',
    'thumbnail': 'Thumbnail',
    'small': 'Small',
    'small_320': 'Small 320',
    'medium': 'Medium',
    'medium_640': 'Medium 640',
    'medium_800': 'Medium 800',
    'large': 'Large',
    'original': 'Original',
}
IMAGE_TYPE_DEFAULT = 'Small'


class FlickrStorageException(Exception):
    pass


class FlickrStorage(Storage):
    _ready = False

    def __init__(self, photoset_id=None, options=None):
        self.photoset_id = photoset_id
        self.options = {
            'cache': True,
        }
        self.options.update(options or settings.FLICKR_STORAGE_OPTIONS)
        self.flickr = FlickrAPIhack(self.options['api_key'],
                                    self.options['api_secret'])
        #if self.options['cache']:
        #    self.flickr.cache = cache

	#self.flickr.token_cache.path = '.flickr'
        #TODO: move to management command
        self._get_tokens()

    def _get_tokens(self, perms=u'write'):
        try:
	    if not self.flickr.token_valid(perms=perms):
		self.flickr.get_request_token(oauth_callback='oob')
		authorize_url = self.flickr.auth_url(perms=perms)
		verifier = unicode(raw_input('Verifier code for %s:'% authorize_url))
		self.flickr.get_access_token(verifier)
	        self._ready = True
        except FlickrError:
            self._ready
        return self._ready

    def _check_response(self, resp):
        if resp.attrib['stat'] != 'ok':
            err = resp.find('err')
            raise FlickrStorageException, "Error %s: %s" % (err.attrib['code'], err.attrib['msg'])

    def delete(self, name):
        if not self._ready and not self._get_tokens():
            raise FlickrStorageException, "Flickr service is not ready"
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
        if not self._ready and not self._get_tokens():
            raise FlickrStorageException, "Flickr service is not ready"

        content.seek(0)             #ImageField read first 1024 bytes
        name = name.encode('utf-8')
        resp = self.flickr.upload(name, content.file)
        self._check_response(resp)
        name = resp.find('photoid').text
        content.close()
        # Add to default album
        photoset_id = self.options.get('photoset_id', None)
        if photoset_id:
            resp = self.flickr.photosets_addPhoto(photoset_id=photoset_id, photo_id=name)
            self._check_response(resp)
        # Add to album for this storage
        if self.photoset_id:
            resp = self.flickr.photosets_addPhoto(photoset_id=self.photoset_id, photo_id=name)
            self._check_response(resp)
        return name

    def exists(self, name):
        return False

    def url(self, name, img_type=None, fallback_to_biggest=True):
        if not self._ready and not self.flickr.token_valid(perms=u'read'):
            raise FlickrStorageException, "Flickr service is not ready"

        resp = self.flickr.photos_getSizes(photo_id=name)
        self._check_response(resp)
        label = IMAGE_TYPES.get(img_type, IMAGE_TYPE_DEFAULT)
        biggest = None
        for size in resp.findall('sizes/size'):
            if size.attrib['label'] != 'Original':
                biggest = size
            if size.attrib['label'] == label:
                return size.attrib['source']

        if biggest!=None and fallback_to_biggest:
            return biggest.attrib['source']

        raise FlickrStorageException, "Can't get URL"
