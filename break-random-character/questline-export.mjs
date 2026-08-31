const APTITUDES = ["might", "deftness", "grit", "insight", "aura"];
const QUESTLINE_PLAYER_SHEET_ID = "JhUsxZOelsROtFyksRAP";
const EXPORT_FLAG = "studio-quagg-break-random-character";
const EXPORT_VERSION = 1;
const BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
const SPEED_VALUES = { Slow: 0, Average: 1, Fast: 2, "Very Fast": 3 };

function numberOrZero(value) {
    const number = Number(value);
    return Number.isFinite(number) ? number : 0;
}

function integerOrZero(value) {
    return Math.trunc(numberOrZero(value));
}

function clone(value) {
    return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

function hash32(value, salt = 2166136261) {
    let hash = salt >>> 0;
    for (const character of String(value)) {
        hash ^= character.charCodeAt(0);
        hash = Math.imul(hash, 16777619) >>> 0;
    }
    return hash >>> 0;
}

function stableId(value) {
    let state = hash32(value);
    let result = "";
    for (let index = 0; index < 20; index += 1) {
        state = Math.imul(state ^ hash32(`${value}:${index}`, state), 2246822519) >>> 0;
        result += BASE62[state % BASE62.length];
    }
    return result;
}

function stableUuid(value) {
    const parts = [
        hash32(`${value}:0`).toString(16).padStart(8, "0"),
        hash32(`${value}:1`).toString(16).padStart(8, "0"),
        hash32(`${value}:2`).toString(16).padStart(8, "0"),
        hash32(`${value}:3`).toString(16).padStart(8, "0"),
    ];
    const hexadecimal = parts.join("").split("");
    hexadecimal[12] = "4";
    hexadecimal[16] = (Number.parseInt(hexadecimal[16], 16) & 3 | 8).toString(16);
    const joined = hexadecimal.join("");
    return `${joined.slice(0, 8)}-${joined.slice(8, 12)}-${joined.slice(12, 16)}-${joined.slice(16, 20)}-${joined.slice(20)}`;
}

function createIdFactory(seed) {
    const used = new Set();
    return (label) => {
        let attempt = 0;
        let id;
        do {
            id = stableId(`${seed}:${label}:${attempt}`);
            attempt += 1;
        } while (used.has(id));
        used.add(id);
        return id;
    };
}

function speedValue(speed) {
    return SPEED_VALUES[speed] ?? SPEED_VALUES.Average;
}

function formatReference(reference = {}) {
    if (reference.pages?.length) {
        const [start, end] = reference.pages;
        return start === end ? `p. ${start}` : `pp. ${start}-${end}`;
    }
    if (reference.page !== undefined && reference.page !== null) return `p. ${reference.page}`;
    if (reference.sourceUrl) return reference.sourceUrl;
    return "";
}

function referenceLine(reference) {
    const referenceText = formatReference(reference);
    return referenceText ? `Source: ${referenceText}` : "";
}

function currencyFromStones(totalStones) {
    let remainder = Math.max(0, integerOrZero(totalStones));
    const gems = Math.floor(remainder / 10000);
    remainder %= 10000;
    const coins = Math.floor(remainder / 100);
    const stones = remainder % 100;
    return { gems, coins, stones };
}

function currencyText(totalStones) {
    const currency = currencyFromStones(totalStones);
    return [
        currency.gems ? `${currency.gems} Gem${currency.gems === 1 ? "" : "s"}` : "",
        currency.coins ? `${currency.coins} Coin${currency.coins === 1 ? "" : "s"}` : "",
        currency.stones ? `${currency.stones} Stone${currency.stones === 1 ? "" : "s"}` : "",
    ].filter(Boolean).join(", ") || "0 Stones";
}

function parseQuantity(item) {
    if (Number.isInteger(item.quantity) && item.quantity > 0) return item.quantity;
    const match = String(item.name ?? "").match(/\bx(\d+)\s*$/i);
    return match ? Math.max(1, Number(match[1])) : 1;
}

function isCurrencyItem(item) {
    return numberOrZero(item.currencyStones) > 0;
}

function itemUnitCost(item, quantity) {
    if (item.unitCostStones !== undefined) return numberOrZero(item.unitCostStones);
    if (item.costStones === null || item.costStones === undefined) return 0;
    return numberOrZero(item.costStones) / quantity;
}

function itemUnitSlots(item, quantity) {
    if (item.unitSlotTenths !== undefined) return numberOrZero(item.unitSlotTenths);
    return numberOrZero(item.slotTenths) / quantity;
}

function blankTokenCrop() {
    return {
        x: 0,
        y: 0,
        width: 100,
        height: 100,
        aspect: 1,
        unit: "%",
    };
}

function blankImage() {
    return { url: null, tokenCrop: blankTokenCrop() };
}

function featureDescription(feature, detail) {
    const lines = [
        detail ? `Acquisition: ${detail}` : "",
        feature.acquiredRank ? `Acquired at Rank ${feature.acquiredRank}` : "",
        feature.tier && feature.tier !== detail ? `Tier: ${feature.tier}` : "",
        referenceLine(feature),
        feature.sourceUrl ? `Reference: ${feature.sourceUrl}` : "",
        "Complete this feature in Questline.",
    ].filter(Boolean);
    return {
        type: "doc",
        content: lines.map((text) => ({
            type: "paragraph",
            content: [{ type: "text", text }],
        })),
    };
}

function featureRecord(nextId, feature, source, detail) {
    const rank = feature.acquiredRank ? `Rank ${feature.acquiredRank}` : "";
    const parts = [...new Set([detail, rank, feature.tier].filter(Boolean))];
    return {
        id: nextId(`feature:${feature.name}`),
        originId: null,
        type: source,
        name: feature.name,
        description: featureDescription(feature, detail),
        subtext: parts.join(" · "),
        value: 0,
        valuePrefix: null,
        valueSuffix: null,
        bonus: 0,
        linkedValue: null,
        starValue: null,
        counters: {},
        counterOverrides: {},
        modifiers: [],
        modifiersPostCalculationFunc: null,
        rollDetails: [],
    };
}

function actionDetails(description) {
    return [
        { type: "image", visibility: "full", value: { image: blankImage() } },
        { type: "description", visibility: "full", value: { description } },
    ];
}

function actionRecord(nextId, name, description, effects = [], type = "", subtype = "") {
    return {
        id: nextId(`action:${name}`),
        type,
        subtype,
        displayName: name,
        version: 2,
        privacy: { level: "private", users: [] },
        effects,
        details: actionDetails(description),
        ready: false,
    };
}

function weaponAction(character, item, nextId) {
    const reference = referenceLine(item);
    const attackBonus = integerOrZero(character.combat?.attack);
    const details = [
        `Weapon Type: ${item.gearType || "Unresolved"}`,
        `Attack Bonus: ${attackBonus >= 0 ? "+" : ""}${attackBonus}`,
        reference,
        "Complete this weapon Action in Questline.",
    ].filter(Boolean).join("\n");
    const rollEffect = {
        name: item.name,
        hide: false,
        quantity: 1,
        bonus: 0,
        advantageType: "none",
        bonusRoll: "",
        baseRoll: "1d20",
        type: "roll",
        encounterRoll: false,
        modifiers: [{
            operator: "add",
            linkedValue: "attack-bonus.attributes.attack-bonus.value.value",
        }],
        useModifiers: true,
        selectedDie: "d20",
    };
    return actionRecord(nextId, item.name, details, [rollEffect], "Weapons");
}

function featureRecords(character, nextId) {
    const records = [];
    const addFeature = (feature, source, detail) => {
        if (!feature?.name) return;
        const record = featureRecord(nextId, feature, source, detail);
        records.push(record);
    };

    (character.abilities?.calling ?? []).forEach((feature) => addFeature(feature, "Calling", "Starting"));
    (character.abilities?.species ?? []).forEach((feature) => addFeature(feature, "Species", "Innate"));
    if (character.abilities?.prodigy) addFeature(character.abilities.prodigy, "Calling", "Prodigy");
    (character.abilities?.elective ?? []).forEach((feature) => addFeature(feature, feature.tier === "Maturative" ? "Species" : "Calling", "Elective"));
    if (character.quirk?.name) addFeature(character.quirk, "Quirk", character.quirk.category);
    (character.additionalQuirks ?? []).forEach((quirk) => addFeature(quirk, "Quirk", "Additional"));
    return records;
}

function giftRecord(nextId, selection, index) {
    const value = String(selection.value ?? "");
    const match = value.match(/^(Bright|Dark):\s*(.*)$/);
    const name = match?.[2] || value;
    const alignment = match?.[1] || "";
    const details = [referenceLine(selection), alignment ? `${alignment} Allegiance Gift` : "Gift"]
        .filter(Boolean)
        .join("\n");
    return {
        id: nextId(`gift:${index}:${name}`),
        originId: null,
        type: alignment ? "Allegiance Gift" : "Gift",
        name,
        description: details,
        subtext: alignment,
        value: 0,
        valuePrefix: null,
        valueSuffix: null,
        bonus: 0,
        linkedValue: null,
        starValue: null,
        counters: {},
        counterOverrides: {},
        modifiers: [],
        modifiersPostCalculationFunc: null,
        rollDetails: [],
    };
}

function giftRecords(character, nextId) {
    return (character.selections ?? [])
        .filter((selection) => /gift/i.test(selection.label) && selection.value)
        .map((selection, index) => giftRecord(nextId, selection, index));
}

function inventoryItem(item, section, index, nextId, action = null) {
    const quantity = parseQuantity(item);
    const unitSlots = itemUnitSlots(item, quantity);
    const nickname = item.nickname ? ` (${item.nickname})` : "";
    const description = [
        item.nickname ? `Nickname: ${item.nickname}` : "",
        referenceLine(item),
        item.costRate ? `Cost rate: ${item.costRate}` : "",
    ].filter(Boolean).join("\n");
    return {
        id: nextId(`inventory:${section}:${index}:${item.name}`),
        itemId: nextId(`inventory-item:${section}:${index}:${item.name}`),
        name: `${item.name}${nickname}`,
        description,
        type: "none",
        privacy: { level: "public", users: [] },
        creator: "",
        data: {
            type: "Gear",
            subtype: item.category || item.gearType || "Generated",
            encumbrance: unitSlots / 10,
            cost: currencyFromStones(itemUnitCost(item, quantity)),
        },
        version: 0,
        owners: [],
        quantity,
        equipped: !item.equipped,
        isCustom: true,
        actions: action ? [action] : [],
    };
}

function allegiancePoints(character) {
    const points = { bright: 0, dark: 0 };
    (character.modifiers?.combat?.allegiance ?? []).forEach((modifier) => {
        const alignment = modifier.alignment === "Light" ? "bright" : modifier.alignment?.toLowerCase();
        if (alignment === "bright" || alignment === "dark") points[alignment] += integerOrZero(modifier.amount);
    });
    if (points.bright || points.dark) return points;
    for (const match of String(character.allegiance ?? "").matchAll(/(\d+)\s+(Bright|Dark)/g)) {
        points[match[2].toLowerCase()] = Number(match[1]);
    }
    return points;
}

function aptitudeData(character, aptitude) {
    const bonusParts = [];
    const bonusNames = [];
    (character.traits ?? []).filter((trait) => trait.aptitude === aptitude).forEach((trait) => {
        bonusParts.push(integerOrZero(trait.amount));
        bonusNames.push("Trait");
    });
    (character.modifiers?.aptitudes?.[aptitude] ?? []).forEach((modifier) => {
        bonusParts.push(integerOrZero(modifier.amount));
        bonusNames.push(modifier.source);
    });
    const result = {
        value: String(integerOrZero(character.aptitudes?.[aptitude])),
        visible: true,
    };
    if (bonusParts.length) {
        const useExplicitPositiveSign = bonusParts.length > 1;
        result.bonusValue = bonusParts.map((amount) => `${useExplicitPositiveSign && amount > 0 ? "+" : ""}${amount}`).join("/");
    }
    result.bonusText = bonusNames.length ? bonusNames.join(", ") : ".";
    return result;
}

function alignmentArea(points) {
    let selected = "none";
    if (points.bright + points.dark > 1) {
        if (points.bright > points.dark + 1) selected = "bright";
        else if (points.dark > points.bright + 1) selected = "dark";
        else selected = "twilight";
    }
    return Object.fromEntries(["bright", "twilight", "none", "dark"].map((key) => [key, {
        value: key === selected ? 1 : 0,
        visible: true,
    }]));
}

function resolvedChoicesText(character) {
    const choices = (character.selections ?? []).map((selection) => {
        const reference = formatReference(selection);
        return `- ${selection.label}: ${selection.value}${reference ? ` (${reference})` : ""}`;
    });
    if (character.additionalHistory) {
        const reference = formatReference(character.additionalHistory);
        choices.push(`- Additional History: ${character.additionalHistory.name} [${character.additionalHistory.tier}]${reference ? ` (${reference})` : ""}`);
    }
    return choices.length ? choices.join("\n") : "- None recorded";
}

function buildBackground(character) {
    return [
        `Rank: ${character.rank}`,
        `Size: ${character.size.name}${formatReference(character.size) ? ` (${formatReference(character.size)})` : ""}`,
        "Resolved Choices:",
        resolvedChoicesText(character),
    ].join("\n\n");
}

function buildCharacterSystem(character, points, features, items, gifts, advancement) {
    const aptitudeValues = Object.fromEntries(APTITUDES.map((aptitude) => [aptitude, aptitudeData(character, aptitude)]));
    const attack = integerOrZero(character.combat.attack);
    const hearts = Math.max(1, integerOrZero(character.combat.hearts));
    const defense = integerOrZero(character.combat.defense);
    const inventory = Math.max(0, Math.round(numberOrZero(character.combat.inventory)));
    const rank = Math.max(1, Math.min(10, integerOrZero(character.rank) || 1));
    const currentXp = integerOrZero(advancement?.xp);
    const nextAdvancement = advancement?.next;
    const nextXp = nextAdvancement ? Math.max(0, integerOrZero(nextAdvancement.xp) - currentXp) : 0;
    const currency = currencyFromStones(character.shopping?.totalCurrencyStones ?? character.coins * 100);
    return {
        "rank-and-xp": {
            attributes: {
                "rank-and-xp": {
                    "next-xp": { value: nextXp, visible: true },
                    rank: { value: String(rank), visible: true },
                    "current-xp": { value: currentXp, visible: true },
                },
            },
        },
        bio: {
            purviews: "",
            tokenCrop: "",
            subname: character.calling.name,
            profileImage: null,
            homeland: character.homeland.name,
            species: character.species.name,
            details: `${character.history.name} [${character.history.tier}]${formatReference(character.history) ? ` (${formatReference(character.history)})` : ""}`,
            languages: (character.languages ?? []).join(", "),
            characteristics: {
                hair: "",
                weight: "",
                eyes: "",
                skin: "",
                height: "",
                gender: "",
                age: "",
            },
            name: character.name,
            appearance: "",
            background: buildBackground(character),
        },
        aptitudes: { attributes: { aptitudes: aptitudeValues } },
        "attack-bonus": {
            attributes: {
                "attack-bonus": { value: { visible: true, value: String(attack) } },
            },
        },
        hearts: {
            max: hearts,
            temp: 0,
            current: hearts,
            showTokenMeter: true,
            tempMax: 0,
        },
        "defense-rating": {
            attributes: {
                "defense-rating": { value: { value: String(defense), visible: true } },
            },
        },
        "speed-rating": {
            attributes: {
                "speed-rating": { value: { visible: true, value: String(speedValue(character.combat.speed)) } },
            },
        },
        allegiance: {
            attributes: {
                allegiance: {
                    "dark-points": { value: String(points.dark), visible: true },
                    "bright-points": { value: String(points.bright), visible: true },
                },
            },
        },
        "allegiance-area": { attributes: { alignment: alignmentArea(points) } },
        "quirk-and-abilities": features,
        actions: [],
        gifts,
        inventory: {
            currency,
            items,
            maxEncumbrance: inventory,
        },
        conditions: [],
    };
}

function actorSeed(character) {
    return `${character.name}:${JSON.stringify(character.seeds ?? {})}`;
}

function findAdvancement(data, character) {
    const calling = [...(data.callings ?? []), ...(data.expandedCallings ?? [])]
        .find((entry) => entry.name === character.calling.name);
    const progressionName = calling?.baseCalling || character.calling.name;
    const table = data.advancementTables?.[progressionName] ?? [];
    const rank = Math.max(1, Math.min(10, integerOrZero(character.rank) || 1));
    return { current: table[rank - 1] || {}, next: table[rank] || null };
}

function buildQuestlineCharacter(character, data, options = {}) {
    if (!character || !data) throw new TypeError("A generated character and generator data are required");
    const nextId = createIdFactory(actorSeed(character));
    const advancement = findAdvancement(data, character);
    const features = featureRecords(character, nextId);
    const giftData = giftRecords(character, nextId);
    const gearEntries = [
        ...(character.gear ?? []).filter((item) => !isCurrencyItem(item)).map((item, index) => ({ item, section: "starting", index })),
        ...(character.purchasedGear ?? []).filter((item) => !isCurrencyItem(item)).map((item, index) => ({ item, section: "purchased", index })),
    ];
    const gearItems = gearEntries.map(({ item, section, index }) => inventoryItem(
        item,
        section,
        index,
        nextId,
        item.gearCategory === "weapons" ? weaponAction(character, item, nextId) : null,
    ));
    const points = allegiancePoints(character);
    const system = buildCharacterSystem(character, points, features, gearItems, giftData, advancement.current);
    const entityId = nextId("character");
    const packageId = stableUuid(actorSeed(character));
    const entity = {
        baseScale: 1,
        privacy: { level: "public", users: [] },
        groups: [],
        version: 9,
        sheetData: system,
        isActive: true,
        id: entityId,
        name: character.name,
        activeSheet: QUESTLINE_PLAYER_SHEET_ID,
        image: { tokenCrop: blankTokenCrop(), url: null },
    };
    const manifest = {
        version: 1,
        format: "questline-package",
        type: "characters",
        packageId,
        packageVersion: 1,
        exportedAt: options.exportedAt || new Date().toISOString(),
        gameType: {
            id: "UOi6Buh2UBoj7ZaBo6iH",
            name: "BREAK!! [Official]",
        },
        totalAssetSize: 0,
        package: {
            name: `${character.name} - BREAK!! Character`,
            description: "",
            publisher: "Studio Quagg",
            tags: [],
            price: 0,
            license: "",
        },
        assetMap: {},
    };
    const entities = { characters: [entity] };
    return {
        manifest,
        entities,
        files: {
            "manifest.json": `${JSON.stringify(manifest, null, 2)}\n`,
            "entities.json": `${JSON.stringify(entities, null, 2)}\n`,
        },
        entity,
    };
}

function writeUint16(target, offset, value) {
    target[offset] = value & 0xff;
    target[offset + 1] = (value >>> 8) & 0xff;
}

function writeUint32(target, offset, value) {
    target[offset] = value & 0xff;
    target[offset + 1] = (value >>> 8) & 0xff;
    target[offset + 2] = (value >>> 16) & 0xff;
    target[offset + 3] = (value >>> 24) & 0xff;
}

const CRC_TABLE = Array.from({ length: 256 }, (_, index) => {
    let value = index;
    for (let bit = 0; bit < 8; bit += 1) value = value & 1 ? 0xedb88320 ^ (value >>> 1) : value >>> 1;
    return value >>> 0;
});

function crc32(bytes) {
    let value = 0xffffffff;
    for (const byte of bytes) value = CRC_TABLE[(value ^ byte) & 0xff] ^ (value >>> 8);
    return (value ^ 0xffffffff) >>> 0;
}

function joinBytes(chunks) {
    const totalLength = chunks.reduce((total, chunk) => total + chunk.length, 0);
    const result = new Uint8Array(totalLength);
    let offset = 0;
    chunks.forEach((chunk) => {
        result.set(chunk, offset);
        offset += chunk.length;
    });
    return result;
}

function zipEntry(name, content, offset, encoder) {
    const nameBytes = encoder.encode(name);
    const dataBytes = typeof content === "string" ? encoder.encode(content) : content;
    const checksum = crc32(dataBytes);
    const localHeader = new Uint8Array(30 + nameBytes.length);
    writeUint32(localHeader, 0, 0x04034b50);
    writeUint16(localHeader, 4, 20);
    writeUint16(localHeader, 6, 0x0800);
    writeUint16(localHeader, 8, 0);
    writeUint16(localHeader, 10, 0);
    writeUint16(localHeader, 12, 0);
    writeUint32(localHeader, 14, checksum);
    writeUint32(localHeader, 18, dataBytes.length);
    writeUint32(localHeader, 22, dataBytes.length);
    writeUint16(localHeader, 26, nameBytes.length);
    writeUint16(localHeader, 28, 0);
    localHeader.set(nameBytes, 30);

    const centralHeader = new Uint8Array(46 + nameBytes.length);
    writeUint32(centralHeader, 0, 0x02014b50);
    writeUint16(centralHeader, 4, 20);
    writeUint16(centralHeader, 6, 20);
    writeUint16(centralHeader, 8, 0x0800);
    writeUint16(centralHeader, 10, 0);
    writeUint16(centralHeader, 12, 0);
    writeUint16(centralHeader, 14, 0);
    writeUint32(centralHeader, 16, checksum);
    writeUint32(centralHeader, 20, dataBytes.length);
    writeUint32(centralHeader, 24, dataBytes.length);
    writeUint16(centralHeader, 28, nameBytes.length);
    writeUint16(centralHeader, 30, 0);
    writeUint16(centralHeader, 32, 0);
    writeUint16(centralHeader, 34, 0);
    writeUint16(centralHeader, 36, 0);
    writeUint32(centralHeader, 38, 0);
    writeUint32(centralHeader, 42, offset);
    centralHeader.set(nameBytes, 46);
    return { local: joinBytes([localHeader, dataBytes]), central: centralHeader };
}

export function createZip(files) {
    const encoder = new TextEncoder();
    const localChunks = [];
    const centralChunks = [];
    let offset = 0;
    Object.entries(files).forEach(([name, content]) => {
        const entry = zipEntry(name, content, offset, encoder);
        localChunks.push(entry.local);
        centralChunks.push(entry.central);
        offset += entry.local.length;
    });
    const localData = joinBytes(localChunks);
    const centralData = joinBytes(centralChunks);
    const endRecord = new Uint8Array(22);
    writeUint32(endRecord, 0, 0x06054b50);
    writeUint16(endRecord, 4, 0);
    writeUint16(endRecord, 6, 0);
    writeUint16(endRecord, 8, centralChunks.length);
    writeUint16(endRecord, 10, centralChunks.length);
    writeUint32(endRecord, 12, centralData.length);
    writeUint32(endRecord, 16, localData.length);
    writeUint16(endRecord, 20, 0);
    return joinBytes([localData, centralData, endRecord]);
}

export function buildQuestlinePackage(character, data, options = {}) {
    const packageData = buildQuestlineCharacter(character, data, options);
    return {
        ...packageData,
        zip: createZip(packageData.files),
    };
}

function safeFileName(name) {
    const baseName = String(name || "break-character")
        .replace(/[^a-z0-9]+/gi, "-")
        .replace(/^-+|-+$/g, "")
        .toLowerCase();
    return `${baseName || "break-character"}.characters`;
}

export function downloadQuestlineCharacter(character, data) {
    const packageData = buildQuestlinePackage(character, data);
    if (typeof document === "undefined" || typeof Blob === "undefined" || typeof URL === "undefined" || typeof URL.createObjectURL !== "function") {
        throw new Error("Questline export downloads require a browser");
    }
    const blob = new Blob([packageData.zip], { type: "application/zip" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = safeFileName(character.name);
    link.hidden = true;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 0);
    return packageData;
}

export { buildQuestlineCharacter, currencyFromStones, safeFileName };