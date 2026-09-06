from yt_dlp.utils import ExtractorError

from .common import AnikotoBaseIE


class AnikotoIE(AnikotoBaseIE):
    _VALID_URL = r'https://anikoto\.cz/watch/(?P<title>[^/]+)/ep-(?P<ep>\d+)$'
    # https://anikoto.cz/watch/please-put-them-on-takamine-san-pfv4v/ep-2

    def _real_extract(self, url: str):
        title, episode = self._match_valid_url(url).groups()
        title = ' '.join(title.split('-')[:-1])
        data_id = self._get_data_id(url, title)

        if not (jeson := self._get_ep_info(data_id=data_id, episode=episode)):
            raise ExtractorError(
                f'Episode {episode} is not available for this anime (maximum available episode might be lower)',
                expected=True,
            )
        if not (servers := self._get_available_server(jeson['server_key'])):
            raise ExtractorError(f'No streaming servers found for Episode {episode}', expected=True)
        if not (info := self._get_stream_info(servers)):
            self.raise_no_formats(f'No playable streams found for Episode {episode}', expected=True)

        return {
            'id': jeson['ep_id'],
            'title': title,
            'episode': int(episode),
            **info,
        }


class AnikotoTvIE(AnikotoIE):
    IE_NAME = AnikotoIE.IE_NAME + 'tv'
    _VALID_URL = r'https://anikototv\.to/watch/(?P<title>[^/]+)/ep-(?P<ep>\d+)$'


# vi:nowrap
