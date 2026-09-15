#!/usr/bin/env python3
"""French bulk part 2: 1797-12 + 1798-01 (vol 3), short verbatim excerpts + own translations."""
import json, sys
sys.path.insert(0, "sources")
from common import push

NAP = {"author": "Napoleon Bonaparte", "handle": "@bonaparte", "accountType": "person"}
DIRN = {"author": "The Executive Directory", "handle": "@directoire", "accountType": "institution"}
ARCH = "Correspondance de Napoléon Ier, Second Empire ed. (Paris, 1858) — public domain (French)"
TR = " Translated for Chronicle from the public-domain French; original below."
U3 = "https://archive.org/details/correspondancede03napouoft"

REC = [
 ("1797-12-10", "Paris", "Allocution au Directoire", NAP, "campo-1797",
  "Return presentation, Campo Formio in his pocket.",
  "Le peuple français, pour être libre, avait les rois à combattre.",
  "To be free, the French people had kings to fight."),
 ("1797-12-12", "Paris", "Instructions du Directoire (incoming)", DIRN, "campo-1797",
  "Incoming voice: secret convention with the Emperor, execute in Italy.",
  "Vous trouverez ci-joint, Citoyen Général, une copie de la convention secrète conclue entre la République française et l'Empereur.",
  "Enclosed, Citizen General, a copy of the secret convention between the French Republic and the Emperor."),
 ("1797-12-13", "Paris", "To Bernardin de Saint-Pierre", NAP, "campo-1797",
  "Napoleon the reader: your pen is a paintbrush.",
  "Je reçois à l'instant un exemplaire de vos ouvrages. Votre plume est un pinceau.",
  "I have just received your works. Your pen is a paintbrush."),
 ("1797-12-26", "Paris", "To the Institut president", NAP, "campo-1797",
  "Elected to the Institut: long their schoolboy first.",
  "Le suffrage des hommes distingués qui composent l'Institut m'honore. Je sens bien qu'avant d'être leur égal je serai longtemps leur écolier.",
  "The votes of the distinguished men of the Institut honor me. Before being their equal I shall long be their schoolboy."),
 ("1798-01-06", "Paris", "To the Directory", NAP, "egypt-1798",
  "Maniot deputies: Greece watched from Paris.",
  "Il y a plusieurs mois que j'envoyai chez les Maniotes deux députés.",
  "Months ago I sent two deputies to the Maniots."),
 ("1798-01-11", "Paris", "Directory instructions (incoming)", DIRN, "egypt-1798",
  "Incoming voice: Duphot's murderers shall not go unpunished; Rome next.",
  "Le Directoire exécutif n'a vu qu'avec la plus vive indignation la conduite de la cour de Rome.",
  "The Executive Directory sees with liveliest indignation Rome's conduct."),
 ("1798-01-11", "Paris", "To Berthier, midnight", NAP, "egypt-1798",
  "Midnight: the honor of taking Rome is reserved to you.",
  "J'ai reçu, mon cher Général, les lettres que vous m'avez écrites. L'honneur de prendre Rome vous est réservé.",
  "I received, my dear General, the letters you wrote me. The honor of taking Rome is reserved to you."),
 ("1798-01-14", "Paris", "To the Foreign Minister", NAP, "egypt-1798",
  "Cisalpine notes: Mantua, Ferrara to be named.",
  "Vous trouverez ci-joint, Citoyen Ministre, les notes que vous m'avez demandées.",
  "Enclosed, Citizen Minister, the notes you asked of me."),
 ("1798-01-16", "Paris", "To the Directory", NAP, "egypt-1798",
  "Ali Pasha offered French mediation via Ionian agents.",
  "Par les dernières lettres du Levant, nos commissaires ont offert la médiation de la République française à Ali, pacha de Janina.",
  "By the latest Levant letters, our commissioners offered French mediation to Ali, pasha of Janina."),
 ("1798-01-24", "Paris", "To Berthier", NAP, "egypt-1798",
  "Hurry to Rome; Mainz army shown off to overawe the Emperor.",
  "J'ai reçu votre lettre qui m'annonce votre départ pour Rome. Il faut arriver le plus vite que vous pourrez.",
  "I received your letter announcing your departure for Rome. Arrive as fast as you can."),
]

out = []
for iso, loc, toline, who, eid, ctx, fr, en in REC:
    push(out, who, "Army of Italy", iso, None, loc, "“" + en + " […]”",
         f"{toline}, {iso}", ARCH, U3,
         "letter" if "Allocution" not in toline else "allocution",
         ctx + TR, eid)
    out[-1]["originalText"] = fr
    out[-1]["originalLanguage"] = "French"

json.dump(out, open("data/nap_france2.json", "w"), ensure_ascii=False, indent=1)
print("france2:", len(out))
