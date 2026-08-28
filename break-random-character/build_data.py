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
ITEMS_SOURCE = ROOT / "questline-vtt-tools" / "BREAK!! Test OCR Items.items"

SHOP_PAGES = {
    "Weapons": 152,
    "Armor": 163,
    "Shields": 169,
    "Outfits": 172,
    "Wearable Accessories": 173,
    "Wayfinding": 174,
    "Illumination": 175,
    "Specialist's Kits": 176,
    "Books": 176,
    "Consumables": 177,
    "Combustibles & Chemicals": 178,
    "Miscellaneous": 179,
    "Curiosities, Artifacts & Gadgets": 180,
}

STARTING_GEAR_SLOT_TENTHS = {
    "50 Coins": 0,
    "Arcane Powder x2 Units": 20,
    "Basic Potion x2": 20,
    "Backpack": 0,
    "Black-out Goggles": 10,
    "Bomb x1": 30,
    "Booster Cakes x2": 2,
    "Booster Cakes x2: Insight": 2,
    "Common Rural Item": 10,
    "Common Urban Good": 10,
    "Companion: Growl": 0,
    "Concealed Weapon with Utility Ability": 10,
    "Drawn Weapon & 10 Arrows": 30,
    "Drawn Weapon & Arrows x10": 30,
    "Extreme Weather Outfit: Cold": 20,
    "Extreme Weather Outfit: Hot": 20,
    "Flame Grenades x2": 20,
    "Follower: Custrel": 0,
    "Follower: Scamp": 0,
    "Forgotten Lore Tome": 20,
    "Gem x1": 0,
    "Grenades x2": 20,
    "Hardy Rations x10": 10,
    "Hardy Rations x5": 5,
    "Lantern & Oil Units x2": 12,
    "Lantern & Oil/Fuel Unit x1": 11,
    "Large Mechanical Missile Weapon & Ammo x5": 25,
    "Luxury Item": 10,
    "Mighty Weapon with Utility Ability": 20,
    "Mount": 0,
    "Oddity": 10,
    "Oil/Fuel Units x10": 10,
    "Other World Side Arm & Ammo x10": 20,
    "Pack Beast: Shaggy Bumpo": 0,
    "Packbeast": 0,
    "Paw Post Membership": 0,
    "Pet: Growl": 0,
    "Pet: Purr": 0,
    "Pet: Skree": 0,
    "Precise Dabber & Solvent x1 Unit": 20,
    "Proper Pen": 10,
    "Pudge Grub": 0,
    "Rations x10": 10,
    "Rebreather Mask": 10,
    "Riding Mount: Jumbug": 0,
    "Rural Goods": 10,
    "Rural Item": 10,
    "Small Mechanical Missile Weapon": 10,
    "Small Mechanical Weapon & Bolts x10": 20,
    "Solvent Units x2": 20,
    "Solvent x2 Units": 20,
    "Standard Weapon with Utility Ability": 10,
    "Thrown Missile Weapon": 10,
    "Toodle Flute": 10,
    "Trade Goods x2 Units": 60,
    "Traveler's Bag": 0,
    "Translation Guide: Fade Song": 10,
    "Treat x10": 10,
    "Treat x2 & Hardy Rations x2": 4,
    "Treat x5": 5,
    "Treats x10": 10,
    "Urban Goods": 10,
    "Vial of Bright Water x3": 30,
}

STARTING_GEAR_COST_STONES = {
    "50 Coins": 5_000,
    "Arcane Powder x2 Units": 10_000,
    "Artisan's Outfit": 800,
    "Basic Potion x2": 2_000,
    "Black-out Goggles": 200,
    "Bomb x1": 4_500,
    "Booster Cakes x2": 3_000,
    "Booster Cakes x2: Insight": 3_000,
    "Common Rural Item": 8,
    "Common Urban Good": 12,
    "Companion: Growl": 7_500,
    "Concealed Weapon with Utility Ability": 1_012,
    "Drawn Weapon & 10 Arrows": 1_200,
    "Drawn Weapon & Arrows x10": 1_200,
    "Extreme Weather Outfit: Cold": 1_200,
    "Extreme Weather Outfit: Hot": 800,
    "Flame Grenades x2": 4_000,
    "Follower: Custrel": 800,
    "Follower: Scamp": 10,
    "Forgotten Lore Tome": 2_400,
    "Gem x1": 10_000,
    "Grenades x2": 4_000,
    "Hardy Rations x10": 30,
    "Hardy Rations x5": 15,
    "Lantern & Oil Units x2": 700,
    "Lantern & Oil/Fuel Unit x1": 600,
    "Large Mechanical Missile Weapon & Ammo x5": 2_700,
    "Luxury Item": 1_600,
    "Mighty Weapon with Utility Ability": 2_508,
    "Oddity": 1_600,
    "Oil/Fuel Units x10": 1_000,
    "Pack Beast: Shaggy Bumpo": 40_000,
    "Paw Post Membership": 50_000,
    "Pet: Growl": 7_500,
    "Pet: Purr": 7_500,
    "Pet: Skree": 10_000,
    "Precise Dabber & Solvent x1 Unit": 2_800,
    "Proper Pen": 12,
    "Rations x10": 10,
    "Rebreather Mask": 1_500,
    "Riding Mount: Jumbug": 20_000,
    "Rural Goods": 8,
    "Rural Item": 8,
    "Small Mechanical Missile Weapon": 1_500,
    "Small Mechanical Weapon & Bolts x10": 1_900,
    "Solvent Units x2": 4_000,
    "Solvent x2 Units": 4_000,
    "Standard Weapon with Utility Ability": 1_508,
    "Thrown Missile Weapon": 200,
    "Toodle Flute": 1_600,
    "Trade Goods x2 Units": 5_000,
    "Translation Guide: Fade Song": 2_000,
    "Treat x10": 30,
    "Treat x2 & Hardy Rations x2": 12,
    "Treat x5": 15,
    "Treats x10": 30,
    "Urban Goods": 12,
    "Vial of Bright Water x3": 15_000,
}

