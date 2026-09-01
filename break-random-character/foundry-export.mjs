const APTITUDES = ["might", "deftness", "grit", "insight", "aura"];
const ACTIVE_EFFECT_ADD = "add";
const ACTIVE_EFFECT_OVERRIDE = "override";
const EXPORT_FLAG = "break-random-character";
const EXPORT_VERSION = 2;
const FOUNDRY_CORE_VERSION = "14.367";
const FOUNDRY_SYSTEM_ID = "break";
const FOUNDRY_SYSTEM_VERSION = "1.3";
const FACTOTUM_PACK_NAME = "Factotum's Pack";
const FACTOTUM_PACK_SOURCE = "Factotum Pack";
const CONTAINER_ACCESS_COSTS = {
    Backpack: 2,
    "Traveler's Bag": 1,
    [FACTOTUM_PACK_NAME]: 1,
};
const SPEED_VALUES = { Slow: 0, Average: 1, Fast: 2, "Very Fast": 3 };
const SIZE_VALUES = { Tiny: 0, Small: 1, Medium: 2, Large: 3, Massive: 4, Colossal: 5 };
const GENERIC_ITEM_TYPES = {
    "Wayfinding": "wayfinding",
    "Illumination": "illumination",
    "Specialist's Kits": "kit",
    Books: "book",
    Consumables: "consumable",
    "Combustibles & Chemicals": "combustible",
    Miscellaneous: "miscellaneous",
    "Curiosities, Artifacts & Gadgets": "curiosity",
    Otherworldly: "otherworldly",
};
const WEAPON_TYPE_KEYS = {
    Standard: "standard",
    Concealed: "concealed",
    Quick: "quick",
    Master: "master",
    Mighty: "mighty",
    Arc: "arc",
    Lash: "lash",
    Thrown: "thrown",
    Drawn: "drawn",
    "Small Mechanical": "mechanicalSmall",
    "Large Mechanical": "mechanicalLarge",
    "Mechanical Missile": "mechanicalSmall",
};
const WEAPON_TYPE_DATA = {
    standard: { extraDamage: 20, loadingTime: 1, hands: 1, slots: 1, ranged: false },
    concealed: { extraDamage: 22, loadingTime: 1, hands: 1, slots: 1, ranged: false },
    quick: { extraDamage: 22, loadingTime: 1, hands: 1, slots: 1, ranged: false },
    master: { extraDamage: 18, attackBonus: 1, loadingTime: 1, hands: 1, slots: 2, ranged: false },
    mighty: { extraDamage: 20, loadingTime: 1, hands: 1, slots: 2, ranged: false },
    arc: { extraDamage: 20, loadingTime: 1, hands: 1, slots: 3, ranged: false },
    lash: { extraDamage: 22, loadingTime: 1, hands: 1, slots: 1, ranged: false },
    thrown: { extraDamage: 20, loadingTime: 1, hands: 1, slots: 0, ranged: true },
    drawn: { extraDamage: 20, loadingTime: 1, hands: 1, slots: 0, ranged: true },
    mechanicalSmall: { extraDamage: 20, loadingTime: 1, hands: 1, slots: 0, ranged: true },
    mechanicalLarge: { extraDamage: 20, loadingTime: 1, hands: 1, slots: 0, ranged: true },
};
const ARMOR_SPEED_LIMITS = { Light: 3, Medium: 2, Heavy: 1, Superheavy: 0 };
const EFFECT_PATHS = {
    attack: "system.attack.value",
    defense: "system.defense.value",
    speed: "system.speed.value",
    hearts: "system.hearts.max",
    hands: "system.hands.value",
    slots: "system.slots.value",
    might: "system.aptitudes.might.value",
    deftness: "system.aptitudes.deftness.value",
    grit: "system.aptitudes.grit.value",
    insight: "system.aptitudes.insight.value",
    aura: "system.aptitudes.aura.value",
};

