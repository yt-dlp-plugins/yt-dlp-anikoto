import re

from yt_dlp.extractor.common import InfoExtractor


class AnikotoBaseIE(InfoExtractor):
    IE_NAME = 'anikoto'
    _HEADERS = {'x-requested-with': 'XMLHttpRequest'}

    def _get_data_id(self, url, title) -> str:
        # Check the cache, if available.
        if not (webpage := self.cache.load(self.IE_NAME, title)):
            # If it doesn't exist, then we download the webpage.
            webpage = self._download_webpage(url, title)
            self.cache.store(self.IE_NAME, title, webpage)

        return self._html_search_regex(r'data-id="([^"]+)', webpage, 'anime id')

    def _get_ep_info(self, data_id: str, episode: str) -> dict:
        result = (
            self._download_json(
                url_or_request=f'https://anikoto.cz/ajax/episode/list/{data_id}',
                video_id=data_id,
                note='Downloading episode info',
                headers=self._HEADERS,
            ).get('result')
            or ''
        )
        match = re.search(
            rf'<a\s+href="#"[^>]*data-id="(?P<ep_id>[^"]+)"[^>]*data-num="{episode}"[^>]*data-ids="(?P<server_key>[^"]+)"',
            result,
        )
        return match.groupdict() if match else {}

    def _get_available_server(self, server_key: str) -> list[str]:
        result = (
            self._download_json(
                url_or_request='https://anikoto.cz/ajax/server/list',
                video_id=server_key[:5],
                note='Downloading server list',
                query={'servers': server_key},
                headers=self._HEADERS,
            ).get('result')
            or ''
        )
        return re.findall(r'data-link-id="([^"]+)"', result)

    def _get_stream_info(self, servers: list[str]) -> dict:
        for server in servers:
            try:
                response = self._download_json(
                    url_or_request='https://anikoto.cz/ajax/server/',
                    video_id=server[:5],
                    note='Downloading stream server',
                    query={'get': server},
                    headers=self._HEADERS,
                )
                url = response['result']['url']
                return self._downloader.extract_info(url, download=False, process=False)
            except Exception:
                continue
        return {}


# vi:ft=python:nowrap