STARTING_GEAR_COST_RATES = {
    "Follower: Custrel": "per day",
    "Follower: Scamp": "per day",
    "Paw Post Membership": "per year",
}

STARTING_GEAR_CURRENCY_STONES = {
    "50 Coins": 5_000,
    "Gem x1": 10_000,
}

INVENTORY_BONUS_TENTHS = {
    "Backpack": 50,
    "Traveler's Bag": 30,
}

SHOP_STACK_LIMITS = {
    "Rations": 10,
    "Hardy Rations": 10,
    "Treats": 10,
    "Basic Potion": 3,
    "Booster Cakes": 3,
    "Oil/Fuel": 2,
    "Solvent": 3,
    "Grenade": 3,
    "Bomb": 2,
}

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


def item_cost_stones(cost: dict) -> int:
    return cost.get("stones", 0) + cost.get("coins", 0) * 100 + cost.get("gems", 0) * 10_000


def load_item_catalog() -> list[dict]:
    return json.loads(ITEMS_SOURCE.read_text())


def build_shop_items(items: list[dict]) -> list[dict]:
    shop_items = []
    for item in items:
        details = item.get("data", {})
        subtype = details.get("subtype")
        if details.get("type") != "Gear" or subtype not in SHOP_PAGES:
            continue
        inventory_bonus = INVENTORY_BONUS_TENTHS.get(item["name"], 0)
        cost_stones = item_cost_stones(details.get("cost", {}))
        if cost_stones <= 0 or (not isinstance(details.get("encumbrance"), (int, float)) and not inventory_bonus):
            continue
        entry = {
            "name": item["name"],
            "page": SHOP_PAGES[subtype],
            "category": subtype,
            "costStones": cost_stones,
            "slotTenths": round(details.get("encumbrance", 0) * 10),
        }
        if inventory_bonus:
            entry["inventoryBonusTenths"] = inventory_bonus
        if item["name"] in SHOP_STACK_LIMITS:
            entry["stackLimit"] = SHOP_STACK_LIMITS[item["name"]]
        entry.update(classify_combat_gear(item["name"]))
        shop_items.append(entry)
    return shop_items


def starting_gear_slot_tenths(name: str, catalog: dict[str, dict]) -> int:
    if name in catalog and isinstance(catalog[name].get("data", {}).get("encumbrance"), (int, float)):
        return round(catalog[name]["data"]["encumbrance"] * 10)
    if name.startswith("Beginner's Tome:"):
        return 10
    if name in STARTING_GEAR_SLOT_TENTHS:
        return STARTING_GEAR_SLOT_TENTHS[name]
    raise ValueError(f"Starting gear needs an explicit slot mapping: {name}")


def starting_gear_cost_stones(gear: dict, catalog: dict[str, dict]) -> int | None:
    name = gear["name"]
    if name.startswith("Beginner's Tome:"):
        return 600
    if name == "Lantern" and "Oil/Fuel Units x2" in gear.get("nickname", ""):
        return 700
    if name in STARTING_GEAR_COST_STONES:
        return STARTING_GEAR_COST_STONES[name]
    cost = catalog.get(name, {}).get("data", {}).get("cost")
    return item_cost_stones(cost) if cost is not None else None


def annotate_history_gear(histories: list[dict], catalog: dict[str, dict]) -> list[dict]:
    for history in histories:
        for gear in history["gear"]:
            gear["slotTenths"] = starting_gear_slot_tenths(gear["name"], catalog)
            gear["costStones"] = starting_gear_cost_stones(gear, catalog)
            if gear["name"] in STARTING_GEAR_CURRENCY_STONES:
                gear["currencyStones"] = STARTING_GEAR_CURRENCY_STONES[gear["name"]]
            if gear["name"] in STARTING_GEAR_COST_RATES:
                gear["costRate"] = STARTING_GEAR_COST_RATES[gear["name"]]
            if gear["name"] in INVENTORY_BONUS_TENTHS:
                gear["inventoryBonusTenths"] = INVENTORY_BONUS_TENTHS[gear["name"]]
    return histories


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
            ("Mechanical (Small)", "Small Mechanical"),
            ("Mechanical (Large)", "Large Mechanical"),
            ("Combination", "Combination"),
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


def build_histories(item_catalog: dict[str, dict]) -> dict[str, list[dict]]:
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
        annotate_history_gear(result[homeland.subtype], item_catalog)
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
    items = load_item_catalog()
    item_catalog = {item["name"]: item for item in items}
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
        "histories": build_histories(item_catalog),
        "neridianHistories": annotate_history_gear(build_neridian_histories(), item_catalog),
        "unterkinHistories": annotate_history_gear(build_unterkin_histories(), item_catalog),
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
        "shopItems": build_shop_items(items),
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