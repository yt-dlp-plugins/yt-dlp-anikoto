from yt_dlp.extractor.common import InfoExtractor


class VidtubeIE(InfoExtractor):
    IE_NAME = 'vidtube'
    _VALID_URL = r'https://vidtube\.site/stream/(?P<id>[^/]+)/(?P<type>h?[sd]?ub)$'
    #  https://vidtube.site/stream/aDFHRmJ2SzFzcEtBSEhlMzU5T01UaUx4aTYzMUdiY3c0U2pYNSs0UU1FYjVqTVN2V3hibkdXZXdFL2Zubldubw/sub
    _BASE_URL = 'https://vidtube.site/'

    def _real_extract(self, url: str):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id[:5])
        data_id = self._html_search_regex(r'data-id="([^"]+)"', webpage, 'data id')
        sources = self._download_json(f'{self._BASE_URL}stream/getSourcesNew', data_id, query={'id': data_id})

        if not (m3u8_url := sources.get('sources').get('file')):
            return {}

        return {
            'id': video_id,
            'title': data_id,
            'formats': self._extract_m3u8_formats(m3u8_url, data_id, headers={'referer': self._BASE_URL}),
        }


# vi: nowrap
