import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { rollCharacter } from "./generator.mjs";
import { buildFoundryActor, currencyFromStones } from "./foundry-export.mjs";

const data = JSON.parse(await readFile(new URL("./data.json", import.meta.url), "utf8"));
const allowedItemTypes = new Set([
    "accessory", "ability", "armor", "calling", "gift", "history", "homeland",
    "item", "outfit", "quirk", "shield", "species", "weapon",
]);

function seededRandom(seed) {
    let state = seed >>> 0;
    return () => {
        state = (state * 1664525 + 1013904223) >>> 0;
        return state / 4294967296;
    };
}

function equipmentReferences(actor) {
    return Object.values(actor.system.equipment).flatMap((value) => Array.isArray(value) ? value : value ? [value] : []);
}

function validateActor(character) {
    const actor = buildFoundryActor(character, data);
    const repeated = buildFoundryActor(character, data);
    const itemIds = new Set(actor.items.map((item) => item._id));
    const references = equipmentReferences(actor);
    const advancementName = data.callings.concat(data.expandedCallings ?? [])
        .find((calling) => calling.name === character.calling.name)?.baseCalling || character.calling.name;
    const advancement = data.advancementTables[advancementName][character.rank - 1];
    const callingItem = actor.items.find((item) => item.type === "calling");

    assert.deepEqual(actor, repeated);
    assert.equal(actor.type, "character");
    assert.equal(actor._id.length, 16);
    assert.equal(actor.system.xp.rank, character.rank);
    assert.equal(actor.system.xp.current, advancement.xp);
    assert.equal(actor.flags["break-random-character"].exportVersion, 2);
    assert.equal(callingItem.system.advancementTable.length, data.advancementTables[advancementName].length + (character.rank === 10 ? 1 : 0));
    if (character.rank === 10) assert.equal(callingItem.system.advancementTable.at(-1).xp, advancement.xp + 1);
    assert.deepEqual(actor.system.currency, currencyFromStones(character.shopping.totalCurrencyStones));
    assert.ok(Array.isArray(actor.system.languages));
    assert.deepEqual(actor.system.languages, character.languages);
    assert.equal(actor.system.size.value, { Tiny: 0, Small: 1, Medium: 2, Large: 3, Massive: 4, Colossal: 5 }[character.size.name]);
    assert.equal(actor.flags["break-random-character"].generatorSchemaVersion, data.schemaVersion);
    assert.deepEqual(actor.flags["break-random-character"].seeds, character.seeds);
    assert.equal(actor.system.description, "");
    assert.deepEqual(actor._stats, {
        coreVersion: "14.367",
        systemId: "break",
        systemVersion: "1.3",
    });
    assert.equal(actor.prototypeToken.depth, 1);
    const capacityChanges = actor.items.flatMap((item) => item.effects).flatMap((effect) => effect.changes)
        .filter((change) => change.key === "system.slots.total");
    assert.equal(capacityChanges.length, 1);
    assert.equal(capacityChanges[0].type, "override");
    assert.equal(capacityChanges[0].phase, "final");
    const physicalContainerBonus = (character.modifiers.combat.inventory ?? [])
        .filter((modifier) => modifier.kind === "gear")
        .reduce((total, modifier) => total + modifier.amount, 0)
        + actor.items
            .filter((item) => item.flags["break-random-character"]?.synthetic)
            .reduce((total, item) => total + item.system.container.capacity, 0);
    assert.equal(Number(capacityChanges[0].value), character.combat.inventory - physicalContainerBonus);
    const inventorySlotChanges = actor.items.flatMap((item) => item.effects).flatMap((effect) => effect.changes)
        .filter((change) => change.key === "system.inventorySlots");
    assert.equal(inventorySlotChanges.length, 1);
    assert.equal(inventorySlotChanges[0].type, "override");
    assert.equal(inventorySlotChanges[0].phase, "final");
    assert.equal(Number(inventorySlotChanges[0].value), character.combat.inventory - physicalContainerBonus);
    const rank10GuardChanges = actor.items.flatMap((item) => item.effects).flatMap((effect) => effect.changes)
        .filter((change) => change.key === "system.xpNextRank");
    assert.equal(rank10GuardChanges.length, character.rank === 10 ? 1 : 0);
    if (character.rank === 10) {
        assert.equal(rank10GuardChanges[0].type, "override");
        assert.equal(rank10GuardChanges[0].phase, "final");
        assert.equal(Number(rank10GuardChanges[0].value), 0);
    }
    assert.equal(actor.system.hearts.value, character.combat.hearts);
    const expectedHeartChanges = (character.modifiers.combat.hearts ?? [])
        .map((modifier) => ({ key: "system.hearts.max", value: String(modifier.amount) }))
        .sort((left, right) => left.value.localeCompare(right.value));
    const actualHeartChanges = actor.items.flatMap((item) => item.effects).flatMap((effect) => effect.changes)
        .filter((change) => change.key === "system.hearts.max")
        .map((change) => ({ key: change.key, value: change.value }))
        .sort((left, right) => left.value.localeCompare(right.value));
    assert.deepEqual(actualHeartChanges, expectedHeartChanges);
    const speciesItem = actor.items.find((item) => item.type === "species");
    const expectedSpeciesChanges = [
        ...Object.entries(character.modifiers.aptitudes).flatMap(([aptitude, modifiers]) => modifiers
            .filter((modifier) => modifier.kind === "species")
            .map((modifier) => ({ key: `system.aptitudes.${aptitude}.value`, value: String(modifier.amount) }))),
        ...(character.modifiers.combat.defense ?? [])
            .filter((modifier) => modifier.kind === "species")
            .map((modifier) => ({ key: "system.defense.value", value: String(modifier.amount) })),
    ].sort((left, right) => left.key.localeCompare(right.key) || left.value.localeCompare(right.value));
    const actualSpeciesChanges = speciesItem.effects.flatMap((effect) => effect.changes)
        .filter((change) => change.key.startsWith("system.aptitudes.") || change.key === "system.defense.value")
        .map((change) => ({ key: change.key, value: change.value }))
        .sort((left, right) => left.key.localeCompare(right.key) || left.value.localeCompare(right.value));
    assert.deepEqual(actualSpeciesChanges, expectedSpeciesChanges);
    assert.ok(!actor.system.notes.includes("Generated by the Studio Quagg BREAK!! Random Character tool."));
    assert.ok(actor.system.notes.includes("Resolved choices"));
    assert.equal(new Set(actor.items.map((item) => item._id)).size, actor.items.length);

    for (const item of actor.items) {
        assert.ok(allowedItemTypes.has(item.type), `Unexpected Item type: ${item.type}`);
        assert.equal(item.system.description, "");
        if ("actions" in item.system) assert.ok(Array.isArray(item.system.actions));
        assert.equal(item._stats, undefined);
        assert.equal(item._uuid, undefined);
        assert.equal(item.ownership, undefined);
        assert.equal(item.system.containerId, item.flags["break-random-character"]?.containerId ?? null);
        assert.equal(item.system.aptitudes, undefined);
        if (["armor", "accessory"].includes(item.type)) {
            assert.ok(item.system.container);
            assert.deepEqual(item.system.container.allowedItemTypes, []);
            assert.deepEqual(item.system.container.allowedItemCategories, []);
        }
        if (item.system.containerId) {
            const container = actor.items.find((candidate) => candidate._id === item.system.containerId);
            assert.ok(container?.system.container?.enabled, `${item.name} references a non-container item`);
            assert.notEqual(item._id, container._id);
        }
        for (const effect of item.effects) {
            assert.ok(effect._id.length === 16);
            assert.ok(effect.changes.every((change) => ["add", "override"].includes(change.type)));
        }
    }

    for (const aptitude of ["might", "deftness", "grit", "insight", "aura"]) {
        const expectedTrait = character.traits
            .filter((trait) => trait.aptitude === aptitude)
            .reduce((total, trait) => total + trait.amount, 0);
        assert.equal(actor.system.aptitudes[aptitude].trait, expectedTrait);
    }

    for (const reference of references) {
        assert.ok(itemIds.has(reference._id), `${reference.name} is not embedded in items`);
        const item = actor.items.find((candidate) => candidate._id === reference._id);
        assert.equal(reference.type, item.type);
        assert.deepEqual(reference.system, item.system);
    }

    return actor;
}

