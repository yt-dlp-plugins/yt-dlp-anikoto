__version__ = '0.0.3'
from .anikoto import AnikotoIE, AnikotoTvIE

for _cls in (AnikotoIE, AnikotoTvIE):
    _cls.__module__ = 'yt_dlp_plugins.extractor.anikoto'
