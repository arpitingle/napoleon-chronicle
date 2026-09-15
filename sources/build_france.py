#!/usr/bin/env python3
"""French batch: PD Second Empire Correspondance + Chronicle's own English
translations (marked TRANSLATION, translator noted in context)."""
import json, sys
sys.path.insert(0, "sources")
from common import push

C = {r["iso"]: r for r in json.load(open("sources/corr_vol1.json"))}
out = []
NAP = {"author": "Napoleon Bonaparte", "handle": "@bonaparte", "accountType": "person"}
ARCH = "Correspondance de Napoléon Ier, Second Empire ed. (Paris, 1858), Vol. I — public domain (French)"
URL = "https://archive.org/details/correspondancede01napouoft"
TR = " Translated for Chronicle from the public-domain French; original below."

REC = [
 ("1793-12-07", "Toulon", "To Citizen Gassendi", "toulon-1793",
  "Toulon eve: thirty thousand men, eleven batteries, and a stolen battery retaken.",
  "J'ai reçu toutes les différentes lettres que vous m'avez écrites. Ici nous sommes toujours à peu près dans la même position. L'armée est forte de trente mille hommes. Nous avons onze batteries contre le fort de Malbousquet.",
  "I have received all the various letters you wrote me. Here we are still much in the same position. The army is thirty thousand strong. We have eleven batteries against Fort Malbousquet."),
 ("1793-12-24", "Toulon", "To Citizen Dupin", "toulon-1793",
  "Toulon retaken: 'I promised you brilliant successes, and you see I keep my word.'",
  "Je t'avais annoncé de brillants succès, et tu vois que je te tiens parole. Excédé de fatigue et d'occupation, je n'ai pas pu t'en instruire le premier; il me suffira de te dire que les Anglais n'ont enlevé aucune de nos pièces.",
  "I promised you brilliant successes, and you see I keep my word. Worn out with fatigue and work, I could not tell you first; suffice it that the English carried off none of our guns."),
 ("1794-02-28", "Héraclée", "To the Committee of Public Safety", "toulon-1793",
  "Coast guns: grain ships, English squadrons, and two new batteries.",
  "Il est encore arrivé ce soir des bâtiments chargés de blé dans cette rade; mais l'escadre ennemie les empêche de se hasarder à passer. Je vais faire établir deux batteries, qui, dès qu'elles seront achevées, rendront le cabotage de la côte sûr, à la vue même de l'escadre ennemie.",
  "More grain ships came into the roads this evening; but the enemy squadron keeps them from venturing through. I shall have two batteries built which, once finished, will make coastal traffic safe, under the very eyes of the enemy squadron."),
 ("1795-08-25", "Paris", "To Joseph Buonaparte", "youth-1795",
  "Bureaucrat in Paris: Naples consulships hoped, Convention thirds renewed.",
  "J'espère que tu auras un consulat dans le royaume de Naples, à la paix avec cette puissance. L'on est ici fort tranquille. L'on va renouveler le tiers de la Convention.",
  "I hope you will have a consulate in the kingdom of Naples, at peace with that power. All is very quiet here. A third of the Convention is about to be renewed."),
 ("1795-09-23", "Paris", "To Joseph Buonaparte", "youth-1795",
  "Twelve days before Vendémiaire: 'here all is quiet... there will be no shock.' Wrong.",
  "Nous attendons la conclusion des affaires de Corse avec quelque intérêt; ici tout est tranquille. La Convention a la majorité pour les deux tiers. Avant un mois il n'y aura aucun choc; la Constitution sera établie.",
  "We await the conclusion of Corsican affairs with some interest; here all is quiet. The Convention has the majority for the two-thirds. Within a month there will be no shock; the Constitution will be established."),
 ("1795-10-12", "Paris", "Note on Italy", "youth-1795",
  "A week after Vendémiaire: the Ceva critique that won him an army.",
  "L'on a commis une faute essentielle en ne forçant pas le camp retranché de Ceva tandis que les Autrichiens battus étaient acculés au delà d'Acqui. Toute notre armée se trouvait disponible pour cette attaque.",
  "An essential error was committed in not forcing the entrenched camp of Ceva while the beaten Austrians were driven beyond Acqui. Our whole army stood available for that attack."),
 ("1796-04-26", "Cherasco", "Proclamation to the Army", "italy-1796",
  "The Cherasco proclamation, in French at last: destitute of everything, supplied everything.",
  "Dénués de tout, vous avez suppléé à tout. Vous avez gagné des batailles sans canons, passé des rivières sans ponts, fait des marches forcées sans souliers, bivouaqué sans eau-de-vie et souvent sans pain. […] Amis, je vous la promets cette conquête; mais il est une condition qu'il faut que vous juriez de remplir: respecter les peuples que vous délivrez. Sans cela, vous ne seriez pas les libérateurs des peuples, vous en seriez les fléaux.",
  "Destitute of everything, you have supplied everything. You have won battles without cannon, crossed rivers without bridges, made forced marches without shoes, bivouacked without brandy and often without bread. […] Friends, I promise you this conquest; but one condition you must swear to fulfil: respect the peoples you deliver. Else you will not be the liberators of peoples, but their scourge."),
]

for iso, loc, toline, eid, ctx, fr, en in REC:
    push(out, NAP, "Army of Italy" if iso >= "1796" else ("Paris" if iso >= "1795" else "Army of Italy (Toulon)"),
         iso, None, loc, "“" + en + " […]”", f"{toline}, {iso}", ARCH, URL,
         "letter" if "Proclamation" not in toline else "proclamation",
         ctx + TR, eid)
    out[-1]["originalText"] = fr
    out[-1]["originalLanguage"] = "French"

json.dump(out, open("data/nap_france.json", "w"), ensure_ascii=False, indent=1)
print("france:", len(out))
