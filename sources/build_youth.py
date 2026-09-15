#!/usr/bin/env python3
"""Youth: verified fragments from Masson/Schütz, Napoléon manuscrits inédits (1908, PD)."""
import json, sys
sys.path.insert(0, "sources")
from common import push

NAP = {"author": "Napoleon Bonaparte", "handle": "@bonaparte", "accountType": "person"}
ARCH = "Masson & Schütz, Napoléon manuscrits inédits 1786–1791 (Paris, 1908) — public domain (French)"
URL = "https://archive.org/details/napolonmanuscr00napo"
TR = " Translated for Chronicle from the public-domain French; original below."

out = []
push(out, NAP, "Corsica", "1791-01-23", None, "Ajaccio",
     "“From Bonifacio to Cape Corse, from Ajaccio to Bastia, nothing rises but a chorus of curses against you. Your friends hide, your kin disown you. […]”",
     "Letter to Matteo Buttafoco, deputy of Corsica, January 1791", ARCH, URL,
     "letter",
     "The 21-year-old denounces Corsica's deputy: treason itemized in letters of blood. Dated January 1791 in the edition." + TR,
     "youth-corsica", cert="approximate")
out[-1]["originalText"] = "Depuis Bonifacio au cap Corse, depuis Ajaccio à Bastia, ce n'est qu'un chorus d'imprécations contre vous. Vos amis se cachent, vos parents vous désavouent."
out[-1]["originalLanguage"] = "French"

push(out, NAP, "Paris (manuscripts)", "1788-01-01", None, "Paris",
     "“Unjust men! I meant to work for a nation's happiness. A moment I succeeded, and you admired me. Fortune turned. I am in a dungeon, and you despise me. […]”",
     "Imagined dialogue: Théodore Neuhoff in debtors' prison, c.1787–88", ARCH, URL,
     "literary fragment",
     "Undated fragment placed by editors between November 1787 and October 1788: the boy lends voice to Corsica's failed king — the editors link it to St Helena." + TR,
     "youth-corsica", cert="approximate")
out[-1]["originalText"] = "Hommes injustes! J'ai voulu contribuer au bonheur d'une nation. J'y ai réussi un moment et vous m'admiriez. Le sort a changé. Je suis dans un cachot et vous me méprisez."
out[-1]["originalLanguage"] = "French"

json.dump(out, open("data/nap_youth.json", "w"), ensure_ascii=False, indent=1)
print("youth:", len(out))
