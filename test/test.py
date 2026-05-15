import yt_dlp

URLS = [
    'https://anikoto.cz/watch/the-warrior-princess-and-the-barbaric-king-snxwm',
    'https://anikoto.cz/watch/the-angel-next-door-spoils-me-rotten-season-2-imyza/ep-7',
    'https://anikoto.cz/watch/an-observation-log-of-my-fiancee-who-calls-herself-a-villainess-tsjbd/ep-7',
    'https://anikoto.cz/watch/wistoria-wand-and-sword-season-2-dua04',
]

ytdl_opts = {
    # 'verbose': True,
    # 'listformats': True,
    'test': True,
    'playlist_items': '1-3',
    'lazy_playlist': True,
    'ignore_no_formats_error': True,
    'outtmpl': '%(playlist_title)s/%(title)s.%(ext)s',
    'paths': {'home': 'test/anikoto'},
}

with yt_dlp.YoutubeDL(ytdl_opts) as y:
    y.download(URLS)
