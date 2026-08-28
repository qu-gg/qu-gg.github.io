"""Build the public, name-only dataset for the BREAK!! character roller.

The source transcriptions contain licensed rules text. This script deliberately
exports only names, roll ranges, summary values, and printed page references.
"""

from __future__ import annotations

import json
import re
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(__file__).with_name("data.json")


CALLINGS = [
    {
        "range": [1, 3],
        "name": "Factotum",
        "page": 16,
        "aptitudes": {"might": 7, "deftness": 9, "grit": 8, "insight": 9, "aura": 9},
        "attack": 0,
        "hearts": 2,
        "defense": 10,
        "speed": "Average",
        "gearAllowance": {"weapons": ["Standard", "Concealed", "Quick", "Lash", "Thrown", "Drawn", "Small Mechanical", "Large Mechanical"], "armor": ["Light"], "shields": ["Small"]},
        "gearAllowancePage": 20,
    },
    {
        "range": [4, 6],
        "name": "Sneak",
        "page": 22,
        "aptitudes": {"might": 7, "deftness": 10, "grit": 7, "insight": 10, "aura": 8},
        "attack": 0,
        "hearts": 2,
        "defense": 10,
        "speed": "Average",
        "gearAllowance": {"weapons": ["Standard", "Concealed", "Quick", "Thrown", "Drawn", "Small Mechanical", "Large Mechanical"], "armor": ["Light"], "shields": []},
        "gearAllowancePage": 26,
    },
    {
        "range": [7, 9],
        "name": "Champion",
        "page": 28,
        "aptitudes": {"might": 10, "deftness": 8, "grit": 9, "insight": 7, "aura": 8},
        "attack": 1,
        "hearts": 3,
        "defense": 10,
        "speed": "Average",
        "gearAllowance": {"weapons": ["Standard", "Concealed", "Quick", "Master", "Mighty", "Arc", "Lash", "Combination", "Thrown", "Drawn", "Small Mechanical", "Large Mechanical"], "armor": ["Light", "Medium", "Heavy", "Superheavy"], "shields": ["Small", "Standard", "Large"]},
        "gearAllowancePage": 32,
    },
    {
        "range": [10, 12],
        "name": "Raider",
        "page": 34,
        "aptitudes": {"might": 9, "deftness": 9, "grit": 9, "insight": 8, "aura": 7},
        "attack": 1,
        "hearts": 3,
        "defense": 10,
        "speed": "Fast",
        "gearAllowance": {"weapons": ["Standard", "Concealed", "Quick", "Master", "Mighty", "Arc", "Lash", "Combination", "Thrown", "Drawn", "Small Mechanical", "Large Mechanical"], "armor": ["Light", "Medium"], "shields": ["Small", "Standard"]},
        "gearAllowancePage": 38,
    },
    {
        "range": [13, 14],
        "name": "Battle Princess",
        "page": 40,
        "aptitudes": {"might": 8, "deftness": 8, "grit": 9, "insight": 7, "aura": 10},
        "attack": 1,
        "hearts": 3,
        "defense": 10,
        "speed": "Average",
        "gearAllowance": {"weapons": ["Standard", "Thrown"], "armor": ["Light", "Medium", "Heavy", "Superheavy"], "shields": ["Small", "Standard", "Large"]},
        "gearAllowancePage": 48,
    },
    {
        "range": [15, 16],
        "name": "Murder Princess",
        "page": 50,
        "aptitudes": {"might": 8, "deftness": 7, "grit": 10, "insight": 8, "aura": 9},
        "attack": 1,
        "hearts": 3,
        "defense": 10,
        "speed": "Average",
        "gearAllowance": {"weapons": ["Standard", "Thrown"], "armor": ["Light", "Medium", "Heavy", "Superheavy"], "shields": ["Small", "Standard", "Large"]},
        "gearAllowancePage": 56,
    },
    {
        "range": [17, 18],
        "name": "Sage",
        "page": 58,
        "aptitudes": {"might": 6, "deftness": 8, "grit": 8, "insight": 10, "aura": 8},
        "attack": 0,
        "hearts": 2,
        "defense": 10,
        "speed": "Average",
        "gearAllowance": {"weapons": ["Standard", "Concealed", "Thrown", "Small Mechanical"], "armor": ["Light"], "shields": []},
        "gearAllowancePage": 66,
    },
    {
        "range": [19, 20],
        "name": "Heretic",
        "page": 68,
        "aptitudes": {"might": 7, "deftness": 7, "grit": 10, "insight": 7, "aura": 9},
        "attack": 0,
        "hearts": 2,
        "defense": 10,
        "speed": "Average",
        "gearAllowance": {"weapons": ["Standard", "Lash", "Thrown"], "armor": ["Light"], "shields": []},
        "gearAllowancePage": 78,
    },
]


