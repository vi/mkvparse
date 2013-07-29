import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "mkvparse",
    version = "0.0.5",
    author = "Vitaly Shukela",
    author_email = "vi0oss@gmail.com",
    description = ("Simple Python matroska (mkv) reading library."),
    license = "BSD",
    keywords = "mkv matroska",
    url = "https://github.com/vi/mkvparse",
    packages=['mkvparse'],
	package_dir={'mkvparse': ''},
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Topic :: Multimedia",
        "License :: OSI Approved :: MIT License",
    ],
)