validateActor(rollCharacter(data, seededRandom(0xC0FFEE), {}, "core", 0, false, 1));
validateActor(rollCharacter(data, seededRandom(0xB4EA5), {}, "expanded", 75, true, 10));
validateActor(rollCharacter(data, seededRandom(1), {}, "expanded", 0, false, 1));
validateActor(rollCharacter(data, seededRandom(5), {}, "expanded", 0, false, 1));
validateActor(rollCharacter(data, seededRandom(7), {}, "expanded", 0, false, 1));
validateActor(rollCharacter(data, seededRandom(15), {}, "core", 0, false, 10));
validateActor(rollCharacter(data, seededRandom(3), {}, "expanded", 0, false, 10));

let specialWeaponCharacter;
for (let seed = 1; seed <= 5000 && !specialWeaponCharacter; seed += 1) {
    const character = rollCharacter(data, seededRandom(seed), {}, "expanded", 0, false, 10);
    const actor = buildFoundryActor(character, data);
    if (actor.items.some((item) => item.flags["break-random-character"]?.specialChoice)) specialWeaponCharacter = actor;
}
assert.ok(specialWeaponCharacter);
assert.ok(specialWeaponCharacter.system.equipment.weapon.some((item) => item.flags["break-random-character"]?.specialChoice));

