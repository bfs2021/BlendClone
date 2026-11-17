import threading

import pytest

from app import media


def test_download_reports_readable_error_when_yt_dlp_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(media, 'validate_url', lambda url: None)

    def fail(*args, **kwargs):
        raise RuntimeError('ERROR: Private video')

    monkeypatch.setattr(media, 'run', fail)
    cancel = threading.Event()
    with pytest.raises(ValueError, match='Could not download'):
        media.download('https://youtube.com/watch?v=private', tmp_path / 'source.bin', cancel)
