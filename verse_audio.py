"""Lecture audio du verset : synthèse WAV (phonikud-tts) et lecteur MCI.

- ``synthesize_wav(text, path)`` : produit un fichier WAV à partir du texte
  hébreu voyellé via **phonikud-tts** (exécution locale, ONNX Runtime) puis
  renvoie la durée en millisecondes lue dans l'en-tête WAV. Le texte est
  normalisé (teamim retirés, nikkud conservé : c'est lui qui porte la
  vocalisation). Les modèles (Phonikud + voix Piper « shaul », ~370 Mo au
  total) sont téléchargés au premier usage dans le cache Hugging Face.
- ``VersePlayer`` : lecteur fondé sur MCI (winmm) qui expose position,
  durée, lecture/pause/reprise, arrêt et déplacement du curseur (seek).

Dépendances : ``phonikud-tts`` (pip) qui fournit ``phonikud``,
``phonikud-onnx``, ``piper-onnx``, ``onnxruntime``, ``espeakng-loader`` et
``soundfile``. Sous Windows, MCI (winmm) lit le WAV ; ailleurs le lecteur
est inopérant et l'interface affiche un message.
"""

import ctypes
import re
import wave

_ALIAS = "analyse_hebreu_verse"

# Teamim (accents massorétiques) : ils portent le chant, pas la
# vocalisation — retirés pour une lecture parlée ; le nikkud est conservé.
_TEAMIM = re.compile("[\u0591-\u05af\u05bd\u05c0\u05c3-\u05c7]")


def strip_teamim(text):
    """Retire les accents massorétiques (teamim), garde le nikkud."""
    return _TEAMIM.sub("", text)


# Tétragramme et ses formes avec préfixe (ב/כ/ל/מ/ה + patach).
# La tradition massorétique ne prononce jamais le Tétragramme : on lit
# אֲדֹנָי (Adonaï) — et pour les formes préfixées (לַיהוָה), la voyelle
# du préfixe est réportée sur l'aleph : לַאדֹנָי (« la-Donaï »).
# Substitution faite uniquement pour la synthèse vocale (l'affichage et
# l'analyse grammaticale gardent le texte biblique intact).
_TETRAGRAMMATON_FORMS = {
    # Tétragramme simple — le texte BHSA (Codex de Leningrad) écrit la
    # forme Qéré Perpétuel SANS holam (יְהוָה) ; la forme avec holam
    # (יְהֹוָה) figure dans certaines éditions. Les deux sont couvertes,
    # avec ou sans nikkud.
    "יְהֹוָה": "אֲדֹנָי",
    "יְהוָה": "אֲדֹנָי",
    "יהוה": "אֲדֹנָי",
    "יהוָה": "אֲדֹנָי",
    # Variantes avec hatef-segol sous le yod (lecture Elohim, quand le
    # Tétragramme est adjacent à אֲדֹנָי) — avec et sans holam (la BHSA
    # écrit la forme sans holam), avec et sans nikkud.
    "יֱהֹוִה": "אֱלֹהִים",
    "יֱהוִה": "אֱלֹהִים",
    # Graphie Leningrad/BHSA avec shva simple sous le yod et hiriq
    # (Ps 109:21 : יְהוִה) — voyelles mixtes, lecture Elohim.
    "יְהֹוִה": "אֱלֹהִים",
    "יְהוִה": "אֱלֹהִים",
    "יהוִה": "אֱלֹהִים",
    # Formes préfixées : le patach du préfixe est réporté sur l'aleph
    # (qéré perpétuel) — לַיהוָה -> לַאדֹנָי (« la-Adonaï »). La BHSA
    # écrit aussi la forme contractée avec hé (לַהוָה).
    "לַיהֹוָה": "לַאדֹנָי",
    "לַיהוָה": "לַאדֹנָי",
    "לַהוָה": "לַאדֹנָי",
    "לַיהוה": "לַאדֹנָי",
    "לַהוה": "לַאדֹנָי",
    "בַּיהֹוָה": "בַּאדֹנָי",
    "בַּיהוָה": "בַּאדֹנָי",
    "בַּהוָה": "בַּאדֹנָי",
    "בַּיהוה": "בַּאדֹנָי",
    "כַּיהֹוָה": "כַּאדֹנָי",
    "כַּיהוָה": "כַּאדֹנָי",
    "כַּהוָה": "כַּאדֹנָי",
    "כַּיהוה": "כַּאדֹנָי",
    "מַיהֹוָה": "מַאדֹנָי",
    "מַיהוָה": "מַאדֹנָי",
    "מַהוָה": "מַאדֹנָי",
    "מַיהוה": "מַאדֹנָי",
    "וַיהֹוָה": "וַאדֹנָי",
    "וַיהוָה": "וַאדֹנָי",
    "וַהוָה": "וַאדֹנָי",
    "וַיהוה": "וַאדֹנָי",
}