const backpackCharacter = rollCharacter(data, seededRandom(2), {}, "expanded", 75, true, 1);
const backpackActor = buildFoundryActor(backpackCharacter, data);
const backpack = backpackActor.items.find((item) => item.name === "Backpack");
assert.ok(backpack);
assert.deepEqual(backpack.system.container, {
    enabled: true,
    capacity: 5,
    accessCost: 2,
    allowedItemTypes: [],
    allowedItemCategories: [],
});
assert.equal(backpack.system.containerId, null);
const backpackSlotEffects = backpack.effects.flatMap((effect) => effect.changes)
    .filter((change) => change.key === "system.slots.value");
assert.equal(backpackSlotEffects.length, 0);
const packedBackpackItems = backpackActor.items.filter((item) => item.system.containerId === backpack._id);
assert.ok(packedBackpackItems.length > 0);
assert.ok(packedBackpackItems.reduce((total, item) => total + item.system.slots * item.system.quantity, 0) <= backpack.system.container.capacity);
const capacityChanges = backpackActor.items.flatMap((item) => item.effects).flatMap((effect) => effect.changes)
    .filter((change) => change.key === "system.slots.total");
assert.equal(capacityChanges.length, 1);
const backpackPhysicalContainerBonus = backpackCharacter.modifiers.combat.inventory
    .filter((modifier) => modifier.kind === "gear")
    .reduce((total, modifier) => total + modifier.amount, 0);
assert.equal(Number(capacityChanges[0].value), backpackCharacter.combat.inventory - backpackPhysicalContainerBonus);

const travelerCharacter = rollCharacter(data, seededRandom(1), {}, "expanded", 75, true, 1);
const travelerActor = buildFoundryActor(travelerCharacter, data);
const travelerBag = travelerActor.items.find((item) => item.name === "Traveler's Bag");
assert.ok(travelerBag);
assert.deepEqual(travelerBag.system.container, {
    enabled: true,
    capacity: 3,
    accessCost: 1,
    allowedItemTypes: [],
    allowedItemCategories: [],
});
assert.equal(travelerBag.system.containerId, null);
assert.equal(travelerBag.effects.flatMap((effect) => effect.changes)
    .filter((change) => change.key === "system.slots.value").length, 0);
const packedTravelerItems = travelerActor.items.filter((item) => item.system.containerId === travelerBag._id);
assert.equal(packedTravelerItems.find((item) => item.name === travelerCharacter.equippedOutfit), undefined);
assert.ok(packedTravelerItems.reduce((total, item) => total + item.system.slots * item.system.quantity, 0) <= travelerBag.system.container.capacity);

const uncategorizedTravelerCharacter = rollCharacter(data, seededRandom(6), {}, "expanded", 0, false, 1);
const uncategorizedTravelerActor = buildFoundryActor(uncategorizedTravelerCharacter, data);
const uncategorizedTravelerBag = uncategorizedTravelerActor.items.find((item) => item.name === "Traveler's Bag");
assert.ok(uncategorizedTravelerBag);
assert.equal(uncategorizedTravelerBag.type, "accessory");
assert.deepEqual(uncategorizedTravelerBag.system.container, travelerBag.system.container);
assert.ok(uncategorizedTravelerActor.system.equipment.accessory.some((item) => item._id === uncategorizedTravelerBag._id));

const noContainerCharacter = rollCharacter(data, seededRandom(1), {}, "expanded", 0, false, 1);
const noContainerActor = buildFoundryActor(noContainerCharacter, data);
assert.equal(noContainerActor.items.filter((item) => item.system.container?.enabled).length, 0);
assert.equal(noContainerActor.items.filter((item) => item.system.containerId).length, 0);

