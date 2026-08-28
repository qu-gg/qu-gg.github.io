"""Build the public, name-only dataset for the BREAK!! character roller.

The source transcriptions contain licensed rules text. This script deliberately
exports only names, roll ranges, summary values, and printed page references.
"""

from __future__ import annotations

import json
import re
import runpy
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(__file__).with_name("data.json")

RESKIN_SOURCE = "https://breakrpg.blogspot.com/2023/07/option-menu-re-skinning-and-modifying.html"
ALTERNATE_SOURCE = "https://breakrpg.blogspot.com/2024/05/freebie-some-more-alternate-callings.html"
EXPANDED_TABLE_SOURCE = "https://breakrpg.blogspot.com/2026/06/blog-bonus-character-creation-tables.html"
BALLADEER_SOURCE = "https://breakrpg.blogspot.com/2025/04/break-balladeer-freebie-calling.html"
HENSHIN_SOURCE = "https://breakrpg.blogspot.com/2026/06/freebie-henshin-hero-calling.html"
HOPPALONG_SOURCE = "https://breakrpg.blogspot.com/2023/08/option-menu-creating-your-own-species.html"
SURF_TURF_SOURCE = "https://breakrpg.blogspot.com/2024/09/freebie-surf-and-turf-gaddabovids-and.html"
UNTERKIN_SOURCE = "https://breakrpg.blogspot.com/2026/04/freebie-architects-of-promise-unterkin.html"


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
        "inventoryBonus": 8,
        "inventoryBonusSource": "Factotum Pack",
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
    {"range": [18, 18], "name": "Dwarf", "page": 100, "size": "Medium", "quirkTable": "Old World", "nameTable": "Dwarf", "inventoryBonus": 2, "inventoryBonusSource": "Sturdy"},
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
    "Unterkin": [
        {"range": [1, 10], "name": "Physiology"},
        {"range": [11, 20], "name": "Eldritch"},
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


def expanded_gear(name: str, nickname: str, source_url: str) -> dict:
    entry = {"name": name, "nickname": nickname, "sourceUrl": source_url}
    entry.update(classify_combat_gear(name))
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


def build_expanded_callings(ability_data: dict[str, dict]) -> list[dict]:
    core = {calling["name"]: calling for calling in CALLINGS}
    abilities = ability_data["callings"]

    def find_ability(name: str) -> dict:
        for calling in abilities.values():
            for tier in ("starting", "standard"):
                for ability in calling[tier]:
                    if ability["name"] == name:
                        return deepcopy(ability)
        raise KeyError(name)

    def blog_ability(name: str, source_url: str) -> dict:
        return {"name": name, "sourceUrl": source_url}

    variants = [
        {
            "range": [3, 3], "name": "Scribe", "base": "Factotum", "source": RESKIN_SOURCE,
            "starting": [blog_ability("Journey Journal", RESKIN_SOURCE), find_ability("Folklorist"), find_ability("Don't Mind Me")],
            "removeStandard": ["Folklorist"], "addStandard": [find_ability("Second To None")],
        },
        {
            "range": [6, 6], "name": "Scoundrel", "base": "Sneak", "source": ALTERNATE_SOURCE,
            "starting": [find_ability("Sidestep"), find_ability("Furtive"), find_ability("Flanker")],
            "removeStandard": ["Flanker"], "addStandard": [find_ability("Sticky Fingers")],
        },
        {
            "range": [8, 8], "name": "Bruiser", "base": "Champion", "source": RESKIN_SOURCE,
            "starting": [find_ability("Brawler"), find_ability("Brazen Defense"), find_ability("Into the Fray")],
            "removeStandard": ["Brawler", "Brazen Defense"], "addStandard": [find_ability("Combat Momentum"), find_ability("Favored Weapon")],
        },
        {
            "range": [10, 10], "name": "Bladesmith", "base": "Raider", "source": ALTERNATE_SOURCE,
            "starting": [find_ability("Like the Wind"), find_ability("Ranger"), find_ability("Artisan Smithy")],
            "removeStandard": ["Ranger", "Artisan Smithy"], "addStandard": [find_ability("Sidestep"), find_ability("Hunter's Focus")],
        },
        {
            "range": [12, 12], "name": "Bright-Heart Paladin", "base": "Battle Princess", "source": RESKIN_SOURCE,
            "starting": [blog_ability("Holy Sword", RESKIN_SOURCE), blog_ability("Bonded Mount", RESKIN_SOURCE), blog_ability("Lay on Hands", RESKIN_SOURCE)],
            "removeStandard": ["Compassion Cure"], "addStandard": [find_ability("Shield of Love")],
        },
        {
            "range": [14, 14], "name": "Haunted Knight", "base": "Murder Princess", "source": ALTERNATE_SOURCE,
            "starting": [find_ability("Wrath's Blade"), blog_ability("Beloved Wraith", ALTERNATE_SOURCE), find_ability("Frost Blade")],
            "removeStandard": ["Frost Blade"], "addStandard": [find_ability("Tenacity")],
        },
        {
            "range": [18, 18], "name": "Mountebank", "base": "Sage", "source": RESKIN_SOURCE,
            "starting": [find_ability("Murky Mask"), find_ability("Light Footed"), find_ability("Prestidigitonium")],
            "removeStandard": ["Murky Mask"], "addStandard": [find_ability("Grand Grimoire")],
        },
        {
            "range": [20, 20], "name": "Soothsayer", "base": "Heretic", "source": ALTERNATE_SOURCE,
            "starting": [find_ability("Fitful Sleep"), blog_ability("Dire Divination", ALTERNATE_SOURCE), find_ability("Seer Kasnah")],
            "removeStandard": ["Seer Kasnah"], "addStandard": [find_ability("Squire Marlow")],
        },
    ]

    expanded = []
    core_ranges = {
        "Factotum": [1, 2], "Sneak": [5, 5], "Champion": [7, 7], "Raider": [9, 9],
        "Battle Princess": [11, 11], "Murder Princess": [13, 13], "Sage": [17, 17], "Heretic": [19, 19],
    }
    for name, roll_range in core_ranges.items():
        entry = deepcopy(core[name])
        entry["range"] = roll_range
        expanded.append(entry)

    for variant in variants:
        entry = deepcopy(core[variant["base"]])
        entry.update({
            "range": variant["range"], "name": variant["name"], "baseCalling": variant["base"],
            "sourceUrl": variant["source"], "expanded": True,
        })
        if variant["name"] == "Scribe":
            entry.pop("inventoryBonus", None)
            entry.pop("inventoryBonusSource", None)
        expanded.append(entry)
        standard = [
            deepcopy(ability) for ability in abilities[variant["base"]]["standard"]
            if ability["name"] not in variant["removeStandard"]
        ] + variant["addStandard"]
        abilities[variant["name"]] = {"starting": variant["starting"], "standard": standard}

    balladeer = {
        "range": [16, 16],
        "name": "Balladeer",
        "sourceUrl": BALLADEER_SOURCE,
        "expanded": True,
        "aptitudes": {"might": 6, "deftness": 7, "grit": 7, "insight": 10, "aura": 10},
        "attack": 0,
        "hearts": 2,
        "defense": 10,
        "speed": "Average",
        "gearAllowance": {"weapons": ["Standard", "Thrown"], "armor": ["Light"], "shields": []},
        "gearAllowanceSourceUrl": BALLADEER_SOURCE,
    }
    abilities["Balladeer"] = {
        "starting": [blog_ability(name, BALLADEER_SOURCE) for name in ["Leitmotif", "Focus Instrument", "The Song in Your Heart"]],
        "standard": [blog_ability(name, BALLADEER_SOURCE) for name in [
            "Disparaging Ditty", "Guiding Beat", "Beckoning Note", "Glorious Echo",
            "Harmonious Hearts", "Tranquil Tune", "Beast Song", "Something to Remember Me By!",
        ]],
    }
    expanded.append(balladeer)

    henshin_hero = {
        "range": [15, 15],
        "name": "Henshin Hero",
        "sourceUrl": HENSHIN_SOURCE,
        "expanded": True,
        "aptitudes": {"might": 8, "deftness": 7, "grit": 10, "insight": 7, "aura": 10},
        "attack": 1,
        "hearts": 3,
        "defense": 10,
        "speed": "Average",
        "gearAllowance": {"weapons": ["Standard", "Concealed", "Small Mechanical"], "armor": [], "shields": []},
        "gearAllowanceSourceUrl": HENSHIN_SOURCE,
    }
    abilities["Henshin Hero"] = {
        "starting": [blog_ability(name, HENSHIN_SOURCE) for name in ["Transformation Driver", "Primary Form", "Finisher"]],
        "standard": [blog_ability(name, HENSHIN_SOURCE) for name in [
            "Additional Form", "Gacha Weapon", "Justice Visor", "Dynamic Guard",
            "Inspiring Opponent", "Timely Arrival", "Eye for Trouble", "Heroic Hobby",
        ]],
    }
    expanded.append(henshin_hero)

    return sorted(expanded, key=lambda calling: calling["range"][0])


def equal_name_table(names: list[str]) -> list[dict]:
    step = 20 // len(names)
    return [
        {"range": [index * step + 1, 20 if index == len(names) - 1 else (index + 1) * step], "name": name}
        for index, name in enumerate(names)
    ]


def build_expanded_species(ability_data: dict[str, dict]) -> list[dict]:
    core = {species["name"]: species for species in SPECIES}
    abilities = ability_data["species"]
    expanded = []
    core_ranges = {
        "Human, Native": [1, 3], "Human, Dimensional Stray": [4, 4], "Chib": [5, 6],
        "Tenebrate": [7, 8], "Rai-Neko": [9, 9], "Promethean": [11, 11], "Gruun": [13, 13],
        "Goblin": [15, 15], "Dwarf": [16, 16], "Elf": [17, 17], "Bio-Mechanoid": [19, 19],
    }
    for name, roll_range in core_ranges.items():
        entry = deepcopy(core[name])
        entry["range"] = roll_range
        expanded.append(entry)

    new_species = [
        {
            "range": [10, 10], "name": "Hoppalong", "size": "Medium", "quirkTable": "Inheritor",
            "nameTable": "Hoppalong", "sourceUrl": HOPPALONG_SOURCE, "expanded": True,
            "abilities": ["Prey's Instinct"],
        },
        {
            "range": [12, 12], "name": "Gadabovid", "size": "Large", "quirkTable": "Inheritor",
            "nameTable": "Gadabovid", "sourceUrl": SURF_TURF_SOURCE, "expanded": True,
            "abilities": ["Grazer"],
        },
        {
            "range": [14, 14], "name": "Mundymutt", "sizeOptions": ["Small", "Medium", "Large"],
            "quirkTable": "Inheritor", "nameTable": "Mundymutt", "page": 403, "expanded": True,
            "abilities": ["Doggone Good Sense"],
        },
        {
            "range": [18, 18], "name": "Neridian", "size": "Medium", "quirkTable": "Inheritor",
            "nameTable": "Neridian", "sourceUrl": SURF_TURF_SOURCE, "expanded": True,
            "startingAllegiance": "1 Dark", "fixedGift": "Melodious Voice", "fixedGiftPage": 207,
            "abilities": ["Ocean Farer", "Sea Song"],
        },
        {
            "range": [20, 20], "name": "Unterkin", "size": "Small", "quirkTable": "Unterkin",
            "nameTable": "Unterkin", "sourceUrl": UNTERKIN_SOURCE, "expanded": True,
            "fixedHomeland": "Buried Kingdom",
            "compatibleCallings": ["Factotum", "Scribe", "Sneak", "Scoundrel", "Sage", "Mountebank", "Balladeer"],
            "abilities": ["Ageless", "Heart's Craft"],
        },
    ]
    for species in new_species:
        expanded.append(species)
        abilities[species["name"]] = [
            ({"name": name, "sourceUrl": species["sourceUrl"]} if species.get("sourceUrl") else {"name": name, "pages": [403, 403]})
            for name in species["abilities"]
        ]
        species.pop("abilities")
    return sorted(expanded, key=lambda species: species["range"][0])


def build_neridian_histories() -> list[dict]:
    return [
        {
            "range": [1, 7], "name": "Shadow Sea Recluse", "tier": "Undersea Origin",
            "homeland": "Wistful Dark", "sourceUrl": SURF_TURF_SOURCE,
            "gear": [
                expanded_gear("Arc Weapon", "ritual trident", SURF_TURF_SOURCE),
                expanded_gear("Light Armor", "witchguard shell mail", SURF_TURF_SOURCE),
                expanded_gear("Lumi-Slime Lantern", "luminescent orb", SURF_TURF_SOURCE),
                expanded_gear("Rations x10", "sliced midnight seaweed", SURF_TURF_SOURCE),
            ],
        },
        {
            "range": [8, 14], "name": "Ruin Dweller", "tier": "Undersea Origin",
            "homeland": "Twilight Meridian", "sourceUrl": SURF_TURF_SOURCE,
            "gear": [
                expanded_gear("Scanner", "beepy-boopy thing you found", SURF_TURF_SOURCE),
                expanded_gear("Treats x10", "sealed pack of CaloriePals", SURF_TURF_SOURCE),
                expanded_gear("Standard Shield", "pincher shell shield", SURF_TURF_SOURCE),
                expanded_gear("Luxury Item", "mistaken eating utensil", SURF_TURF_SOURCE),
            ],
        },
        {
            "range": [15, 20], "name": "Coral Farmer", "tier": "Undersea Origin",
            "homeland": "Blazing Garden", "sourceUrl": SURF_TURF_SOURCE,
            "gear": [
                expanded_gear("Long Grabber", "coral picker", SURF_TURF_SOURCE),
                expanded_gear("Quick Weapon", "quill sword", SURF_TURF_SOURCE),
                expanded_gear("Traveler's Bag", "gulper fish pack", SURF_TURF_SOURCE),
                expanded_gear("Trade Goods", "clamfruit bushel", SURF_TURF_SOURCE),
            ],
        },
    ]


def build_unterkin_histories() -> list[dict]:
    return [
        {
            "range": [1, 5], "name": "Red Hand", "tier": "Unterkin History", "sourceUrl": UNTERKIN_SOURCE,
            "gear": [
                expanded_gear("Thrown Weapon", "bits of a shattered blade", UNTERKIN_SOURCE),
                expanded_gear("Light Armor", "patchwork mail", UNTERKIN_SOURCE),
                expanded_gear("Lumi-Slime Lantern", "your last friend from home", UNTERKIN_SOURCE),
                expanded_gear("Rations x10", "cured deeproot", UNTERKIN_SOURCE),
            ],
        },
        {
            "range": [6, 10], "name": "Fizzicist", "tier": "Unterkin History", "sourceUrl": UNTERKIN_SOURCE,
            "gear": [
                expanded_gear("Artisan's Outfit", "your favorite coat", UNTERKIN_SOURCE),
                expanded_gear("Common Urban Good", "sturdy old bottle", UNTERKIN_SOURCE),
                expanded_gear("Basic Potion", "broot beer", UNTERKIN_SOURCE),
                expanded_gear("Grenade", "over-carbonated broot beer", UNTERKIN_SOURCE),
            ],
        },
        {
            "range": [11, 15], "name": "Storyteller", "tier": "Unterkin History", "sourceUrl": UNTERKIN_SOURCE,
            "gear": [
                expanded_gear("Toodle Flute", "oddity and luxury instrument", UNTERKIN_SOURCE),
                expanded_gear("Proper Pen", "common urban good", UNTERKIN_SOURCE),
                expanded_gear("Appealing Outfit", "multi-colored cloak", UNTERKIN_SOURCE),
                expanded_gear("Treats x10", "star sweets", UNTERKIN_SOURCE),
            ],
        },
        {
            "range": [16, 20], "name": "Wonder Aspirant", "tier": "Unterkin History", "sourceUrl": UNTERKIN_SOURCE,
            "gear": [
                expanded_gear("Star Gem", "memento of their greatest work", UNTERKIN_SOURCE),
                expanded_gear("Shadow Stone", "reminder that everything can be broken", UNTERKIN_SOURCE),
                expanded_gear("Forgotten Lore Tome", "wonder werk manual", UNTERKIN_SOURCE),
                expanded_gear("Compass", "something you always knew you'd need", UNTERKIN_SOURCE),
            ],
        },
    ]


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
    expanded_callings = build_expanded_callings(abilities)
    expanded_species = build_expanded_species(abilities)
    payload = {
        "schemaVersion": 2,
        "source": "BREAK!! RPG Core Rules v1",
        "callings": CALLINGS,
        "expandedTableSource": EXPANDED_TABLE_SOURCE,
        "expandedCallings": expanded_callings,
        "species": SPECIES,
        "expandedSpecies": expanded_species,
        "homelands": HOMELANDS,
        "histories": build_histories(),
        "neridianHistories": build_neridian_histories(),
        "unterkinHistories": build_unterkin_histories(),
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
        } | {
            "Hoppalong": equal_name_table(["Skippy Floofins", "Cotton Highhop", "Bouncy Bedding", "Nimble Puffins"]),
            "Gadabovid": equal_name_table(["Jesse Littlehouse", "Sundance Openrange", "Annie Prairiefarm", "Etta Stonyranch"]),
            "Mundymutt": equal_name_table(["Ruff Akitaa", "Paws Terrerian", "Ruh Roh", "Bau Bau", "Knight Pugwash"]),
            "Neridian": equal_name_table(["Tea Foam", "Pearl Current", "Melody Coral", "Symmetry Wave"]),
            "Unterkin": equal_name_table(["Patasy Potables", "Bluesy Hugh", "Keepin Chinup", "Munamina", "Henkly Widget"]),
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
            "brightGifts": ["Luminescent Tattoos", "Serpent Eyes", "Halo", "Resonant Voice", "Feathers", "Aesthetic Consistency", "Scaled Joints", "Prismatic Hair", "Elongation", "Third Eye Gem"],
            "ailments": AILMENTS,
            "specialistKits": SPECIALIST_KITS,
            "craftingDisciplines": ["Forging", "Gadgeteering", "Tailoring", "Artificing", "Alchemy", "Cooking"],
            "petNames": ["Growl", "Buzzer", "Pudge Grub", "Fuzzcoil", "Skree", "Purr"],
            "bioskinSpecies": ["Human", "Tenebrate", "Elf"],
            "companionTypes": ["Guardian Animal", "Brave Toy"],
            "animalCompanionAbilities": ["Mount", "Burrower", "Fighter", "Glider"],
            "toyCompanionAbilities": ["Shielder", "Weapon Link", "Booster", "Toter"],
            "aptitudes": ["might", "deftness", "grit", "insight", "aura"],
            "henshinMotifs": ["Insects", "Beauty Products", "Games", "Vehicles", "Ancient Warriors", "Foodstuffs"],
            "henshinAllegianceMotifs": ["Light", "Dark"],
            "henshinDriverBenefits": ["Referencer", "Pocket Device", "Scanner", "Weapon"],
            "henshinDriverWeapons": ["Concealed", "Small Mechanical"],
            "henshinForms": ["Attacker", "Defender", "Gunner", "Sprinter"],
            "henshinFinishers": ["Attack Edge", "Additional Heart", "All Foes in Area"],
        },
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()