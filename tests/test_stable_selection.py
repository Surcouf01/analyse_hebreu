# -*- coding: utf-8 -*-
"""Tests du module stable_selection (sélection à la souris stable sur
l'hébreu vocalisé dans tk.Text, sans serveur X : le widget est simulé).

Exécution :
  python -m unittest tests.test_stable_selection -v
"""

import re
import unittest

try:
    import tkinter as tk
except ImportError:
    tk = None

from stable_selection import StableSelection


class FakeText:
    """Simulation minimale d'un tk.Text en ordre logique.

    Implémente le sous-ensemble de l'API utilisé par StableSelection :
    index (avec « + 1 c », « - 1 c », linestart, lineend, end), get,
    compare, tag_remove/tag_add, mark_set, bbox, bind, focus_set.
    """

    def __init__(self, text):
        self.lines = text.split("\n")
        self.sel = []
        self.insert = "1.0"
        self.events = []
        self.cur = "1.0"
        self.end_index = "%d.0" % (len(self.lines) + 1)
        self.lastchar = "%d.%d" % (len(self.lines), len(self.lines[-1]))

    def _parse(self, idx):
        line, col = idx.split(".")
        return int(line) - 1, int(col)

    def index(self, idx):
        if idx.startswith("@"):
            return self.cur
        if idx == "insert":
            return self.insert
        if idx == "end":
            return self.end_index
        if idx == "end - 1 c":
            return self.lastchar
        m = re.match(r"^(\d+)\.(\d+) \+ 1 c$", idx)
        if m:
            line, col = int(m.group(1)) - 1, int(m.group(2))
            if line >= len(self.lines):
                return self.end_index
            if col >= len(self.lines[line]):
                if line + 2 <= len(self.lines):
                    return "%d.0" % (line + 2)
                return self.end_index
            return "%d.%d" % (line + 1, col + 1)
        m = re.match(r"^(\d+)\.(\d+) - 1 c$", idx)
        if m:
            line, col = int(m.group(1)) - 1, int(m.group(2))
            if col == 0:
                if line == 0:
                    return "1.0"
                return "%d.%d" % (line, len(self.lines[line - 1]))
            return "%d.%d" % (line + 1, col - 1)
        m = re.match(r"^(\d+)\.(\d+) (linestart|lineend)$", idx)
        if m:
            line = int(m.group(1)) - 1
            if m.group(3) == "linestart":
                return "%d.0" % (line + 1)
            return "%d.%d" % (line + 1, len(self.lines[line]))
        return idx

    def get(self, idx):
        idx = self.index(idx)
        line, col = self._parse(idx)
        if line >= len(self.lines):
            return ""
        if col >= len(self.lines[line]):
            return "\n"
        return self.lines[line][col]

    def compare(self, i1, op, i2):
        i1 = self.index(i1)
        i2 = self.index(i2)
        l1, c1 = self._parse(i1)
        l2, c2 = self._parse(i2)
        return eval("(l1, c1) %s (l2, c2)" % op)

    def tag_remove(self, *args):
        self.sel = []

    def tag_add(self, tag, first, last):
        self.sel = [first, last]

    def mark_set(self, mark, value):
        self.insert = value

    def focus_set(self):
        pass

    def bbox(self, index):
        return None

    def bind(self, sequence, handler):
        self.events.append((sequence, handler))


class Event:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


# Genèse 1:1 (avec nikkud) : les clusters base+marques se chevauchent à
# l'écran — c'est le cas où la sélection par défaut de Tk « danse ».
GEN11 = "בְּרֵאשִׁית בָּרָא"
# Colonnes : ב(0) ְ(1) ר(2) ֵ(3) א(4) ִ(5) ׁ(6) ת(7) ' '(8)
# Colonnes : ב(0) ְ(1) ּ(2) | ר(3) ֵ(4) | א(5) | ש(6) ִ(7) ׁ(8) | י(9) |
#            ת(10) | ' '(11) | ב(12) ָ(13) ּ(14) | ר(15) ָ(16) | א(17)