function clone(value) {
    return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

function numberOrZero(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number : 0;
}

function integerOrZero(value) {
    return Math.trunc(numberOrZero(value));
}

function normalizedKey(value) {
    return String(value ?? "").trim().toLowerCase().replace(/[^a-z0-9]+/g, "");
}

function speedValue(speed) {
    return SPEED_VALUES[speed] ?? SPEED_VALUES["Average"];
}

function sizeValue(size) {
    return SIZE_VALUES[size] ?? SIZE_VALUES.Medium;
}

function currencyFromStones(totalStones) {
    let remainder = Math.max(0, integerOrZero(totalStones));
    const gems = Math.floor(remainder / 10000);
    remainder %= 10000;
    const coins = Math.floor(remainder / 100);
    const stones = remainder % 100;
    return { gems, coins, stones };
}

function findByName(records, name) {
    return (records ?? []).find((record) => record?.name === name) || null;
}

function allHistoryRecords(data) {
    return [
        ...Object.values(data.histories ?? {}).flat(),
        ...(data.neridianHistories ?? []),
        ...(data.unterkinHistories ?? []),
    ];
}

function findHistory(data, name) {
    return findByName(allHistoryRecords(data), name);
}

function findQuirk(data, category, name) {
    const categoryRecords = data.quirks?.[category] ?? [];
    return findByName(categoryRecords, name)
        || findByName(Object.values(data.quirks ?? {}).flat(), name);
}

function findCalling(data, name) {
    return findByName([...(data.callings ?? []), ...(data.expandedCallings ?? [])], name);
}

function findSpecies(data, name) {
    return findByName([...(data.species ?? []), ...(data.expandedSpecies ?? [])], name);
}

function referenceData(record = {}) {
    const reference = {};
    if (record.page !== undefined) reference.page = record.page;
    if (record.pages !== undefined) reference.pages = clone(record.pages);
    if (record.sourceUrl) reference.sourceUrl = record.sourceUrl;
    return reference;
}

function createIdFactory(seed) {
    const used = new Set();

    function hash(value) {
        let result = 2166136261;
        for (const character of String(value)) {
            result = Math.imul(result ^ character.charCodeAt(0), 16777619);
        }
        return result >>> 0;
    }

    return (label) => {
        let attempt = 0;
        let id;
        do {
            const first = hash(`${seed}:${label}:${attempt}`).toString(16).padStart(8, "0");
            const second = hash(`${attempt}:${label}:${seed}`).toString(16).padStart(8, "0");
            id = `${first}${second}`;
            attempt += 1;
        } while (used.has(id));
        used.add(id);
        return id;
    };
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function selectionReference(selection) {
    if (selection.pages?.length) {
        const [start, end] = selection.pages;
        return start === end ? `p. ${start}` : `pp. ${start}-${end}`;
    }
    return selection.page === undefined ? "" : `p. ${selection.page}`;
}

function buildNotes(character) {
    const selections = character.selections ?? [];
    const selectionMarkup = selections.length
        ? `<ul>${selections.map((selection) => `<li><strong>${escapeHtml(selection.label)}</strong>: ${escapeHtml(selection.value)}${selectionReference(selection) ? ` (${selectionReference(selection)})` : ""}</li>`).join("")}</ul>`
        : "<p>No additional choices were recorded.</p>";
    const additionalHistory = character.additionalHistory
        ? `<p>Additional History: ${escapeHtml(character.additionalHistory.name)} [${escapeHtml(character.additionalHistory.tier)}]</p>`
        : "";
    const additionalQuirks = character.additionalQuirks?.length
        ? `<p>Additional Quirks: ${character.additionalQuirks.map((quirk) => escapeHtml(quirk.name)).join(", ")}</p>`
        : "";
    return `<p>Resolved choices:</p>${selectionMarkup}${additionalHistory}${additionalQuirks}`;
}

function quirkCategoryNames(data, source) {
    const table = data.quirkCategoryTables?.[source?.quirkTable];
    const entries = Array.isArray(table) ? table : Object.values(table ?? {}).flat();
    return entries
        .map((entry) => entry?.name ?? entry?.category ?? entry?.key)
        .filter(Boolean);
}

function parseQuantity(item) {
    if (Number.isInteger(item.quantity) && item.quantity > 0) return item.quantity;
    const match = String(item.name ?? "").match(/\bx(\d+)\s*$/i);
    return match ? Math.max(1, Number(match[1])) : 1;
}

function isCurrencyGear(item) {
    return numberOrZero(item.currencyStones) > 0;
}

function isOutfit(item) {
    return item.category === "Outfits" || item.name === "Costume" || /outfit/i.test(item.name ?? "");
}

function gearDocumentType(item) {
    if (item.gearCategory === "weapons") return "weapon";
    if (item.gearCategory === "armor") return "armor";
    if (item.gearCategory === "shields") return "shield";
    if (isOutfit(item)) return "outfit";
    if (item.category === "Wearable Accessories" || numberOrZero(item.inventoryBonusTenths) > 0) return "accessory";
    return "item";
}

function genericItemType(category) {
    return GENERIC_ITEM_TYPES[category] || normalizedKey(category) || "miscellaneous";
}

function weaponTypeKey(type) {
    return WEAPON_TYPE_KEYS[type] || WEAPON_TYPE_KEYS[String(type ?? "").trim()]
        || normalizedKey(type) || "standard";
}

function localUnitCost(item, quantity) {
    if (item.unitCostStones !== undefined) return item.unitCostStones;
    if (item.costStones === null || item.costStones === undefined) return 0;
    return numberOrZero(item.costStones) / quantity;
}

function localUnitSlots(item, quantity) {
    if (item.unitSlotTenths !== undefined) return item.unitSlotTenths;
    return numberOrZero(item.slotTenths) / quantity;
}

function baseItemSystem(item, quantity) {
    return {
        description: "",
        slots: localUnitSlots(item, quantity) / 10,
        value: currencyFromStones(localUnitCost(item, quantity)),
        quantity,
        actions: [],
    };
}

function emptyContainerData() {
    return {
        enabled: false,
        capacity: 0,
        accessCost: 0,
        allowedItemTypes: [],
        allowedItemCategories: [],
    };
}

function gearContainerData(item) {
    const capacity = numberOrZero(item.inventoryBonusTenths) / 10;
    if (capacity <= 0) return emptyContainerData();
    return {
        enabled: true,
        capacity,
        accessCost: CONTAINER_ACCESS_COSTS[item.name] ?? 0,
        allowedItemTypes: [],
        allowedItemCategories: [],
    };
}

function createActiveEffect(nextId, name, changes, type = ACTIVE_EFFECT_ADD) {
    return {
        _id: nextId(`effect:${name}`),
        name,
        icon: "icons/svg/aura.svg",
        changes: changes.map(({ key, value, phase = "initial" }) => ({
            key,
            type,
            value: String(value),
            priority: 20,
            phase,
        })),
        disabled: false,
        transfer: true,
        flags: {},
    };
}

function addActiveEffect(item, nextId, name, changes, type = ACTIVE_EFFECT_ADD) {
    const validChanges = changes.filter((change) => EFFECT_PATHS[change.key] || change.path);
    if (!validChanges.length) return;
    item.effects.push(createActiveEffect(nextId, name, validChanges.map((change) => ({
        key: change.path || EFFECT_PATHS[change.key],
        value: change.value,
        phase: change.phase,
    })), type));
}

function makeFlags(reference, generator = {}) {
    return {
        [EXPORT_FLAG]: {
            reference: referenceData(reference),
            ...clone(generator),
        },
    };
}

function makeItem(nextId, name, type, system, reference, generator = {}) {
    return {
        _id: nextId(`item:${type}:${name}`),
        name,
        type,
        img: "icons/svg/item-bag.svg",
        system: { containerId: null, ...system },
        effects: [],
        flags: makeFlags(reference, generator),
    };
}

function buildCallingItem(character, data, nextId, abilityNames) {
    const source = findCalling(data, character.calling.name) || character.calling;
    const progressionName = source.baseCalling || source.name;
    const advancementTable = data.advancementTables?.[progressionName] ?? [];
    const exportedAdvancementTable = advancementTable.map((row) => ({
        attack: integerOrZero(row.attack),
        hearts: integerOrZero(row.hearts),
        might: integerOrZero(row.aptitudes?.might),
        deftness: integerOrZero(row.aptitudes?.deftness),
        grit: integerOrZero(row.aptitudes?.grit),
        insight: integerOrZero(row.aptitudes?.insight),
        aura: integerOrZero(row.aptitudes?.aura),
        xp: integerOrZero(row.xp),
    }));
    if (integerOrZero(character.rank) >= 10 && exportedAdvancementTable.length) {
        const lastRank = exportedAdvancementTable.at(-1);
        exportedAdvancementTable.push({ ...lastRank, xp: lastRank.xp + 1 });
    }
    const system = {
        description: "",
        overview: "",
        headerImage: "",
        baseSpeed: speedValue(source.speed ?? character.combat.speed),
        baseDefense: numberOrZero(source.defense),
        startingAbilities: abilityNames,
        advancementTable: exportedAdvancementTable,
        armorAllowances: clone(source.gearAllowance?.armor ?? []),
        shieldAllowances: clone(source.gearAllowance?.shields ?? []),
        weaponAllowances: clone(source.gearAllowance?.weapons ?? []),
        abilities: [],
    };
    return makeItem(nextId, character.calling.name, "calling", system, character.calling, {
        baseCalling: source.baseCalling || source.name,
        expanded: Boolean(source.expanded),
        inventoryBonusSource: source.inventoryBonusSource || "",
    });
}

function buildSpeciesItem(character, data, nextId, abilityNames, maturativeNames) {
    const source = findSpecies(data, character.species.name) || character.species;
    const system = {
        description: "",
        overview: "",
        size: sizeValue(character.size.name),
        innateAbilities: abilityNames,
        maturativeAbilities: maturativeNames,
        quirkCategories: quirkCategoryNames(data, source),
        abilities: [],
    };
    return makeItem(nextId, character.species.name, "species", system, character.species, {
        expanded: Boolean(source.expanded),
        baseSize: source.size,
        inventoryBonusSource: source.inventoryBonusSource || "",
    });
}

function buildFactotumPackItem(character, data, nextId) {
    const source = findCalling(data, character.calling.name);
    if (source?.inventoryBonusSource !== FACTOTUM_PACK_SOURCE || !numberOrZero(source.inventoryBonus)) return null;
    const capacity = numberOrZero(source.inventoryBonus);
    return makeItem(nextId, FACTOTUM_PACK_NAME, "accessory", {
        ...baseItemSystem({}, 1),
        container: {
            enabled: true,
            capacity,
            accessCost: CONTAINER_ACCESS_COSTS[FACTOTUM_PACK_NAME],
            allowedItemTypes: [],
            allowedItemCategories: [],
        },
    }, character.calling, {
        source: FACTOTUM_PACK_SOURCE,
        synthetic: true,
        inventoryBonusTenths: capacity * 10,
        equipped: true,
        stowed: false,
    });
}

function buildHomelandItem(character, data, nextId) {
    const source = findByName(data.homelands, character.homeland.name) || character.homeland;
    return makeItem(nextId, character.homeland.name, "homeland", {
        description: "",
        bonusLanguages: "",
        histories: [],
    }, character.homeland, {
        availableLanguages: clone(source.languages ?? []),
        selectedLanguage: character.languages?.[1] || "",
    });
}

function buildHistoryItem(character, data, nextId) {
    const source = findHistory(data, character.history.name) || character.history;
    return makeItem(nextId, character.history.name, "history", {
        description: "",
        purviews: [],
        gearPicks: 0,
        startingGear: [],
    }, character.history, {
        tier: character.history.tier,
        generatedGear: character.gear?.filter((item) => item.option !== undefined).map((item) => item.name) ?? [],
        sourceHomeland: character.homeland.name,
        sourceHasPurviews: Boolean(source.purviews?.length),
    });
}

function buildQuirkItem(character, data, nextId) {
    const source = findQuirk(data, character.quirk.category, character.quirk.name) || character.quirk;
    return makeItem(nextId, character.quirk.name, "quirk", {
        description: "",
        advantages: "",
        disadvantages: "",
        type: normalizedKey(character.quirk.category),
        actions: [],
    }, character.quirk, {
        category: character.quirk.category,
        adjustment: clone(data.quirkAdjustments?.[character.quirk.name] ?? {}),
        pages: clone(source.pages ?? character.quirk.pages),
    });
}

function abilitySubtype(ability, fallback) {
    const tier = String(ability.tier ?? fallback ?? "").toLowerCase();
    if (["starting", "standard", "advanced", "innate", "maturative"].includes(tier)) return tier;
    return fallback === "species" ? "innate" : "standard";
}

function buildAbilityItem(ability, type, fallbackSubtype, nextId, generator = {}) {
    const subtype = abilitySubtype(ability, fallbackSubtype);
    const item = makeItem(nextId, ability.name, "ability", {
        type,
        subtype,
        description: "",
        rules: "",
        actions: [],
        magic: Boolean(ability.magical),
    }, ability, {
        tier: ability.tier,
        acquiredRank: ability.acquiredRank,
        ...generator,
    });
    return item;
}

function weaponSystem(type1, type2, slots, value) {
    const primary = WEAPON_TYPE_DATA[type1] ?? WEAPON_TYPE_DATA.standard;
    return {
        description: "",
        slots,
        value,
        quantity: 1,
        extraDamage: primary.extraDamage,
        rangedExtraDamage: primary.ranged ? primary.extraDamage : 0,
        attackBonus: primary.attackBonus ?? 0,
        rangedAttackBonus: 0,
        range: 0,
        loadingTime: primary.loadingTime,
        weaponType1: type1,
        weaponType2: type2,
        abilities: [],
        hands: primary.hands,
        ranged: primary.ranged,
        melee: !primary.ranged,
        actions: [],
    };
}

function specialWeaponData(character, nextId) {
    const choices = character.selections ?? [];
    const weaponChoices = choices.filter((selection) => ["Heart's Blade", "Wrath's Blade", "Holy Sword"].includes(selection.label));
    const properties = new Map(choices
        .filter((selection) => /(?:Heart's|Wrath's|Holy Sword) Blade Property|Holy Sword Property/.test(selection.label))
        .map((selection) => [selection.label.replace(" Property", ""), selection.value]));
    return weaponChoices.flatMap((selection) => {
        const [typesPart, material] = String(selection.value ?? "").split(" / ");
        const typeKeys = typesPart.split("+").map((type) => weaponTypeKey(type.trim())).filter((type) => WEAPON_TYPE_DATA[type]);
        if (!typeKeys.length) return [];
        const system = weaponSystem(typeKeys[0], typeKeys[1] ?? "", WEAPON_TYPE_DATA[typeKeys[0]].slots, { gems: 0, coins: 0, stones: 0 });
        const property = properties.get(selection.label);
        if (property) system.abilities.push(property);
        return [makeItem(nextId, selection.label, "weapon", system, selection, {
            material,
            property: property || "",
            specialChoice: true,
        })];
    });
}

function buildGearItem(item, section, index, nextId) {
    const type = gearDocumentType(item);
    const quantity = parseQuantity(item);
    const system = baseItemSystem(item, quantity);
    if (item.stowed) system.slots = 0;
    if (type === "weapon") {
        const type1 = weaponTypeKey(item.gearType);
        const primary = WEAPON_TYPE_DATA[type1] ?? WEAPON_TYPE_DATA.standard;
        Object.assign(system, weaponSystem(type1, "", system.slots, system.value));
        system.quantity = quantity;
        system.extraDamage = primary.extraDamage;
        system.rangedExtraDamage = primary.ranged ? primary.extraDamage : 0;
    } else if (type === "armor") {
        system.defenseBonus = numberOrZero(item.defenseBonus);
        system.speedLimit = ARMOR_SPEED_LIMITS[item.gearType] ?? 3;
        system.type = normalizedKey(item.gearType) || "light";
        system.abilities = [];
        system.container = emptyContainerData();
    } else if (type === "shield") {
        system.defenseBonus = numberOrZero(item.defenseBonus);
        system.speedPenalty = 0;
        system.type = normalizedKey(item.gearType) || "small";
        system.abilities = [];
        system.hands = 1;
    } else if (type === "accessory") {
        system.container = gearContainerData(item);
    } else if (type === "item") {
        system.type = genericItemType(item.category);
        system.uses = { value: 1, total: 1 };
    }
    const document = makeItem(nextId, item.name, type, system, item, {
        section,
        index,
        option: item.option,
        nickname: item.nickname || "",
        costRate: item.costRate || "",
        unitCostStones: localUnitCost(item, quantity),
        unitSlotTenths: localUnitSlots(item, quantity),
        inventoryBonusTenths: numberOrZero(item.inventoryBonusTenths),
        restricted: Boolean(item.restricted),
        restrictions: clone(item.restrictions ?? []),
        equipped: Boolean(item.equipped),
        stowed: Boolean(item.stowed),
        currencyStones: numberOrZero(item.currencyStones),
    });
    return document;
}

function referenceItem(item) {
    return {
        _id: item._id,
        name: item.name,
        type: item.type,
        img: item.img,
        system: clone(item.system),
        effects: clone(item.effects),
        flags: clone(item.flags),
    };
}

function bestItem(items, predicate) {
    return items.filter(predicate).sort((left, right) => numberOrZero(right.system?.defenseBonus) - numberOrZero(left.system?.defenseBonus))[0] || null;
}

function sourceItemForModifier(source, character, roles) {
    const callingFlags = roles.calling.flags?.[EXPORT_FLAG] ?? {};
    const speciesFlags = roles.species.flags?.[EXPORT_FLAG] ?? {};
    if (source === character.calling.name || source === callingFlags.baseCalling || source === callingFlags.inventoryBonusSource) return roles.calling;
    if (source === character.species.name || source === speciesFlags.inventoryBonusSource) return roles.species;
    if (source === `${character.size.name} Species`) return roles.species;
    if (source === character.quirk.name) return roles.quirk;
    if (source === "Leisurely Focus") return roles.leisurelyFocus || roles.species;
    const ability = roles.abilities.find((item) => item.name === source);
    if (ability) return ability;
    return roles.gear.find((item) => item.name === source) || null;
}

function addModifierEffect(source, character, roles, label, key, value, type = ACTIVE_EFFECT_ADD) {
    if (!numberOrZero(value) && type !== ACTIVE_EFFECT_OVERRIDE) return;
    const item = sourceItemForModifier(source, character, roles);
    if (!item) return;
    addActiveEffect(item, roles.nextId, label, [{ key, value }], type);
}

function applyKnownEffects(character, roles) {
    const abilityHasEffect = (source, key) => roles.abilities.some((item) => item.name === source
        && item.flags?.[EXPORT_FLAG]?.sourceAbility?.effects?.[key] !== undefined);
    const defenseAlternative = (character.modifiers?.combat?.defense ?? [])
        .find((modifier) => ["Brazen Defense", "Bulwark of Disdain"].includes(modifier.source));
    const armor = bestItem(roles.gear, (item) => item.type === "armor");
    if (defenseAlternative && armor && numberOrZero(armor.system?.defenseBonus) < 4) {
        const defenseAlternativeItem = roles.abilities.find((item) => item.name === defenseAlternative.source) || roles.calling;
        addActiveEffect(defenseAlternativeItem, roles.nextId, `${defenseAlternative.source} Armor Replacement`, [{
            path: "system.equipment.armor.system.defenseBonus",
            value: 0,
        }], ACTIVE_EFFECT_OVERRIDE);
    }

    roles.abilities.forEach((item) => {
        const sourceAbility = item.flags?.[EXPORT_FLAG]?.sourceAbility;
        Object.entries(sourceAbility?.effects ?? {}).forEach(([key, value]) => {
            if (EFFECT_PATHS[key] !== undefined) addActiveEffect(item, roles.nextId, `${item.name} ${key}`, [{ key, value }]);
        });
    });

    Object.entries(character.modifiers?.aptitudes ?? {}).forEach(([aptitude, modifiers]) => {
        modifiers.forEach((modifier) => {
            if (modifier.kind === "species") {
                if (modifier.source === `${character.size.name} Species`) addModifierEffect(modifier.source, character, roles, `${modifier.source} ${aptitude}`, aptitude, modifier.amount);
                return;
            }
            addModifierEffect(modifier.source, character, roles, `${modifier.source} ${aptitude}`, aptitude, modifier.amount);
        });
    });

    ["attack", "defense", "speed", "hearts"].forEach((stat) => {
        (character.modifiers?.combat?.[stat] ?? []).forEach((modifier) => {
            if (modifier.kind === "gear") return;
            if (modifier.kind === "species") {
                if (modifier.source === `${character.size.name} Species`) addModifierEffect(modifier.source, character, roles, `${modifier.source} ${stat}`, stat, modifier.amount);
                return;
            }
            if (abilityHasEffect(modifier.source, stat)) return;
            addModifierEffect(modifier.source, character, roles, `${modifier.source} ${stat}`, stat, modifier.amount, modifier.kind === "set" ? ACTIVE_EFFECT_OVERRIDE : ACTIVE_EFFECT_ADD);
        });
    });

    (character.modifiers?.combat?.inventory ?? []).forEach((modifier) => {
        const factotumPackSource = roles.factotumPack?.flags?.[EXPORT_FLAG]?.source;
        if (modifier.kind === "species" || modifier.kind === "gear"
            || (factotumPackSource && modifier.source === factotumPackSource)) return;
        addModifierEffect(modifier.source, character, roles, `${modifier.source} Inventory`, "slots", modifier.amount);
    });

    (character.modifiers?.combat?.allegiance ?? []).forEach((modifier) => {
        if (!modifier.amount || modifier.kind === "gift") return;
        const alignment = modifier.alignment === "Light" ? "bright" : modifier.alignment?.toLowerCase();
        if (!alignment || !["bright", "dark"].includes(alignment)) return;
        const item = sourceItemForModifier(modifier.source, character, roles) || roles.calling;
        addActiveEffect(item, roles.nextId, `${modifier.source} Allegiance`, [{
            path: `system.allegiance.${alignment}`,
            value: modifier.amount,
        }]);
    });
}

function applyInventoryCapacity(character, roles) {
    if (!roles.calling) return;
    const physicalContainerBonus = (character.modifiers?.combat?.inventory ?? [])
        .filter((modifier) => modifier.kind === "gear")
        .reduce((total, modifier) => total + numberOrZero(modifier.amount), 0)
        + numberOrZero(roles.factotumPack?.system?.container?.capacity);
    const baseInventory = numberOrZero(character.combat?.inventory) - physicalContainerBonus;
    addActiveEffect(roles.calling, roles.nextId, "Generated Inventory Capacity", [{
        path: "system.slots.total",
        value: baseInventory,
        phase: "final",
    }, {
        path: "system.inventorySlots",
        value: baseInventory,
        phase: "final",
    }], ACTIVE_EFFECT_OVERRIDE);
}

function applyRank10ProgressionGuard(character, roles) {
    if (integerOrZero(character.rank) < 10 || !roles.calling) return;
    addActiveEffect(roles.calling, roles.nextId, "Rank 10 Progression Guard", [{
        path: "system.xpNextRank",
        value: 0,
        phase: "final",
    }], ACTIVE_EFFECT_OVERRIDE);
}

function itemSlotCost(item) {
    return numberOrZero(item.system?.slots) * numberOrZero(item.system?.quantity ?? 1);
}

function packGearIntoContainer(roles, container, equippedItemIds) {
    if (!container?.system?.container?.enabled) return;
    const capacity = numberOrZero(container.system.container.capacity);
    let used = 0;
    for (const item of roles.gear) {
        const generatorFlags = item.flags?.[EXPORT_FLAG] ?? {};
        if (item._id === container._id
            || equippedItemIds.has(item._id)
            || generatorFlags.equipped
            || generatorFlags.stowed
            || item.system?.container?.enabled) continue;
        const slots = itemSlotCost(item);
        if (used + slots > capacity) continue;
        item.system.containerId = container._id;
        item.flags[EXPORT_FLAG].containerId = container._id;
        used += slots;
    }
}

function addResolvedChoiceItems(character, nextId, items, roles) {
    const leisureChoice = character.selections?.find((selection) => selection.label === "Leisurely Focus");
    if (leisureChoice) {
        const item = buildAbilityItem({
            name: "Leisurely Focus",
            page: leisureChoice.page,
            tier: "Innate",
            effects: { [normalizedKey(leisureChoice.value)]: 1 },
        }, "species", "innate", nextId, { resolvedChoice: leisureChoice.value });
        item.flags[EXPORT_FLAG].sourceAbility = { effects: {} };
        item.flags[EXPORT_FLAG].reference = referenceData(leisureChoice);
        items.push(item);
        roles.abilities.push(item);
        roles.leisurelyFocus = item;
    }

    (character.additionalQuirks ?? []).forEach((quirk, index) => {
        const item = makeItem(nextId, quirk.name, "quirk", {
            description: "",
            advantages: "",
            disadvantages: "",
            type: "",
            actions: [],
        }, quirk, { additional: true, index });
        items.push(item);
        roles.additionalQuirks.push(item);
    });

    const soulCompanion = character.selections?.find((selection) => selection.label === "Soul Companion");
    if (soulCompanion) {
        const item = makeItem(nextId, "Soul Companion", "item", {
            ...baseItemSystem({}, 1),
            type: "miscellaneous",
            uses: { value: 1, total: 1 },
        }, soulCompanion, { resolvedValue: soulCompanion.value, playerMayExpand: true });
        items.push(item);
        roles.soulCompanion = item;
    }
}

function giftItems(character, nextId) {
    return (character.selections ?? [])
        .filter((selection) => /gift/i.test(selection.label) && selection.value)
        .map((selection, index) => {
            const match = String(selection.value).match(/^(Bright|Dark):\s*(.*)$/);
            const alignment = match?.[1]?.toLowerCase() || "";
            const name = match?.[2] || selection.value;
            return makeItem(nextId, name, "gift", {
                ...baseItemSystem({}, 1),
                type: alignment || "gift",
                uses: { value: 1, total: 1 },
            }, selection, { alignment, index });
        });
}

function buildSnapshot(character) {
    return {
        rank: character.rank,
        calling: clone(character.calling),
        species: clone(character.species),
        size: clone(character.size),
        homeland: clone(character.homeland),
        history: clone(character.history),
        additionalHistory: clone(character.additionalHistory),
        languages: clone(character.languages),
        traits: clone(character.traits),
        quirk: clone(character.quirk),
        additionalQuirks: clone(character.additionalQuirks),
        aptitudes: clone(character.aptitudes),
        combat: clone(character.combat),
        allegiance: clone(character.allegiance),
        selections: clone(character.selections),
        shopping: clone(character.shopping),
        gear: clone(character.gear),
        purchasedGear: clone(character.purchasedGear),
    };
}

function actorSeed(character) {
    return `${character.name}:${JSON.stringify(character.seeds ?? {})}`;
}

export function buildFoundryActor(character, data) {
    if (!character || !data) throw new TypeError("A generated character and generator data are required");

    const nextId = createIdFactory(actorSeed(character));
    const items = [];
    const roles = {
        nextId,
        calling: null,
        species: null,
        quirk: null,
        abilities: [],
        gear: [],
        additionalQuirks: [],
        leisurelyFocus: null,
        soulCompanion: null,
        factotumPack: null,
    };

    const callingAbilities = data.callingAbilities?.[character.calling.name] ?? {};
    const speciesAbilities = data.speciesAbilities?.[character.species.name] ?? [];
    const maturative = data.speciesMaturatives?.[character.species.name];
    const abilityNames = [...(callingAbilities.starting ?? [])].map((ability) => ability.name);
    const speciesAbilityNames = speciesAbilities.map((ability) => ability.name);
    const maturativeNames = maturative ? [maturative.name] : [];

    roles.calling = buildCallingItem(character, data, nextId, abilityNames);
    roles.species = buildSpeciesItem(character, data, nextId, speciesAbilityNames, maturativeNames);
    const homelandItem = buildHomelandItem(character, data, nextId);
    const historyItem = buildHistoryItem(character, data, nextId);
    roles.quirk = buildQuirkItem(character, data, nextId);
    items.push(roles.calling, roles.species, homelandItem, historyItem, roles.quirk);

    (callingAbilities.starting ?? []).forEach((ability) => {
        const item = buildAbilityItem(ability, "calling", "starting", nextId, { sourceAbility: clone(ability) });
        items.push(item);
        roles.abilities.push(item);
    });
    speciesAbilities.forEach((ability) => {
        const item = buildAbilityItem(ability, "species", "innate", nextId, { sourceAbility: clone(ability) });
        items.push(item);
        roles.abilities.push(item);
    });
    if (character.abilities.prodigy) {
        const item = buildAbilityItem(character.abilities.prodigy, "calling", "standard", nextId, { sourceAbility: clone(character.abilities.prodigy), prodigy: true });
        items.push(item);
        roles.abilities.push(item);
    }
    (character.abilities.elective ?? []).forEach((ability) => {
        const type = ability.tier === "Maturative" ? "species" : "calling";
        const item = buildAbilityItem(ability, type, type === "species" ? "maturative" : "standard", nextId, { sourceAbility: clone(ability) });
        items.push(item);
        roles.abilities.push(item);
    });

    addResolvedChoiceItems(character, nextId, items, roles);
    const specialWeapons = specialWeaponData(character, nextId);
    items.push(...specialWeapons);
    const gifts = giftItems(character, nextId);
    items.push(...gifts);

    const gearEntries = [
        ...(character.gear ?? []).filter((item) => !isCurrencyGear(item)).map((item, index) => ({ item, section: "starting", index })),
        ...(character.purchasedGear ?? []).filter((item) => !isCurrencyGear(item)).map((item, index) => ({ item, section: "purchased", index })),
    ];
    gearEntries.forEach(({ item, section, index }) => {
        const document = buildGearItem(item, section, index, nextId);
        items.push(document);
        roles.gear.push(document);
    });

    const factotumPack = buildFactotumPackItem(character, data, nextId);
    if (factotumPack) {
        items.push(factotumPack);
        roles.gear.push(factotumPack);
        roles.factotumPack = factotumPack;
    }

    applyKnownEffects(character, roles);
    applyInventoryCapacity(character, roles);
    applyRank10ProgressionGuard(character, roles);

    const equipmentGear = roles.gear;
    const armor = bestItem(equipmentGear, (item) => item.type === "armor");
    const shield = bestItem(equipmentGear, (item) => item.type === "shield");
    const outfit = equipmentGear.find((item) => item.type === "outfit" && item.name === character.equippedOutfit)
        || equipmentGear.find((item) => item.type === "outfit" && item.flags?.[EXPORT_FLAG]?.equipped);
    const containerAccessories = equipmentGear.filter((item) => item.type === "accessory"
        && numberOrZero(item.flags?.[EXPORT_FLAG]?.inventoryBonusTenths) > 0);
    const normalWeapons = equipmentGear.filter((item) => item.type === "weapon");
    const equippedWeapons = specialWeapons.length ? specialWeapons : normalWeapons.slice(0, 1);
    const equippedItemIds = new Set([
        armor?._id,
        outfit?._id,
        shield?._id,
        ...equippedWeapons.map((item) => item._id),
        ...containerAccessories.map((item) => item._id),
        ...equipmentGear.filter((item) => item.flags?.[EXPORT_FLAG]?.equipped).map((item) => item._id),
    ].filter(Boolean));
    packGearIntoContainer(roles, containerAccessories[0], equippedItemIds);

    const rank = Math.max(1, Math.min(10, integerOrZero(character.rank) || 1));
    const progressionName = findCalling(data, character.calling.name)?.baseCalling || character.calling.name;
    const advancement = data.advancementTables?.[progressionName]?.[rank - 1] || {};
    const baseAptitudes = advancement.aptitudes ?? {};
    const actorSystem = {
        attack: { value: integerOrZero(advancement.attack) },
        defense: { value: numberOrZero(findCalling(data, character.calling.name)?.defense ?? character.combat.defense) },
        speed: { value: speedValue(findCalling(data, character.calling.name)?.speed ?? character.combat.speed) },
        hearts: { value: Math.max(1, integerOrZero(character.combat.hearts)), max: integerOrZero(advancement.hearts) },
        hands: { value: 2 },
        slots: { value: 0 },
        size: { value: sizeValue(character.size.name) },
        aptitudes: Object.fromEntries(APTITUDES.map((aptitude) => [aptitude, {
            value: integerOrZero(baseAptitudes[aptitude]),
            trait: Math.max(-2, Math.min(2, integerOrZero((character.traits ?? [])
                .filter((trait) => trait.aptitude === aptitude)
                .reduce((total, trait) => total + integerOrZero(trait.amount), 0)))),
        }])),
        equipment: {
            armor: armor ? referenceItem(armor) : null,
            outfit: outfit ? referenceItem(outfit) : null,
            accessory: containerAccessories.map(referenceItem),
            weapon: equippedWeapons.map(referenceItem),
            shield: shield ? referenceItem(shield) : null,
        },
        allegiance: { dark: 0, bright: 0 },
        notes: buildNotes(character),
        xp: {
            rank,
            current: integerOrZero(advancement.xp),
        },
        languages: clone(character.languages ?? []),
        description: "",
        purviews: [],
        currency: currencyFromStones(character.shopping?.totalCurrencyStones ?? character.coins * 100),
    };

    const actor = {
        _id: nextId("actor"),
        name: character.name,
        type: "character",
        img: "",
        system: actorSystem,
        items,
        effects: [],
        flags: {
            [EXPORT_FLAG]: {
                exportVersion: EXPORT_VERSION,
                generatorSchemaVersion: data.schemaVersion,
                source: data.source || "BREAK!! RPG Core Rules",
                contentMode: character.contentMode,
                seeds: clone(character.seeds),
                rolls: clone(character.rolls),
                snapshot: buildSnapshot(character),
                notes: {
                    noCompendiumReferences: true,
                    actionsIncluded: false,
                    companionActorsIncluded: false,
                },
            },
        },
        _stats: {
            coreVersion: FOUNDRY_CORE_VERSION,
            systemId: FOUNDRY_SYSTEM_ID,
            systemVersion: FOUNDRY_SYSTEM_VERSION,
        },
        prototypeToken: { actorLink: true, depth: 1 },
        ownership: { default: 0 },
        folder: null,
        sort: 0,
    };
    return actor;
}

function safeFileName(name) {
    const fileName = String(name || "BREAK Character")
        .replace(/[^a-z0-9]+/gi, "-")
        .replace(/^-+|-+$/g, "")
        .toLowerCase();
    return `${fileName || "break-character"}.json`;
}

export function downloadFoundryActor(character, data) {
    const actor = buildFoundryActor(character, data);
    if (typeof document === "undefined" || typeof Blob === "undefined" || typeof URL === "undefined" || typeof URL.createObjectURL !== "function") {
        throw new Error("Foundry export downloads require a browser");
    }
    const blob = new Blob([JSON.stringify(actor, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = safeFileName(character.name);
    link.hidden = true;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 0);
    return actor;
}

export { currencyFromStones, gearDocumentType, sizeValue, speedValue };