def substitute_tetragrammaton(text):
    """Remplace le Tétragramme (et formes préfixées) par Adonaï pour la
    lecture — ou par Elohim quand il est adjacent à אֲדֹנָי.

    Deux lectures traditionnelles (qéré perpétuel) :
    - Adonaï par défaut ;
    - Elohim quand le Tétragramme précède ou suit immédiatement
      אֲדֹנָי, pour éviter « Adonaï Adonaï » : Ps 109:21 (יְהוָה
      אֲדֹנָי) se lit « Elohim Adonaï ». Dans l'ordre אֲדֹנָי + YHWH,
      la massore signale Elohim par le hatef-segol (יֱהוִה, déjà couvert
      par la table) ; dans l'ordre inverse, la graphie est identique à la
      forme normale : la substitution contextuelle est nécessaire.
    """
    # Cas contextuel : YHWH (graphie normale) immédiatement suivi de
    # אֲדֹנָי -> Elohim. Teamim/espaces déjà retirés ou réduits ; on
    # tolère un espace ou un maqaf (־) entre les deux mots.
    for yhwh in ("יְהֹוָה", "יְהוָה", "יהוה", "יהוָה"):
        for sep in (" ", "־"):
            text = text.replace(yhwh + sep + "אֲדֹנָי",
                               "אֱלֹהִים" + sep + "אֲדֹנָי")
    for src, dst in _TETRAGRAMMATON_FORMS.items():
        text = text.replace(src, dst)
    return text


def wave_duration_ms(path):
    """Durée du fichier WAV en millisecondes (via l'en-tête)."""
    with wave.open(path, "rb") as wav:
        frames = wav.getnframes()
        rate = wav.getframerate() or 1
    return int(round(frames * 1000.0 / rate))


_MODELS = {}

# Voix disponibles dans le dépôt de checkpoints (Piper ONNX, mono-locuteur).
# « grave » = f0 médian ≈ 111 Hz, « shaul » ≈ 133 Hz (mesuré sur Gen 1:1).
VOICES = {
    "shaul": {"label": "Shaul", "model": "shaul.onnx"},
    "michael": {"label": "Michael (grave)", "model": "michael.onnx"},
}


def _download_quiet(repo, filename):
    """Télécharge un fichier du Hub en neutralisant l'avertissement stderr
    « You are sending unauthenticated requests to the HF Hub » émis par le
    backend de téléchargement (hf_xet) : le téléchargement anonyme est
    normal ici (modèles publics, pas de compte requis), le message n'a
    donc pas lieu d'apparaître dans la console de l'utilisateur."""
    import contextlib
    import os
    import sys
    from huggingface_hub import hf_hub_download

    sys.stderr.flush()
    saved = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, 2)
        with contextlib.redirect_stderr(sys.stderr):
            return hf_hub_download(repo, filename)
    finally:
        os.dup2(saved, 2)
        os.close(devnull)
        os.close(saved)


def _get_models(voice="shaul"):
    """Charge (une seule fois par voix) le modèle Piper correspondant."""
    voice = voice if voice in VOICES else "shaul"
    if voice in _MODELS:
        return _MODELS[voice]
    from phonikud_tts import Piper

    tts_dir = _download_quiet("thewh1teagle/phonikud-tts-checkpoints",
                              VOICES[voice]["model"])
    cfg = _download_quiet("thewh1teagle/phonikud-tts-checkpoints",
                          "model.config.json")
    _MODELS[voice] = Piper(tts_dir, cfg)
    return _MODELS[voice]


def synthesize_wav(text, path, speed=1.0, voice="shaul"):
    """Synthétise ``text`` en WAV dans ``path`` ; renvoie la durée en ms.

    ``speed`` (> 1 = plus vite) ajuste le ``length_scale`` de Piper : la
    vitesse agit sur la synthèse, pas sur la lecture, donc la voix reste
    naturelle à toute vitesse. Le texte du verset biblique étant déjà
    voyellé, il est passé directement au phonétiseur phonikud (le modèle de
    diacritisation ne sert que pour du texte non voyellé). Renvoie ``None``
    en cas d'échec (dépendances manquantes, modèle introuvable, erreur).
    """
    import soundfile as sf
    from phonikud import phonemize

    try:
        piper = _get_models(voice)
        phonemes = phonemize(substitute_tetragrammaton(strip_teamim(text)))
        length_scale = piper.config["inference"]["length_scale"]
        if speed and speed > 0 and speed != 1.0:
            length_scale = length_scale / float(speed)
        samples, rate = piper.create(phonemes, is_phonemes=True,
                                    length_scale=length_scale)
        if samples is None or len(samples) == 0:
            return None
        sf.write(path, samples, rate)
    except Exception:  # noqa: BLE001
        return None
    try:
        return wave_duration_ms(path)
    except (OSError, wave.Error):
        return None


class VersePlayerError(Exception):
    """Erreur renvoyée par MCI."""


def _mci():
    import ctypes
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
