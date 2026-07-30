import os
import platform

from .vlc import play as play_windows
from .mpv import play as play_linux
from .termux import play as play_termux


def play(stream, referer=None):

    sistema = platform.system()

    if "TERMUX_VERSION" in os.environ:
        return play_termux(stream, referer)

    if sistema == "Windows":
        return play_windows(stream, referer)

    return play_linux(stream, referer)