import re

from yt_dlp.extractor.common import InfoExtractor


class MegaPlayIE(InfoExtractor):
    IE_NAME = 'megaplay:buzz'
    _VALID_URL = r'https://megaplay\.buzz/stream/s-2/(?P<id>[^/]+)/(?:h?[sd]ub)$'

    # https://megaplay.buzz/stream/s-2/136052/sub?autostart=true
    _BASE_URL = 'https://megaplay.buzz/'
    _HEADERS = {'referer': _BASE_URL}

    def _real_extract(self, url: str):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, headers={'referer': 'https://anikoto.cz/'})
        data_id = self._html_search_regex(r'data-id="([^"]+)"', webpage, 'data id')

        sources = self._download_json(
            f'{self._BASE_URL}stream/getSources',
            data_id,
            query={'id': data_id},
            headers=self._HEADERS,
        )
        ##print(self._HEADERS)
        if not (m3u8_url := sources.get('sources').get('file')):
            return {}
        return {
            'id': video_id,
            'title': data_id,
            'formats': self._extract_m3u8_formats(m3u8_url, data_id, headers=self._HEADERS),
            'subtitles': self._parse_subtitles(sources),
            'http_headers': self._HEADERS,
        }

    def _parse_subtitles(self, sources):
        subtitles = {}
        if not (tracks := sources.get('tracks')) and not isinstance(tracks, list):
            return subtitles  # {}
        for t in tracks:
            if not (url := t.get('file')):
                continue
            subtitles.setdefault(_Ngawi.l2s(label := t.get('label')), []).append(
                {'url': url, 'name': label, 'http_headers': self._HEADERS}
            )
        return subtitles


class _Ngawi:
    _patterns = {
        r'English': 'en',
        r'Indonesian': 'id',
        r'Malay': 'ms',
        r'Thai': 'th',
        r'Vietnamese': 'vi',
        r'French': 'fr',
        r'German': 'de',
        r'Italian': 'it',
        r'Russian': 'ru',
        r'Arabic': 'ar',
        r'Spanish.*Latin': 'es-419',
        r'Spanish': 'es',
        r'Spanish.*(?:Spain|European|CR)': 'es-es',
        r'Portuguese.*Brazil': 'pt-br',
        r'Chinese.*Simplified': 'zh-Hans',
        r'Chinese.*Traditional': 'zh-Hant',
        r'Chinese.*Hong Kong': 'zh-hk',
        r'Chinese.*China': 'zh-cn',
        r'Chinese': 'zh',
        r'Korean': 'ko',
        r'Japanese': 'ja',
    }

    @classmethod
    def long2short(cls, amba):
        if not amba:
            return 'unknown'

        clean_amba = re.sub(r'_+|\s+', ' ', amba).strip()

        for rusdi, imut in cls._patterns.items():
            if re.search(rusdi, clean_amba, re.IGNORECASE):
                if re.search(r'signs', clean_amba, re.IGNORECASE):
                    return f'{imut}-signs'
                if re.search(r'closed captions|cc', clean_amba, re.IGNORECASE):
                    return f'{imut}-cc'
                if re.search(r'forced', clean_amba, re.IGNORECASE):
                    return f'{imut}-forced'
                if re.search(r'\(ai\)|ai', clean_amba, re.IGNORECASE):
                    return f'{imut}-ai'
                if '[CR]' in clean_amba:
                    return f'{imut}-cr'

                return imut

        return clean_amba  # Hytam -> white

    @classmethod
    def l2s(cls, fuad45):
        return cls.long2short(fuad45)


# vi:nowrap
