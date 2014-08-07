from flickrapi import FlickrAPI
from flickrapi.multipart import Part, Multipart
from flickrapi import make_utf8

class FlickrAPIhack(FlickrAPI):

    def __init__(self, api_key, secret=None, username=None,
            token=None, format='etree', store_token=True, cache=False):
        FlickrAPI.__init__(self, api_key, secret, username, token, format,\
                           store_token, cache)

    def _FlickrAPI__upload_to_form(self, form_url, filename, fileobj, callback, **kwargs):
        '''
        Can upload a file using file object
        '''

        if not filename:
            raise IllegalArgumentException("filename must be specified")
        if not self.token_cache.token:
            raise IllegalArgumentException("Authentication is required")

        format = self._FlickrAPI__extract_upload_response_format(kwargs)

        # Update the arguments with the ones the user won't have to supply
        arguments = {'auth_token': self.token_cache.token,
                     'api_key': self.api_key}
        arguments.update(kwargs)

        # Convert to UTF-8 if an argument is an Unicode string
        kwargs = make_utf8(arguments)

        if self.secret:
            kwargs["api_sig"] = self.sign(kwargs)
        url = "https://%s%s" % (FlickrAPI.flickr_host, form_url)

        # construct POST data
        body = Multipart()

        for arg, value in kwargs.iteritems():
            part = Part({'name': arg}, value)
            body.attach(part)

        content = fileobj.read()
        fileobj.close()

        filepart = Part({'name': 'photo', 'filename': filename}, content, 'image/jpeg')
        body.attach(filepart)

        return self._FlickrAPI__wrap_in_parser(self._FlickrAPI__send_multipart, format,
                url, body, callback)
    
    def upload(self, filename, fileobj, callback=None, **kwargs):
        return self._FlickrAPI__upload_to_form(FlickrAPI.flickr_upload_form, filename, fileobj, callback, **kwargs)