SPECIES = [
    {"range": [1, 4], "name": "Human, Native", "page": 84, "size": "Medium", "quirkTable": "Inheritor", "nameTable": "Native Human"},
    {"range": [5, 5], "name": "Human, Dimensional Stray", "page": 86, "size": "Medium", "quirkTable": "Inheritor", "nameTable": "Native Human"},
    {"range": [6, 7], "name": "Chib", "page": 88, "size": "Small", "quirkTable": "Inheritor", "nameTable": "Chib"},
    {"range": [8, 10], "name": "Tenebrate", "page": 90, "size": "Medium", "quirkTable": "Inheritor", "nameTable": "Tenebrate"},
    {"range": [11, 13], "name": "Rai-Neko", "page": 92, "size": "Medium", "quirkTable": "Inheritor", "nameTable": "Rai-Neko"},
    {"range": [14, 15], "name": "Promethean", "page": 94, "size": "Large", "quirkTable": "Inheritor", "nameTable": "Promethean"},
    {"range": [16, 16], "name": "Gruun", "page": 96, "size": "Large", "quirkTable": "Inheritor", "nameTable": "Gruun"},
    {"range": [17, 17], "name": "Goblin", "page": 98, "size": "Small", "quirkTable": "Old World", "nameTable": "Goblin"},
    {"range": [18, 18], "name": "Dwarf", "page": 100, "size": "Medium", "quirkTable": "Old World", "nameTable": "Dwarf", "inventoryBonus": 2},
    {"range": [19, 19], "name": "Elf", "page": 102, "size": "Medium", "quirkTable": "Old World", "nameTable": "Elf"},
    {"range": [20, 20], "name": "Bio-Mechanoid", "page": 104, "size": "Medium", "quirkTable": "Bio-Mechanoid", "nameTable": "Bio-Mechanoid"},
]


HOMELANDS = [
    {"range": [1, 5], "name": "Wistful Dark", "page": 110, "languages": ["High Akenian", "Dark Tongue", "Dream Call"]},
    {"range": [6, 10], "name": "Twilight Meridian", "page": 114, "languages": ["Dark Tongue", "Fade Song", "Gleysian Code"]},
    {"range": [11, 15], "name": "Blazing Garden", "page": 118, "languages": ["Bright Speech", "Hoshi-Ban", "Fade Song"]},
    {"range": [16, 20], "name": "Buried Kingdom", "page": 122, "languages": ["High Akenian", "Under Warble", "Creator's Script"]},
]


QUIRK_CATEGORY_TABLES = {
    "Inheritor": [
        {"range": [1, 7], "name": "Spirit"},
        {"range": [8, 14], "name": "Physiology"},
        {"range": [15, 20], "name": "Fate"},
    ],
    "Old World": [
        {"range": [1, 7], "name": "Spirit"},
        {"range": [8, 14], "name": "Physiology"},
        {"range": [15, 20], "name": "Eldritch"},
    ],
    "Bio-Mechanoid": [
        {"range": [1, 10], "name": "Spirit"},
        {"range": [11, 20], "name": "Robotic"},
    ],
}