const factotumCharacter = rollCharacter(data, seededRandom(8), {}, "expanded", 75, true, 1);
const factotumActor = buildFoundryActor(factotumCharacter, data);
const factotumPack = factotumActor.items.find((item) => item.name === "Factotum's Pack" && item.type === "accessory");
assert.ok(factotumPack);
assert.deepEqual(factotumPack.system.container, {
    enabled: true,
    capacity: 8,
    accessCost: 1,
    allowedItemTypes: [],
    allowedItemCategories: [],
});
assert.equal(factotumPack.system.containerId, null);
const packedFactotumItems = factotumActor.items.filter((item) => item.system.containerId === factotumPack._id);
assert.ok(packedFactotumItems.length > 0);
assert.ok(packedFactotumItems.reduce((total, item) => total + item.system.slots * item.system.quantity, 0) <= factotumPack.system.container.capacity);
const factotumCapacity = factotumActor.items.flatMap((item) => item.effects).flatMap((effect) => effect.changes)
    .filter((change) => change.key === "system.slots.total");
assert.equal(factotumCapacity.length, 1);
assert.equal(Number(factotumCapacity[0].value), factotumCharacter.combat.inventory - factotumPack.system.container.capacity);
const factotumBonusEffects = factotumPack.effects.flatMap((effect) => effect.changes)
    .filter((change) => change.key === "system.slots.value");
assert.equal(factotumBonusEffects.length, 0);

const largeMechanicalCharacter = rollCharacter(data, seededRandom(20), {}, "expanded", 75, true, 1);
const largeMechanicalActor = buildFoundryActor(largeMechanicalCharacter, data);
const largeMechanicalWeapons = largeMechanicalActor.items.filter((item) => item.system.weaponType1 === "mechanicalLarge");
assert.ok(largeMechanicalWeapons.length > 0);
for (const weapon of largeMechanicalWeapons) {
    assert.equal(weapon.system.ranged, true);
    assert.equal(weapon.system.melee, false);
    assert.equal(weapon.system.rangedExtraDamage, weapon.system.extraDamage);
}

const masterCharacter = rollCharacter(data, seededRandom(108), {}, "core", 0, false, 10);
const masterActor = buildFoundryActor(masterCharacter, data);
const masterWeapons = masterActor.items.filter((item) => item.system.weaponType1 === "master");
assert.ok(masterWeapons.length > 0);
for (const weapon of masterWeapons) assert.equal(weapon.system.attackBonus, 1);

const brazenCharacter = rollCharacter(data, seededRandom(1236), {}, "core", 0, false, 10);
const brazenActor = buildFoundryActor(brazenCharacter, data);
const brazenArmor = brazenActor.items.find((item) => item.type === "armor");
assert.equal(brazenArmor.system.defenseBonus, 2);
const armorReplacementChanges = brazenActor.items.flatMap((item) => item.effects).flatMap((effect) => effect.changes)
    .filter((change) => change.key === "system.equipment.armor.system.defenseBonus");
assert.equal(armorReplacementChanges.length, 1);
assert.equal(armorReplacementChanges[0].type, "override");
assert.equal(armorReplacementChanges[0].value, "0");

const bulwarkCharacter = rollCharacter(data, seededRandom(49), {}, "core", 0, false, 9);
const bulwarkActor = buildFoundryActor(bulwarkCharacter, data);
const bulwarkArmorReplacementChanges = bulwarkActor.items.flatMap((item) => item.effects).flatMap((effect) => effect.changes)
    .filter((change) => change.key === "system.equipment.armor.system.defenseBonus");
assert.equal(bulwarkArmorReplacementChanges.length, 1);
assert.equal(bulwarkArmorReplacementChanges[0].type, "override");
assert.equal(bulwarkArmorReplacementChanges[0].value, "0");

const stowingCharacter = rollCharacter(data, seededRandom(22), {}, "core", 75, false, 9);
const stowingActor = buildFoundryActor(stowingCharacter, data);
const stowedItem = stowingActor.items.find((item) => item.flags["break-random-character"]?.stowed);
assert.ok(stowedItem);
assert.equal(stowedItem.system.slots, 0);
assert.equal(stowedItem.flags["break-random-character"].unitSlotTenths, 10);

const companionCharacter = rollCharacter(data, seededRandom(15), {}, "core", 0, false, 5);
assert.ok(companionCharacter.selections.find((selection) => selection.label === "Soul Companion").value.includes("+1 Heart"));
assert.equal(companionCharacter.modifiers.combat.hearts.some((modifier) => modifier.source === "Soul Companion"), false);
const companionActor = buildFoundryActor(companionCharacter, data);
assert.equal(companionActor.items.flatMap((item) => item.effects).flatMap((effect) => effect.changes)
    .filter((change) => change.key === "system.hearts.max").length, 0);

console.log("Foundry export checks passed");