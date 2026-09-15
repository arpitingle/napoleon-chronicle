#!/usr/bin/env python3
p = "sources/build_empire.py"
s = open(p).read()
mapping = [
    ("Entering Milan", "milan"),
    ("Entering Brescia", "brescia"),
    ("Siege of Mantua", "mantua"),
    ("Cisalpine Republic", "cisalpine"),
    ("Embarking for Egypt", "egypt-embark"),
    ("Egyptians", "egyptians"),
    ("Government of Egypt", "egypt-govt"),
    ("Tippoo", "tippoo"),
    ("Abandoning", "acre-abandon"),
    ("Departure for France", "departure-fr"),
    ("Army of the East", "army-east"),
    ("Colors", "colors"),
    ("King of England", "england-king"),
    ("Jerome Bonaparte", "jerome"),
    ("Third Coalition", "third-coalition"),
    ("Fall of Ulm", "ulm"),
    ("Peace with Austria", "pressburg"),
    ("February, 1806", "feb1806"),
    ("Captive Officers", "captive"),
    ("Entering Warsaw", "warsaw"),
    ("Prussia", "prussia-eylau"),
    ("Friedland", "friedland"),
    ("Champagny", "champagny07"),
    ("Spaniards", "spaniards"),
    ("Austria, October", "austria08"),
    ("Spanish People", "spanish-people"),
    ("Morla", "morla"),
    ("Eckmuhl", "eckmuhl"),
    ("Ratisbon", "ratisbon"),
    ("Entering Vienna", "vienna09"),
    ("Hungarians", "hungarians"),
]
miss = []
for old, new in mapping:
    a = '("' + old + '",'
    if a not in s:
        miss.append(old)
    else:
        s = s.replace(a, '("' + new + '",')
print("missing:", miss)
open(p, "w").write(s)
print("done")
