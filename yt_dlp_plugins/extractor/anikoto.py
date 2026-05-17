__version__ = '0.0.1'

import re

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import str_to_int


class AnikotoIE(InfoExtractor):
    IE_NAME = 'anikoto'
    _VALID_URL = r'https?://anikoto(?:tv)?\.(?:cz|to)/watch/(?P<id>[^/]+)'
    _HEADERS = {'x-requested-with': 'XMLHttpRequest'}

    eps_re = re.compile(
        r"""(?xi)<li\s+title="(?P<ep_title>[^"]+)"[^>]*>
        .*?
        data-id="(?P<ep_id>[^"]+)"\s
        .*?
        data-num="(?P<ep_num>[^"]+)"
        .*?
        data-ids="(?P<server_key>[^"]+)"
        """,
        re.DOTALL,
    )

    def _real_extract(self, url: str):
        slug = self._match_id(url)
        webpage = self._download_webpage(url, slug)
        ani_id = self._html_search_regex(r'data-id="([^"]+)', webpage, 'anime id')
        title = self._title(webpage, slug)
        return self.playlist_result(
            entries=self._entries(ani_id, title, slug), playlist_id=ani_id, playlist_title=title
        )

    def _title(self, webpage, slug):
        title = self._html_extract_title(webpage, default=slug)
        title = re.sub(r'(?i)^(?:Watch\s+|Free!\s+|Anime\s+)', '', title)
        return re.split(
            r'(?i)\s+(?:Episode\s+\d+|Online\s+with\s+SUB|Anime\s+Online|Watch\s+Online\s+Free|\||-)', title, maxsplit=1
        )[0].strip()

    def _entries(self, ani_id, title, slug):
        stream_ie = _MegaplayIE(self._downloader)
        for ep_info in self._get_all_episode_info(ani_id):
            new_ep_info = self._get_available_server(ep_info)
            formats = []
            subtitles = {}
            for stream in self._get_stream_url(new_ep_info):
                res = stream_ie.extract(stream['url'])
                for lang, sub_list in res.get('subtitles', {}).items():
                    subtitles.setdefault(lang, []).extend(sub_list)
                for f in res.get('formats', []):
                    formats.append(
                        {
                            **f,
                            'format_note': (stype := stream.get('type', 'unknown')),
                            'format_id': f'{stype}-{f.get("format_id")}',
                            'http_headers': res.get('http_headers', {}),
                        }
                    )
            yield {
                'id': ep_info.get('ep_id'),
                'display_id': slug,
                'title': ep_info.get('ep_title', title),
                'episode_number': str_to_int(ep_info.get('ep_num')),
                'formats': formats,
                'subtitles': subtitles,
            }

    def _call_api(self, url, video_id, note=None, query=None):
        return self._download_json(url, video_id, note, headers=self._HEADERS, query=query).get('result')

    def _get_all_episode_info(self, anime_id: str):
        result = self._call_api(
            url=f'https://anikoto.cz/ajax/episode/list/{anime_id}',
            video_id=anime_id,
            note='Downloading episode list',
        )
        for match in self.eps_re.finditer(result):
            yield match.groupdict()

    def _get_available_server(self, episode_info):
        server_key = episode_info['server_key']
        result = self._call_api(
            url='https://anikoto.cz/ajax/server/list',
            video_id=server_key[:5],
            note='Downloading server list',
            query={'servers': server_key},
        )
        episode_info['servers'] = re.findall(r'data-link-id="([^"]+)"', result)
        return episode_info

    def _get_stream_url(self, epinfo):
        for server_id in epinfo.get('servers', []):
            response = self._call_api(
                url='https://anikoto.cz/ajax/server/',
                video_id=server_id[:5],
                note='Downloading stream server',
                query={'get': server_id},
            )
            if not (url := response.get('url')) or len(parts := url.rsplit('/', 2)) < 3:
                continue
            yield {
                'url': url,
                'type': parts[2],
                **epinfo,
            }


class _MegaplayIE(InfoExtractor):
    """PRIVATE CLASS"""

    IE_NAME = AnikotoIE.IE_NAME
    _VALID_URL = (
        r'https?://(?:vidwish|megaplay)\.(?:buzz|live)/stream/s-2/(?P<id>[^/]+)/(?:h?sub|dub)(?:\?autostart=true)?'
    )

    def _real_extract(self, url: str):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id, headers={'referer': 'https://anikoto.cz/'})
        data_id = self._html_search_regex(r'data-id="([^"]+)"', webpage, 'data id')
        headers = {'referer': (base_url := url.rsplit('/', 4)[0]) + '/', 'x-requested-with': 'XMLHttpRequest'}
        sources = self._download_json(
            url_or_request=f'{base_url}/stream/getSources?id={data_id}',
            video_id=data_id,
            note='Downloading sources',
            headers=headers,
            fatal=not self.get_param('ignore_no_formats_error'),
        )
        subtitles = {}
        if not sources:
            return {
                'id': data_id,
                'title': data_id,
                'formats': [],
                'subtitles': subtitles,
            }
        for subs in sources.get('tracks', []):
            subtitles.setdefault(_Ngawi.l2s(label := subs.get('label')), []).append(
                {
                    'url': subs.get('file'),
                    'name': label,
                    'http_headers': headers,
                }
            )
        return {
            'id': video_id,
            'title': video_id,
            'formats': self._extract_m3u8_formats(sources.get('sources', {}).get('file'), data_id, headers=headers),
            'subtitles': subtitles,
            'http_headers': headers,
        }


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
        r'Spanish.*(?:Spain|European|CR)': 'es-es',
        r'Portuguese.*Brazil': 'pt-br',
        r'Chinese.*Simplified': 'zh-Hans',
        r'Chinese.*Traditional': 'zh-Hant',
        r'Chinese.*Hong Kong': 'zh-hk',
        r'Chinese.*China': 'zh-cn',
    }

    @classmethod
    def long2short(cls, amba):
        if not amba:
            return None

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

        return None

    @classmethod
    def l2s(cls, fuad45):
        return cls.long2short(fuad45)
