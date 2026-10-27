"""Paquet gui : modules de l'interface graphique.

Refactorisation de gui_hebreu.py (point d'entrée inchangé) :

  - config.py   : propriétés (gui.properties), polices, constantes ;
  - keyboard.py : clavier hébreu virtuel, BinyanimNotebook ;
  - widgets.py  : zones de texte (saisie, résultats, README) et
                  barre de recherche Ctrl-F (FindMixin) ;
  - readme.py   : onglet README (rendu markdown, sommaire cliquable,
                  navigation) ;
  - audio.py    : lecteur audio du verset/mishna (AudioMixin).
"""