SIZE_RULES = {
    "Small": {
        "page": 106,
        "aptitudes": {"might": -1, "deftness": 1},
        "defense": 1,
        "inventory": 8,
        "restricted": {"weapons": ["Mighty", "Arc"], "armor": ["Heavy", "Superheavy"], "shields": ["Large"]},
    },
    "Medium": {"page": 106, "aptitudes": {}, "defense": 0, "inventory": 10, "restricted": {"weapons": [], "armor": [], "shields": []}},
    "Large": {
        "page": 106,
        "aptitudes": {"might": 1},
        "defense": -1,
        "inventory": 12,
        "restricted": {"weapons": ["Concealed", "Small Mechanical"], "armor": [], "shields": []},
    },
}


ARMOR_DEFENSE = {"Light": 2, "Medium": 4, "Heavy": 6, "Superheavy": 8}
SHIELD_DEFENSE = {"Small": 0, "Standard": 1, "Large": 2}


QUIRK_ADJUSTMENTS = {
    "Unhinged": {"attack": 2, "defense": -1},
    "Girthsome": {"aptitudes": {"grit": 1}, "hearts": 1, "speed": -1},
    "Nearsighted": {"aptitudes": {"insight": 1}, "extraLanguages": 2},
    "Waifish": {"aptitudes": {"deftness": 1}, "hearts": -1, "speed": 1},
    "Winged": {"aptitudes": {"grit": -1}, "hearts": -1},
    "Past Injury": {"defense": 1, "randomAptitudePenalty": -1},
    "Weary": {"aptitudes": {"might": -1, "grit": -1}},
    "Fairy Cap": {"defense": 1},
    "Ferrous": {"defenseSet": 14},
    "Industrial Frame": {"aptitudes": {"might": 1}, "hearts": 1, "speed": -1},
}


WEAPON_TYPES = ["Standard", "Concealed", "Quick", "Master", "Mighty", "Arc", "Lash", "Thrown", "Drawn", "Small Mechanical", "Large Mechanical"]
BLADE_WEAPON_TYPES = ["Quick", "Master", "Mighty", "Arc", "Lash", "Drawn", "Mechanical Missile"]
AILMENTS = ["Ballooned", "Blinded/Deafened", "Chibbed", "Disoriented", "Dispirited", "Fatigued", "Jellyfied", "Petrified", "Putrefied", "Restrained", "Starved", "Suffocated", "Terrified", "Toppled"]
SPECIALIST_KITS = ["Dungeoneer's Kit", "Gadgeteer's Kit", "Physician's Kit", "Survivalist's Kit", "Thief's Kit"]


NAME_TABLES = {
    "Native Human": ["Jahgi Tailor", "Velna Gleamblade", "Zoppo Flyfisher", "Nishe Smallhat", "Grinbu Runner", "Deldi Bluerod", "Olza Flowerpicker", "Rumi Treasurebox", "Bullza Taster", "Fisho Oldkey"],
    "Chib": ["Handy Mann", "Falin Down", "Nebb Ish", "Bilk Tinny", "Penny Pincher", "Leaf Acorn", "Sweetsy Shortcake", "Hammy Glaze", "Glum Plumby", "Naldo Bean"],
    "Tenebrate": ["Izaiah Prudence", "Vahln Noblesse", "Micah Gallant", "Rose Justhorn", "Galahad Crown", "Aurora Melody", "Valentine Sapphire", "Peckrah Stalwart", "Lily Gilded", "Rolm Leonhart"],
    "Rai-Neko": ["Astute Observation", "Orange Fruit", "Fine Afternoon", "Wrong Idea", "Different Angle", "Pickles Jar", "Snowy Weather", "Clubs Deck", "Goggles Gear", "Dad Joke"],
    "Promethean": ["Lotl", "Hiss", "Faang", "Pogonas", "Iguano", "Basilisk", "Krait", "Skinks", "Rattle", "Cobrash"],
    "Gruun": ["Shoog Thiill", "Treep Knuuk", "Maash Mook", "Adeed Kroop", "Bluud Greem", "Lookout Beello", "Thuud Chaam", "Phooby Sheenk", "Graash Ruud", "Fruunt Shaak"],
    "Goblin": ["Scritch", "Frag", "Plunk", "Bubble", "Thwack", "Clicky", "Snap", "Bung", "Squelch", "Thwip"],
    "Dwarf": ["Handleba Tungston", "Gabbro Grim", "Molasses Stubble", "Emeralda Golden", "Balbo Wacke", "Mildred Mudrock", "Coal Mutton", "Quartz Bedrock", "Silva Chalk", "Brass Swindle"],
    "Elf": ["Obsidian Moonsoul", "Dee'do Fii'ren", "Nanashi", "Quicksilver Ripple", "Key Fulcrum", "Altair Swiftblade", "Wanderer", "(Random name from another chart)", "PhenLeiShun", "Candace"],
    "Bio-Mechanoid": ["0-Alpha", "Solider Seven", "4man", "AK00lade", "Main 10-ance", "Second", "Gr33ter", "Variant", "Arc-5er", "Factory Setting"],
}


