#!/usr/bin/env python3
"""1794-1795 French batch + own translations."""
import json, sys
sys.path.insert(0, "sources")
from common import push

NAP = {"author": "Napoleon Bonaparte", "handle": "@bonaparte", "accountType": "person"}
ARCH = "Correspondance de Napoléon Ier, Second Empire ed. (Paris, 1858), Vol. I — public domain (French)"
URL = "https://archive.org/details/correspondancede01napouoft"
TR = " Translated for Chronicle from the public-domain French; original below."

REC = [
 ("1794-01-04", "Marseille", "To the War Minister", "toulon-1793",
  "Saint-Nicolas untenable: three enceintes razed, open on all sides.",
  "Le fort Saint-Nicolas n'est pas susceptible d'un quart d'heure de défense. Les trois enceintes qui fermaient le fort du côté de la ville ont été démolies.",
  "Fort Saint-Nicolas cannot withstand a quarter-hour. The three walls closing it town-side are razed."),
 ("1794-04-07", "Nice", "Coast battery order", "toulon-1793",
  "Sainte-Marguerite battery rebuilt, mortars raised eight feet.",
  "Il faut rétablir la batterie de la pointe de l'île Sainte-Marguerite; il faut élever de huit pieds l'épaulement des mortiers.",
  "Rebuild Sainte-Marguerite point battery; raise the mortar parapet eight feet."),
 ("1794-05-21", "Nice", "Plan for Piedmont", "toulon-1793",
  "No Piedmont plain without superior force: join Alps and Italy armies.",
  "L'on ne peut se présenter dans la plaine de Piémont qu'avec des forces supérieures à son ennemi; pour obtenir cette supériorité il faut réunir l'armée des Alpes et celle d'Italie.",
  "Piedmont's plain demands superior force; join the Alps and Italy armies for it."),
 ("1794-06-20", "Nice", "Plan, continued", "toulon-1793",
  "Secure rearwards first, unite Alps-Italy defence.",
  "1° Assurer ses derrières, soit contre les ennemis internes, soit contre les ennemis externes. 2° Réunir le système de défense des armées des Alpes et d'Italie.",
  "1. Secure rearwards against enemies within and without. 2. Unite the Alps and Italy defence systems."),
 ("1794-06-27", "Nice", "To Berlier (islands)", "toulon-1793",
  "Marguerite not Pelletier: island names need a Convention decree.",
  "Tu ne dois pas appeler l'île Sainte-Marguerite l'île Pelletier. Il faut un décret de la Convention pour pouvoir changer le nom des places.",
  "Call it not Pelletier but Marguerite island; renaming places needs a Convention decree."),
 ("1794-07-02", "Nice", "To Berlier (alarmistes)", "toulon-1793",
  "Two alarmist breeds: grain-famine criers and powder-fearers.",
  "Il y a dans la République deux espèces d'alarmistes, ceux qui crient famine de grain et ceux qui ont toujours peur de rester sans poudre.",
  "The Republic breeds two alarmists: grain-famine criers and powder-fearers."),
 ("1794-07-02", "Nice", "To Berlier (powder)", "toulon-1793",
  "Powder imposture: 45 not 28 thousand at Antibes.",
  "C'est une imposture de dire que tu n'as que 28 milliers de poudre à Antibes, lorsque tu en as 45 milliers.",
  "It is imposture to claim 28 thousand powder at Antibes when you hold 45."),
 ("1794-09-15", "Nice", "To Multedo", "toulon-1793",
  "Unanswered letters, but no contempt: the Corsican affair.",
  "Je t'ai écrit plusieurs fois, mais tu ne m'as pas répondu; je ne puis penser que ce soit par mépris.",
  "I wrote you several times unanswered; I cannot think it contempt."),
 ("1795-06-18", "Paris", "To an unknown protectress (Saliceti)", "youth-1795",
  "Saliceti hides at her house, twenty days known.",
  "Je n'ai jamais voulu être pris pour dupe; je sais, depuis plus de vingt jours, que Saliceti est caché chez vous.",
  "Never take me for a dupe; these twenty days I know Saliceti hides with you."),
 ("1795-06-22", "Paris", "To Joseph", "youth-1795",
  "Chiappe pleases; Lucien to be placed; letter No. 16 received.",
  "J'ai reçu ta lettre numérotée 16. La lettre de Chiappe m'a fait plaisir. Je ferai ce que je pourrai pour placer Lucien.",
  "Your No. 16 received. Chiappe's letter pleased me. I shall do what I can for Lucien."),
 ("1795-07-12", "Paris", "To Joseph", "youth-1795",
  "English re-embarking soon; Pichegru prepares the Rhine; Vendée quiet.",
  "Les Anglais seront obligés de s'embarquer sous peu de jours. Pichegru prépare le passage du Rhin. La Vendée proprement dite est tranquille.",
  "The English must re-embark within days. Pichegru prepares the Rhine crossing. The Vendée proper is quiet."),
 ("1795-07-24", "Paris", "To a war commissary", "youth-1795",
  "No pleasant news: unfrocked war commissary, departure pending.",
  "Je ne vous ai pas écrit, mon ami, parce que je n'avais aucune nouvelle agréable à vous donner.",
  "I did not write, friend, for I had no pleasant news to give."),
 ("1795-07-28", "Paris", "Quiberon note", "youth-1795",
  "Twelve thousand émigrés landed; English ships hold the isthmus.",
  "Les émigrés, au nombre de douze mille, étant débarqués dans la presqu'île de Quiberon, avaient établi des batteries pour défendre le passage de l'isthme.",
  "Twelve thousand émigrés landed at Quiberon, battering the isthmus passage."),
 ("1795-08-23", "Paris", "To Kellermann", "youth-1795",
  "Italy instructions via last courier: reinforcements coming.",
  "Le Comité de salut public vous a fait passer, Général, par le dernier courrier, des instructions relatives à la direction de l'armée d'Italie.",
  "The Committee sent you, General, by last courier, Italy's direction instructions."),
 ("1795-08-30", "Paris", "Committee to Italy (incoming)", "youth-1795",
  "Incoming voice: Swiss note examined; enemy conforms to true interest.",
  "Nous vous faisons passer, Général, une note qui nous a été envoyée de Suisse.",
  "We forward, General, a note just received from Switzerland."),
 ("1795-09-05", "Paris", "Note", "youth-1795",
  "Cannot leave France while war lasts; artillery restoration likely.",
  "Le Comité a pensé qu'il était impossible que je sortisse de France tant que durera la guerre.",
  "The Committee thinks I cannot leave France while war lasts."),
 ("1795-09-08", "Paris", "To Joseph", "youth-1795",
  "Wrote yesterday to 'la femme'; primaries meet in three days.",
  "J'ai écrit hier à la femme, mon ami; elle aura reçu ma lettre. Les assemblées primaires seront réunies dans trois jours.",
  "Yesterday I wrote her, friend; she will have it. Primary assemblies meet in three days."),
 ("1795-09-12", "Paris", "To Joseph", "youth-1795",
  "Writing daily against Genoa rumors; Constitution accepted everywhere.",
  "Comme je pense que l'on ne manque pas de faire courir à Gênes des bruits faux, je t'écris tous les jours.",
  "Lest false rumors run at Genoa, I write you daily."),
 ("1795-09-15", "Paris", "Note", "youth-1795",
  "Majority accepted Constitution and renewal; sections still ferment.",
  "La majorité de la République a déjà accepté la Constitution et le décret sur le renouvellement. Des sections de Paris continuent à être en fermentation.",
  "The majority accepted Constitution and renewal; Paris sections still ferment."),
 ("1795-10-11", "Paris", "Note", "youth-1795",
  "Gazettes told all: second of the interior army, Barras commanding; we conquered.",
  "Tu auras appris par les feuilles publiques tout ce qui me concerne. J'ai été nommé général en second de l'armée de l'intérieur. Nous avons vaincu.",
  "The gazettes told you all: named second of the interior army. We conquered."),
]

out = []
for iso, loc, toline, eid, ctx, fr, en in REC:
    push(out, NAP, "Army of Italy" if iso < "1795" else "Paris", iso, None, loc, "“" + en + " […]”",
         f"{toline}, {iso}", ARCH, URL,
         "letter", ctx + TR, eid)
    out[-1]["originalText"] = fr
    out[-1]["originalLanguage"] = "French"

json.dump(out, open("data/nap_1794.json", "w"), ensure_ascii=False, indent=1)
print("1794-95:", len(out))
