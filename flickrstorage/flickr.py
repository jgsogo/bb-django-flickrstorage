try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import httplib
from urlparse import urlparse

from django.conf import settings
from django.core.cache import cache
from django.core.files.base import File
from django.core.files.storage import Storage

from flickrhack import FlickrAPIhack


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
        #???
        if not self.token:
            raw_input('Press Enter...')
        self.flickr.get_token_part_two((self.token, frob))


#    def _open(self, name, mode='rb'):
#        flickr_file = FlickrStorageFile(name, self, mode)
#        return flickr_file

#   def _read(self, name):
#       url = self.url(name)
#       resp = urllib.urlopen(url)
#       return resp.read()

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
        return name

    def exists(self, name):
        return False

    def url(self, name):
        resp = self.flickr.photos_getSizes(photo_id=name)
        self._check_response(resp)
        for size in resp.findall('sizes/size'):
            if size.attrib['label'] == 'Large':  #original size
                return size.attrib['source']
        raise FlickrStorageException, "Can't get URL"


#class FlickrStorageFile(File):
#    def __init__(self, name, storage, mode):
#        self._name = name
#        self._storage = storage
#        self._mode = mode
#        self._is_dirty = False
#        self.file = StringIO()
#
#    @property
#    def size(self):
#        if not hasattr(self, '_size'):
#            self._size = self._storage.size(self._name)
#        return self._size
#
#    def read(self, num_bytes=None):
#        if not self.is_read:
#            self.file = StringIO(self._storage._read(self._name))
#            self.is_read = True
#        return self.file.read(num_bytes)
#
##    def write(self, content):
##        pass
#
#    def close(self):
##        if self._is_dirty:
##            self._storage._put_file(self._name, self.file.getvalue())
#        self.file.close()