NAME_TABLE_CHART = [
    {"range": [1, 5], "name": "Native Human"},
    {"range": [6, 7], "name": "Chib"},
    {"range": [8, 10], "name": "Tenebrate"},
    {"range": [11, 13], "name": "Rai-Neko"},
    {"range": [14, 15], "name": "Promethean"},
    {"range": [16, 16], "name": "Gruun"},
    {"range": [17, 17], "name": "Goblin"},
    {"range": [18, 18], "name": "Dwarf"},
    {"range": [19, 19], "name": "Elf"},
    {"range": [20, 20], "name": "Bio-Mechanoid"},
]


def page_reference(text: str) -> int | None:
    match = re.search(r"\(p(\d+)(?:[^)]*)\)", text)
    return int(match.group(1)) if match else None


def public_gear_entry(text: str) -> dict:
    """Separate a generic item name from its history-specific nickname."""
    without_page = re.sub(r"\s*\(p\d+(?:[^)]*)\)\.?$", "", text).strip()
    name, separator, nickname = without_page.partition(",")
    entry = {
        "name": name.strip(),
        "nickname": nickname.strip() if separator else "",
        "page": page_reference(text),
    }
    entry.update(classify_combat_gear(entry["name"]))
    return entry


def classify_combat_gear(name: str) -> dict:
    if " Armor" in name:
        armor_type = name.split(" Armor", 1)[0]
        return {"gearCategory": "armor", "gearType": armor_type, "defenseBonus": ARMOR_DEFENSE[armor_type]}
    if " Shield" in name:
        shield_type = name.split(" Shield", 1)[0]
        return {"gearCategory": "shields", "gearType": shield_type, "defenseBonus": SHIELD_DEFENSE[shield_type]}
    if "Weapon" in name:
        weapon_prefixes = [
            ("Small Mechanical", "Small Mechanical"),
            ("Large Mechanical", "Large Mechanical"),
            ("Thrown", "Thrown"),
            ("Drawn", "Drawn"),
            ("Concealed", "Concealed"),
            ("Standard", "Standard"),
            ("Quick", "Quick"),
            ("Master", "Master"),
            ("Mighty", "Mighty"),
            ("Arc", "Arc"),
            ("Lash", "Lash"),
        ]
        for prefix, weapon_type in weapon_prefixes:
            if name.startswith(prefix):
                return {"gearCategory": "weapons", "gearType": weapon_type}
        raise ValueError(f"Unrecognized weapon type: {name}")
    return {}


def build_calling_abilities() -> dict[str, dict]:
    module = runpy.run_path(ROOT / "questline-vtt-tools" / "build_calling_abilities.py")
    result = {}
    for calling in module["CALLINGS"]:
        result[calling.name] = {
            "starting": [{"name": ability.name, "pages": list(calling.pages)} for ability in calling.abilities if ability.tier == "Starting"],
            "standard": [{"name": ability.name, "pages": list(calling.pages)} for ability in calling.abilities if ability.tier == "Standard"],
        }
    species_result = {}
    species_aliases = {
        "Human (Native)": "Human, Native",
        "Human (Dimensional Stray)": "Human, Dimensional Stray",
    }
    for species in module["SPECIES"]:
        public_name = species_aliases.get(species.name, species.name)
        if public_name in {entry["name"] for entry in SPECIES}:
            species_result[public_name] = [
                {"name": ability.name, "pages": list(species.pages)}
                for ability in species.abilities
                if ability.tier == "Starting"
            ]
    return {"callings": result, "species": species_result}


