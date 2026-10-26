"""Lecture audio du verset / de la mishna.

Extrait de gui_hebreu.py (refactorisation en paquet gui/) : le mixin
AudioMixin regroupe toute la gestion du lecteur audio de l'onglet
« Livre » — synthèse (verse_audio), lecture/pause, navigation dans
le temps, changement de vitesse/voix, et le nettoyage à l'arrêt.

Le mixin suppose que la classe hôte fournit les widgets construits
dans _build_verse_tab (audio_button, audio_time, audio_scale,
audio_voice_combo, audio_speed_spin) et la file self._work_queue.
"""

import os
import tempfile
import threading
import tkinter as tk
from tkinter import messagebox

import verse_audio
from verse_audio import (
    VersePlayer,
    VersePlayerError,
    synthesize_wav,
    VOICES,
)
from bhsa_grammar.sefaria_client import fetch_mishnah_mishnayot
from gui.config import CORPUS_MISHNA


class AudioMixin:
    # --- Lecture audio du verset -----------------------------------------
    def _set_audio_error(self, msg):
        self.audio_time.configure(text=msg)
        self.audio_scale.state(["disabled"])

    def _current_verse_reference(self):
        """Référence actuellement sélectionnée (Bible ou Mishna), ou None
        si la sélection est incomplète. La comparaison avec le WAV en
        lecture se fait sur cette même chaîne (les traités Mishna sont
        indentés dans la liste : .strip() comme pour _start_audio_mishnah)."""
        fr = self.book_var.get()
        entry = self._book_index.get(fr)
        if entry is None:
            return None
        chap = self.chapter_var.get()
        verse = self.verse_var.get()
        if not chap or not verse:
            return None
        return f"{fr.strip()} {chap}:{verse}"

    def _on_audio_button(self):
        if self._audio_player is not None:
            # Référence courante ≠ celle du WAV en lecture (l'utilisateur a
            # affiché un autre verset) : on repart d'une synthèse du verset
            # courant, pas d'une reprise de l'ancien WAV.
            current_ref = self._current_verse_reference()
            if current_ref is not None and current_ref != self._audio_ref:
                self._stop_audio()
            else:
                # Bouton unique, machine à états : ⏸ pendant la lecture (clic
                # = pause), ▶ en pause ou en fin de lecture (clic = (re)
                # lecture depuis la position du curseur), ▶ au repos.
                player = self._audio_player
                if not player.is_playing() and not player.is_paused():
                    # Fin de lecture : relance à la position du curseur ; si
                    # le curseur est en fin de verset, on repart du début.
                    pos = player.position_ms()
                    if self._audio_duration_ms - pos < 50:
                        pos = 0
                        self.audio_pos.set(0)
                    try:
                        player.play(pos)
                        self.btn_audio.configure(text="⏸")
                    except VersePlayerError:
                        pass
                    self._poll_audio()
                    return
                self._toggle_audio_pause()
                return
        mishna = self.corpus_var.get() == CORPUS_MISHNA
        fr = self.book_var.get()
        entry = self._book_index.get(fr)
        if entry is None:
            messagebox.showwarning("Référence", "Sélectionnez un livre.")
            return
        bhsa, _b = entry
        chap = self.chapter_var.get()
        verse = self.verse_var.get()
        if not chap or not verse:
            messagebox.showwarning("Référence",
                                   "Sélectionnez chapitre et verset.")
            return
        if mishna:
            self._start_audio_mishnah(bhsa, fr.strip(), int(chap),
                                      int(verse))
            return
        if self.api is None:
            return
        try:
            speed = float(self.audio_speed.get())
            if not 0.5 <= speed <= 2.0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Vitesse",
                                   "Vitesse invalide : entrez une valeur "
                                   "entre 0.5 et 2.0.")
            return
        voice = self._voice_labels.get(self.audio_voice.get(), "shaul")
        reference = self._current_verse_reference()

        def fetch():
            from bhsa_grammar.reference import find_verse
            F, L, T = self.api.F, self.api.L, self.api.T
            node = find_verse(F, L, bhsa, int(chap), int(verse))
            if node is None:
                return None, reference
            return T.text(node), reference

        self._start_audio_synthesis(fetch, speed, voice, reference)

    def _start_audio_mishnah(self, tractate, fr, chapter, mishnah):
        """Lecture audio d'une mishna : texte hébreu « Torat Emet 357 » via
        l'API Sefaria (requiert le réseau, comme l'affichage), puis la même
        chaîne de synthèse phonikud-tts que pour le verset biblique."""
        try:
            speed = float(self.audio_speed.get())
            if not 0.5 <= speed <= 2.0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Vitesse",
                                   "Vitesse invalide : entrez une valeur "
                                   "entre 0.5 et 2.0.")
            return
        voice = self._voice_labels.get(self.audio_voice.get(), "shaul")
        reference = f"{fr} {chapter}:{mishnah}"

        def fetch():
            he = fetch_mishnah_mishnayot(tractate, chapter, "hebrew")
            if not he or not 1 <= mishnah <= len(he):
                return None, reference
            return he[mishnah - 1], reference

        self._start_audio_synthesis(fetch, speed, voice, reference)

    def _start_audio_synthesis(self, fetch, speed, voice, reference):
        """Sablier + thread de synthèse commun aux deux corpus.

        ``fetch`` est un callable exécuté dans le thread de travail qui
        renvoie ``(texte_hébreu_ou_None, reference)``.
        """
        self.btn_audio.state(["disabled"])
        self.audio_time.configure(text=f"Synthèse : {reference}…")
        # Sablier comme pour le chargement de la base : le premier usage
        # peut télécharger ~370 Mo de modèles phonikud-tts.
        self.root.configure(cursor="watch")

        def worker():
            hebrew, reference = fetch()
            if hebrew is None:
                self._work_queue.put(("audio_error",
                                      "Texte hébreu introuvable pour "
                                      f"{reference}."))
                return
            self._audio_last_text = hebrew
            path = os.path.join(tempfile.gettempdir(),
                                "analyse_hebreu_verse.wav")
            duration = synthesize_wav(hebrew, path, speed=speed, voice=voice)
            if duration is None or duration <= 0:
                detail = (("Détail : " + verse_audio.LAST_ERROR)
                          if verse_audio.LAST_ERROR else
                          "modèles phonikud-tts introuvables.")
                self._work_queue.put(("audio_error",
                                      "Synthèse vocale indisponible "
                                      f"({detail})"))
                return
            self._work_queue.put(("audio_ready", (path, duration, reference)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_audio_ready(self, path, duration_ms, reference=None,
                         resume_ms=None, start_paused=False):
        self._audio_ref = reference
        player = VersePlayer()
        try:
            length = player.open(path)
        except VersePlayerError as exc:
            player.close()
            self._set_audio_error(str(exc))
            self.btn_audio.state(["!disabled"])
            return
        self._audio_player = player
        self._audio_wav = path
        self._audio_duration_ms = max(1, duration_ms or length)
        self.btn_audio.configure(text="⏸")
        self.btn_audio.state(["!disabled"])
        self.root.configure(cursor="")
        self.audio_scale.state(["!disabled"])
        self.audio_scale.configure(to=self._audio_duration_ms)
        resume_ms = int(resume_ms) if resume_ms else 0
        self.audio_pos.set(min(resume_ms, self._audio_duration_ms))
        try:
            player.play(resume_ms)
        except VersePlayerError as exc:
            self._set_audio_error(str(exc))
            self._stop_audio()
            return
        if start_paused:
            player.pause()
            self.btn_audio.configure(text="▶")
        self._poll_audio()

    def _on_audio_error(self, msg):
        self._set_audio_error(msg)
        self.btn_audio.state(["!disabled"])
        self.root.configure(cursor="")

    def _resynthesize_current(self, reason):
        """Resynthétise le verset courant (vitesse ou voix changée en cours
        de lecture) et reprend la lecture à la position proportionnelle."""
        if self._audio_player is None or self._audio_last_text is None:
            return
        try:
            speed = float(self.audio_speed.get())
            if not 0.5 <= speed <= 2.0:
                return
        except ValueError:
            return
        voice = self._voice_labels.get(self.audio_voice.get(), "shaul")
        text = self._audio_last_text
        was_paused = self._audio_player.is_paused()
        pos = self._audio_player.position_ms()
        old_dur = self._audio_duration_ms or 1
        self._stop_audio()
        self.btn_audio.state(["disabled"])
        self.audio_time.configure(text=reason)
        self.root.configure(cursor="watch")

        def worker():
            path = os.path.join(tempfile.gettempdir(),
                                "analyse_hebreu_verse.wav")
            duration = synthesize_wav(text, path, speed=speed, voice=voice)
            if duration is None or duration <= 0:
                detail = (("Détail : " + verse_audio.LAST_ERROR)
                          if verse_audio.LAST_ERROR else
                          "modèles phonikud-tts introuvables.")
                self._work_queue.put(("audio_error",
                                      "Synthèse vocale indisponible "
                                      f"({detail})"))
                return
            ratio = duration / float(old_dur)
            self._work_queue.put(
                ("audio_ready", (path, duration, self._audio_ref,
                                 int(pos * ratio), was_paused)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_audio_speed_change(self, event=None):
        self._resynthesize_current("Resynthèse à la nouvelle vitesse…")

    def _on_audio_voice_change(self, event=None):
        self._resynthesize_current("Resynthèse avec la nouvelle voix…")

    def _toggle_audio_pause(self):
        if self._audio_player is None:
            return
        if self._audio_player.is_paused():
            self._audio_player.play()
            self.btn_audio.configure(text="⏸")
        else:
            self._audio_player.pause()
            self.btn_audio.configure(text="▶")

    def _on_audio_seek(self, value):
        if self._audio_player is None or self._audio_seeking:
            return
        self._audio_seeking = True
        try:
            self._audio_player.seek(float(value))
        except VersePlayerError:
            pass
        finally:
            self._audio_seeking = False

    def _poll_audio(self):
        if self._audio_player is None or self._audio_polling:
            return
        self._audio_polling = True

        def tick():
            self._audio_polling = False
            player = self._audio_player
            if player is None:
                return
            if not player.is_playing() and not player.is_paused():
                # Fin du verset : le lecteur reste ouvert et le curseur
                # actif — ▶ relance la lecture à la position du curseur.
                # La position MCI peut être retombée à 0 : on ne touche
                # pas au curseur, il marque l'endroit atteint.
                self.btn_audio.configure(text="▶")
                return
            if not self._audio_seeking:
                pos = player.position_ms()
                self.audio_pos.set(pos)
                self._update_audio_time(pos)
            self.root.after(200, tick)

        self.root.after(200, tick)

    def _update_audio_time(self, pos_ms):
        dur = self._audio_duration_ms

        def fmt(ms):
            return f"{int(ms) // 60000}:{int(ms) % 60000 // 1000:02d}"

        self.audio_time.configure(text=f"{fmt(pos_ms)} / {fmt(dur)}")

    def _stop_audio(self):
        player = self._audio_player
        self._audio_player = None
        self._audio_wav = None
        self._audio_ref = None
        self.root.configure(cursor="")
        if player is not None:
            player.stop()
            player.close()
        self.btn_audio.configure(text="▶")
        self.audio_scale.state(["disabled"])
        self.audio_pos.set(0)
        self._audio_duration_ms = 0
        self.audio_time.configure(text="0:00 / 0:00")
