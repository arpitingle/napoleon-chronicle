#!/usr/bin/env python3
"""Closer 1821: testament, codicil, death message — verified in Antommarchi (1825, PD)."""
import json, sys
sys.path.insert(0, "sources")
from common import push

NAP = {"author": "Napoleon Bonaparte", "handle": "@bonaparte", "accountType": "person"}
ARCH = "Antommarchi, Derniers momens de Napoléon (Paris, 1825) — public domain (French)"
URL = "https://archive.org/details/derniersmomensd02antogoog"
TR = " Translated for Chronicle from the public-domain French; original below."

out = []
push(out, NAP, "St Helena", "1821-04-15", None, "Longwood",
     "“I die prematurely, assassinated by the English oligarchy and its hired killer; the English people will soon avenge me. […]”",
     "Testament, article 5, April 1821", ARCH, URL, "testament",
     "Dictated in his final month; widely printed within months. Day approximate." + TR,
     "sthelena-1815", cert="approximate")
out[-1]["originalText"] = "Je meurs prématurément, assassiné par l'oligarchie anglaise et son sicaire; le peuple anglais ne tardera pas à me venger."
out[-1]["originalLanguage"] = "French"

push(out, NAP, "St Helena", "1821-04-15", None, "Longwood",
     "“I desire my ashes to rest on the banks of the Seine, amid the French people I loved so well. […]”",
     "Codicil on burial, April 1821", ARCH, URL, "testament",
     "Holograph codicil, sealed with his arms; the governor refused it. Day approximate." + TR,
     "sthelena-1815", cert="approximate")
out[-1]["originalText"] = "Je désire que mes cendres reposent sur les bords de la Seine, au milieu de ce peuple français que j'ai tant aimé."
out[-1]["originalLanguage"] = "French"

push(out, NAP, "St Helena", "1821-05-01", None, "Longwood",
     "“Tell them the great Napoleon expired in the most deplorable state, wanting everything, abandoned to himself and his glory. […]”",
     "Dictated farewell message, final days", ARCH, URL, "reported speech",
     "Dictated to Antommarchi in his last days; reported speech via the doctor's journal." + TR,
     "sthelena-1815", cert="approximate")
out[-1]["originalText"] = "Vous leur direz que le grand Napoléon est expiré dans l'état le plus déplorable, manquant de tout, abandonné à lui-même et à sa gloire."
out[-1]["originalLanguage"] = "French"

json.dump(out, open("data/nap_closer.json", "w"), ensure_ascii=False, indent=1)
print("closer:", len(out))
