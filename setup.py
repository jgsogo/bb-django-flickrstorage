#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
        name="django-flickrstorage",
        version="0.1",
        packages=find_packages(),
        author="slav0nic",
        author_email="slav0nic0@gmail.com",
        description="django flickr.net image storage.",
        license="BSD",
        keywords="django",
        url="http://bitbucket.org/slav0nic/django-flickrstorage/wiki/Home",
        install_requires=["flickrapi"]
)