def history_ranges(count: int) -> list[list[int]]:
    if count == 10:
        return [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12], [13, 14], [15, 16], [17, 19], [20, 20]]
    return [[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12], [13, 14], [15, 16], [17, 17], [18, 18], [19, 19], [20, 20]]


def build_histories() -> dict[str, list[dict]]:
    module = runpy.run_path(ROOT / "questline-vtt-tools" / "build_histories.py")
    homelands = module["HOMELANDS"]
    result = {}
    for homeland in homelands:
        ranges = history_ranges(len(homeland.histories))
        result[homeland.subtype] = [
            {
                "range": ranges[index],
                "name": history.name,
                "tier": history.tier,
                "page": 110 + ["Wistful Dark", "Twilight Meridian", "Blazing Garden", "Buried Kingdom", "Other World"].index(homeland.subtype) * 4 + index // 3,
                "gear": [
                    {"option": gear_index + 1, **public_gear_entry(item)}
                    for gear_index, item in enumerate(history.gear)
                ],
            }
            for index, history in enumerate(homeland.histories)
        ]
    return result


def build_quirks() -> dict[str, list[dict]]:
    module = runpy.run_path(ROOT / "questline-vtt-tools" / "build_quirks.py")
    result = {}
    for group in module["GROUPS"]:
        result[group.subtype] = [
            {"range": [index * 2 + 1, index * 2 + 2], "name": quirk.name, "pages": list(group.page_range)}
            for index, quirk in enumerate(group.quirks)
        ]
    return result


def main() -> None:
    abilities = build_calling_abilities()
    payload = {
        "schemaVersion": 1,
        "source": "BREAK!! RPG Core Rules v1",
        "callings": CALLINGS,
        "species": SPECIES,
        "homelands": HOMELANDS,
        "histories": build_histories(),
        "quirkCategoryTables": QUIRK_CATEGORY_TABLES,
        "quirks": build_quirks(),
        "nameSource": "https://breakrpg.blogspot.com/2025/04/random-name-tables-setting-freebie.html",
        "nameTableChart": NAME_TABLE_CHART,
        "nameTables": {
            table_name: [
                {"range": [index * 2 + 1, index * 2 + 2], "name": name}
                for index, name in enumerate(names)
            ]
            for table_name, names in NAME_TABLES.items()
        },
        "callingAbilities": abilities["callings"],
        "speciesAbilities": abilities["species"],
        "sizeRules": SIZE_RULES,
        "quirkAdjustments": QUIRK_ADJUSTMENTS,
        "choices": {
            "weaponTypes": WEAPON_TYPES,
            "bladeWeaponTypes": BLADE_WEAPON_TYPES,
            "brightBladeMaterials": ["Sun Gold", "Ash Bronze", "Sky Steel"],
            "darkBladeMaterials": ["Shade Iron", "Dew Silver", "Warp Root"],
            "darkGifts": ["Horns", "Opaque Eyes", "Devil's Tail", "Fangs", "Melodious Voice", "Winter's Embrace", "Bone Spikes", "Bestial Mane", "Raptor's Talons", "Shadow Mark"],
            "ailments": AILMENTS,
            "specialistKits": SPECIALIST_KITS,
            "craftingDisciplines": ["Forging", "Gadgeteering", "Tailoring", "Artificing", "Alchemy", "Cooking"],
            "petNames": ["Growl", "Buzzer", "Pudge Grub", "Fuzzcoil", "Skree", "Purr"],
            "bioskinSpecies": ["Human", "Tenebrate", "Elf"],
            "companionTypes": ["Guardian Animal", "Brave Toy"],
            "animalCompanionAbilities": ["Mount", "Burrower", "Fighter", "Glider"],
            "toyCompanionAbilities": ["Shielder", "Weapon Link", "Booster", "Toter"],
            "aptitudes": ["might", "deftness", "grit", "insight", "aura"],
        },
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()