class TestClusters(unittest.TestCase):
    def setUp(self):
        self.t = FakeText(GEN11)
        self.sel = StableSelection(self.t)

    def test_cluster_start_reaches_base(self):
        # Colonne 1 (sheva) : le cluster commence à la base ב (col 0).
        self.assertEqual(self.sel._cluster_start("1.1"), "1.0")

    def test_cluster_start_on_base_is_stable(self):
        self.assertEqual(self.sel._cluster_start("1.0"), "1.0")

    def test_cluster_end_after_marks(self):
        # Cluster בְּ : fin (exclusive) après les marques.
        self.assertEqual(self.sel._cluster_end("1.0"), "1.3")
        # Cluster שִׁ (cols 6-8) : fin col 9.
        self.assertEqual(self.sel._cluster_end("1.6"), "1.9")

    def test_nearest_cluster_skips_orphan_marks(self):
        # Clic simulé sur un nikkud (col 13, cluster בָּ col 12) :
        # la borne est arrimée au bord du cluster, pas au milieu.
        self.t.cur = "1.13"
        self.assertEqual(self.sel._nearest_cluster_index(0, 0), "1.12")


class TestHandlers(unittest.TestCase):
    def setUp(self):
        self.t = FakeText(GEN11)
        self.sel = StableSelection(self.t)
        self.e = Event()

    def test_press_sets_anchor_and_breaks(self):
        self.t.cur = "1.3"
        self.assertEqual(self.sel._press(self.e), "break")
        self.assertEqual(self.sel.anchor, "1.3")
        self.assertEqual(self.t.insert, "1.3")
        self.assertEqual(self.t.sel, [])

    def test_drag_selects_ordered_range(self):
        self.t.cur = "1.3"
        self.sel._press(self.e)
        self.t.cur = "1.9"
        self.assertEqual(self.sel._drag(self.e), "break")
        self.assertEqual(self.t.sel, ["1.3", "1.9"])
        # Drag inverse (ancre > position) : bornes réordonnées.
        self.t.cur = "1.0"
        self.assertEqual(self.sel._drag(self.e), "break")
        # La sélection va du point courant à l'ancre, pas à l'ancien max.
        self.assertEqual(self.t.sel, ["1.0", "1.3"])

    def test_release_clears_anchor(self):
        self.t.cur = "1.0"
        self.sel._press(self.e)
        self.assertEqual(self.sel._release(self.e), "break")
        self.assertIsNone(self.sel.anchor)

    def test_double_click_selects_word(self):
        self.t.cur = "1.7"
        self.assertEqual(self.sel._double_click(self.e), "break")
        # Premier mot entier, bornes sur bords de clusters.
        self.assertEqual(self.t.sel, ["1.0", "1.12"])

    def test_triple_click_selects_line(self):
        self.t.cur = "1.7"
        self.assertEqual(self.sel._triple_click(self.e), "break")
        self.assertEqual(self.t.sel, ["1.0", "2.0"])

    def test_shift_press_extends_from_insert(self):
        self.t.cur = "1.9"
        self.sel.anchor = None
        self.t.insert = "1.0"
        self.assertEqual(self.sel._shift_press(self.e), "break")
        self.assertEqual(self.t.sel, ["1.0", "1.9"])


class TestBindings(unittest.TestCase):
    def test_expected_sequences_bound(self):
        t = FakeText("x")
        StableSelection(t)
        self.assertEqual(
            sorted(seq for seq, _ in t.events),
            sorted([
                "<Button-1>", "<B1-Motion>", "<ButtonRelease-1>",
                "<Double-Button-1>", "<Triple-Button-1>",
                "<Shift-Button-1>", "<Shift-B1-Motion>",
            ]),
        )

    def test_idempotent_per_widget(self):
        t = FakeText("x")
        StableSelection(t)
        n = len(t.events)
        StableSelection(t)
        self.assertEqual(len(t.events), n)


if __name__ == "__main__":
    unittest.main()
