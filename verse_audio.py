"""Lecture audio du verset : synthèse WAV (SAPI5) et lecteur MCI.

- ``synthesize_wav(text, path)`` : produit un fichier WAV à partir du texte
  hébreu via la voix SAPI installée (Synthèse vocale Windows), puis renvoie
  la durée en millisecondes lue dans l'en-tête WAV. Le texte est normalisé
  (teamim et nikkud retirés : la voix lit les consonnes).
- ``VersePlayer`` : lecteur fondé sur MCI (winmm) qui expose position,
  durée, lecture/pause/reprise, arrêt et déplacement du curseur (seek).

Hors Windows, ces fonctions sont inopérantes : ``synthesize_wav`` renvoie
``None`` et ``VersePlayer`` lève une erreur explicite à l'ouverture — l'interface
graphique désactive alors le bouton et affiche un message.
"""

import ctypes
import re
import sys
import wave

_ALIAS = "analyse_hebreu_verse"


_MCI_HEBREW_LETTERS = re.compile(
    "[^\u05d0-\u05ea ]")


def strip_marks(text):
    """Retire teamim, nikkud et signes parasites du texte hébreu."""
    text = text.replace("\u05be", " ")
    return _MCI_HEBREW_LETTERS.sub("", text)


def wave_duration_ms(path):
    """Durée du fichier WAV en millisecondes (via l'en-tête)."""
    with wave.open(path, "rb") as wav:
        frames = wav.getnframes()
        rate = wav.getframerate() or 1
    return int(round(frames * 1000.0 / rate))


def synthesize_wav(text, path):
    """Synthétise ``text`` en WAV dans ``path`` ; renvoie la durée en ms.

    Renvoie ``None`` si la synthèse est indisponible (hors Windows ou
    voix SAPI introuvable).
    """
    if sys.platform != "win32":
        return None
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        return None
    try:
        pythoncom.CoInitialize()
        voice = win32com.client.Dispatch("SAPI.SpVoice")
        stream = win32com.client.Dispatch("SAPI.SpFileStream")
        try:
            stream.Format.Type = 22  # SAFT22kHz16BitMono
            stream.Open(path, 3)  # SSFMCreateForWrite
            voice.AudioOutputStream = stream
            voice.Speak(strip_marks(text), 0)  # SVSFDefault : synchrone
        finally:
            try:
                stream.Close()
            except Exception:  # noqa: BLE001
                pass
    except Exception:  # noqa: BLE001
        return None
    try:
        return wave_duration_ms(path)
    except (OSError, wave.Error):
        return None


class VersePlayerError(Exception):
    """Erreur renvoyée par MCI."""


def _mci():
    return ctypes.windll.winmm


class VersePlayer:
    """Lecteur MCI minimal avec contrôle de la position (seek).

    Le fichier est ouvert avec le périphérique ``mpegvideo`` (Quartz),
    qui accepte aussi les WAV et autorise le seek arbitraire — le
    périphérique ``waveaudio`` ne se positionne qu'aux frontières
    d'échantillonnage.
    """

    def __init__(self):
        self._playing = False
        self._paused = False
        self._opened = False

    def _send(self, command):
        buf = ctypes.create_unicode_buffer(256)
        err = _mci().mciSendStringW(command, buf, 255, 0)
        if err:
            msg = ctypes.create_unicode_buffer(256)
            _mci().mciGetErrorStringW(err, msg, 255)
            raise VersePlayerError(msg.value or f"Erreur MCI {err}")

    def open(self, path):
        """Ouvre le fichier WAV ; renvoie sa durée en ms."""
        self.close()
        self._send(f'open "{path}" type mpegvideo alias {_ALIAS}')
        self._opened = True
        return self.length_ms()

    def close(self):
        if self._opened:
            try:
                self._send(f"close {_ALIAS}")
            except VersePlayerError:
                pass
        self._opened = False
        self._playing = False
        self._paused = False

    def _status(self, what):
        buf = ctypes.create_unicode_buffer(64)
        err = _mci().mciSendStringW(
            f"status {_ALIAS} {what}", buf, 63, 0)
        if err:
            return 0
        try:
            return int(buf.value)
        except ValueError:
            return 0

    def length_ms(self):
        return self._status("length")

    def position_ms(self):
        return self._status("position")

    def mode(self):
        buf = ctypes.create_unicode_buffer(32)
        _mci().mciSendStringW(f"status {_ALIAS} mode", buf, 31, 0)
        return buf.value

    def is_playing(self):
        return self.mode() == "playing"

    def is_paused(self):
        return self.mode() == "paused"

    def play(self, from_ms=None):
        if not self._opened:
            raise VersePlayerError("Aucun fichier audio ouvert.")
        if self.is_paused():
            self._send(f"resume {_ALIAS}")
        else:
            pos = int(from_ms) if from_ms is not None else self.position_ms()
            self._send(f"play {_ALIAS} from {pos}")
        self._playing = True
        self._paused = False

    def pause(self):
        if self._opened and self.is_playing():
            self._send(f"pause {_ALIAS}")
            self._paused = True

    def stop(self):
        if self._opened:
            try:
                self._send(f"stop {_ALIAS}")
            except VersePlayerError:
                pass
            try:
                self._send(f"seek {_ALIAS} to start")
            except VersePlayerError:
                pass
        self._playing = False
        self._paused = False

    def seek(self, ms):
        was_playing = self.is_playing()
        if not self._opened:
            return
        ms = max(0, int(ms))
        self._send(f"seek {_ALIAS} to {ms}")
        if was_playing:
            self._send(f"play {_ALIAS}")
            self._playing = True
        else:
            self._paused = False
