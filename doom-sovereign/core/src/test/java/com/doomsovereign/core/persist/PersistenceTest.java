package com.doomsovereign.core.persist;

import com.doomsovereign.core.analysis.AnalysisLedger;
import com.doomsovereign.core.analysis.ObservationMethod;
import com.doomsovereign.core.analysis.ProfileRegistry;
import com.doomsovereign.core.api.ResearchEvent;
import com.doomsovereign.core.api.SecurityIdentity;
import com.doomsovereign.core.bot.BotLocation;
import com.doomsovereign.core.bot.BotOrder;
import com.doomsovereign.core.module.Loadout;
import com.doomsovereign.core.module.ModuleCatalog;
import com.doomsovereign.core.research.DoomResearch;
import com.doomsovereign.core.research.ResearchProgress;
import com.doomsovereign.core.research.ResearchTree;
import com.doomsovereign.core.security.AccessPolicy;
import com.doomsovereign.core.security.DeviceKind;
import com.doomsovereign.core.security.Permission;
import com.doomsovereign.core.suit.DoomSuit;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.util.List;
import java.util.Random;
import java.util.Set;
import java.util.UUID;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class PersistenceTest {
    static final ModuleCatalog CAT = ModuleCatalog.standard();
    static final ResearchTree TREE = DoomResearch.standard();
    static final ProfileRegistry PROFILES = ProfileRegistry.loadDefaults();
    static final UUID PLAYER = UUID.fromString("0f0e0d0c-0b0a-4908-8706-050403020100");

    static JsonObject reparse(JsonObject o) {
        return JsonParser.parseString(o.toString()).getAsJsonObject();
    }

    static PlayerDoomData sample() {
        PlayerDoomData p = new PlayerDoomData();
        p.player = PLAYER;
        p.energy = 12_345;
        p.lastDrainTick = 999;
        p.heat = 42.5;
        p.heatLocked = true;
        p.everInitialised = true;
        p.frame = "royal_mk2";
        p.modules = List.of("thermal_management", "capacitor_standard");
        p.cooldowns.put("bolt", new long[]{0, 1234});
        p.focus = 61.25;
        p.researchCounters.put("SAMPLE_COLLECTED|minecraft:quartz", 8);
        p.researchCompleted.add("latverian_metallurgy");
        p.researchActive = "doom_engineering";
        p.researchActiveTicks = 17;
        PlayerDoomData.AnalysisRecord r = new PlayerDoomData.AnalysisRecord();
        r.knowledge = 37.5;
        r.counts.put("SCAN", 3);
        r.revealed.add("vitals");
        r.countermeasures.add("counter:coolant_bolts");
        p.analysis.put("minecraft:blaze", r);
        p.sovereign = true;
        p.sovereignSince = 24_000;
        p.title = "Monarch of Latveria";
        p.waypoints.add(new PlayerDoomData.Waypoint("Castle Doom", "minecraft:overworld", 799.5, 70, -10090.5));
        return p;
    }

    static void assertSame(PlayerDoomData a, PlayerDoomData b) {
        assertEquals(a.player, b.player);
        assertEquals(a.energy, b.energy);
        assertEquals(a.lastDrainTick, b.lastDrainTick);
        assertEquals(a.heat, b.heat);
        assertEquals(a.heatLocked, b.heatLocked);
        assertEquals(a.everInitialised, b.everInitialised);
        assertEquals(a.frame, b.frame);
        assertEquals(a.modules, b.modules);
        assertEquals(a.cooldowns.keySet(), b.cooldowns.keySet());
        a.cooldowns.forEach((k, v) -> assertArrayEquals(v, b.cooldowns.get(k)));
        assertEquals(a.focus, b.focus);
        assertEquals(a.researchCounters, b.researchCounters);
        assertEquals(a.researchCompleted, b.researchCompleted);
        assertEquals(a.researchActive, b.researchActive);
        assertEquals(a.researchActiveTicks, b.researchActiveTicks);
        assertEquals(a.analysis.keySet(), b.analysis.keySet());
        a.analysis.forEach((k, r) -> {
            PlayerDoomData.AnalysisRecord s = b.analysis.get(k);
            assertEquals(r.knowledge, s.knowledge);
            assertEquals(r.counts, s.counts);
            assertEquals(r.revealed, s.revealed);
            assertEquals(r.countermeasures, s.countermeasures);
        });
        assertEquals(a.sovereign, b.sovereign);
        assertEquals(a.sovereignSince, b.sovereignSince);
        assertEquals(a.title, b.title);
        assertEquals(a.waypoints, b.waypoints);
        assertEquals(a.extra, b.extra);
    }

    // ---- player documents ------------------------------------------------------------------------------
    @Test
    void playerDataRoundTrips() {
        PlayerDoomData p = sample();
        Warnings w = new Warnings();
        PlayerDoomData q = PlayerDataCodec.decode(reparse(PlayerDataCodec.encode(p)), w);
        assertTrue(w.isEmpty(), w.all().toString());
        assertSame(p, q);
        assertEquals(PlayerDataCodec.encode(p).toString(), PlayerDataCodec.encode(q).toString(), "encoding is stable");
    }

    @Test
    void version1DocumentsMigrate() {
        String v1 = "{\"schema\":1,\"player\":\"" + PLAYER + "\",\"energyFraction\":0.25,"
                + "\"research\":[\"latverian_metallurgy\",\"doom_engineering\"],\"knownMobs\":{\"minecraft:blaze\":40,\"minecraft:ghast\":12.5},"
                + "\"focus\":80}";
        Warnings w = new Warnings();
        PlayerDoomData p = PlayerDataCodec.decode(JsonParser.parseString(v1).getAsJsonObject(), w);
        assertTrue(w.isEmpty(), w.all().toString());
        assertEquals(5_000, p.energy, "a quarter of the v1 20,000 DE cell");
        assertEquals(Set.of("latverian_metallurgy", "doom_engineering"), p.researchCompleted);
        assertEquals(40, p.analysis.get("minecraft:blaze").knowledge);
        assertEquals(12.5, p.analysis.get("minecraft:ghast").knowledge);
        assertEquals(80, p.focus);
        assertEquals("royal_mk1", p.frame, "missing v2 fields take defaults");
        JsonObject re = PlayerDataCodec.encode(p);
        assertEquals(PlayerDataCodec.CURRENT, re.get("schema").getAsInt());
        assertFalse(re.has("energyFraction") || re.has("knownMobs"), "v1 keys are gone after migration");
    }

    @Test
    void documentsWithoutASchemaAreTreatedAsVersion1() {
        Warnings w = new Warnings();
        PlayerDoomData p = PlayerDataCodec.decode(JsonParser.parseString("{\"energyFraction\":1.7}").getAsJsonObject(), w);
        assertEquals(20_000, p.energy, "fraction clamped to 1");
    }

    @Test
    void unknownFieldsFromNewerVersionsArePreserved() {
        JsonObject doc = PlayerDataCodec.encode(sample());
        JsonObject future = new JsonObject();
        future.addProperty("paradoxCharge", 7);
        doc.add("timePlatform", future);
        doc.addProperty("schema", PlayerDataCodec.CURRENT + 3);
        Warnings w = new Warnings();
        PlayerDoomData p = PlayerDataCodec.decode(reparse(doc), w);
        assertTrue(w.all().stream().anyMatch(s -> s.contains("newer version")));
        JsonObject back = PlayerDataCodec.encode(p);
        assertSame(sample(), withoutExtra(PlayerDataCodec.decode(reparse(doc), new Warnings())));
        assertEquals(7, back.getAsJsonObject("timePlatform").get("paradoxCharge").getAsInt(), "written back unchanged");
    }

    private static PlayerDoomData withoutExtra(PlayerDoomData p) {
        p.extra = new JsonObject();
        return p;
    }

    @Test
    void missingFieldsTakeDefaults() {
        Warnings w = new Warnings();
        PlayerDoomData p = PlayerDataCodec.decode(JsonParser.parseString("{\"schema\":2}").getAsJsonObject(), w);
        assertTrue(w.isEmpty(), w.all().toString());
        assertNull(p.player);
        assertEquals(0, p.energy);
        assertEquals(100, p.focus);
        assertEquals("royal_mk1", p.frame);
        assertTrue(p.modules.isEmpty() && p.researchCompleted.isEmpty() && p.analysis.isEmpty() && p.waypoints.isEmpty());
        assertEquals("", p.title);
    }

    @Test
    void corruptValuesAreRepairedAndReported() {
        String bad = "{\"schema\":2,\"player\":\"not-a-uuid\",\"armor\":{\"energy\":\"lots\",\"heat\":-40,\"heatLocked\":\"maybe\","
                + "\"modules\":[\"thermal_management\",7,null],\"cooldowns\":{\"bolt\":5,\"pulse\":{\"charges\":-3,\"next\":\"x\"}}},"
                + "\"focus\":\"NaN\",\"research\":{\"counters\":{\"a\":\"b\",\"c\":4},\"completed\":\"everything\",\"activeTicks\":-9},"
                + "\"analysis\":{\"minecraft:blaze\":{\"knowledge\":4000},\"minecraft:ghast\":\"x\"},"
                + "\"sovereignty\":[],\"waypoints\":[{\"name\":\"half\",\"x\":1},17,{\"dimension\":\"d\",\"x\":1,\"y\":2,\"z\":\"3\"}]}";
        Warnings w = new Warnings();
        PlayerDoomData p = assertDoesNotThrow(() -> PlayerDataCodec.decode(JsonParser.parseString(bad).getAsJsonObject(), w));
        assertFalse(w.isEmpty());
        assertNull(p.player);
        assertEquals(0, p.energy);
        assertEquals(0, p.heat);
        assertFalse(p.heatLocked);
        assertEquals(List.of("thermal_management"), p.modules);
        assertFalse(p.cooldowns.containsKey("bolt"));
        assertEquals(0, p.cooldowns.get("pulse")[0]);
        assertTrue(p.focus >= 0 && p.focus <= 100);
        assertEquals(4, p.researchCounters.get("c"));
        assertFalse(p.researchCounters.containsKey("a"));
        assertTrue(p.researchCompleted.isEmpty());
        assertEquals(0, p.researchActiveTicks);
        assertEquals(100, p.analysis.get("minecraft:blaze").knowledge, "clamped to 100");
        assertFalse(p.analysis.containsKey("minecraft:ghast"));
        assertEquals(1, p.waypoints.size());
        assertEquals(3, p.waypoints.get(0).z());
    }

    @Test
    void nonJsonNumbersNeverCrashTheLoader() {
        String nan = "{\"schema\":2,\"armor\":{\"energy\":1e400,\"heat\":\"Infinity\"},\"focus\":-1e999}";
        Warnings w = new Warnings();
        JsonObject o = JsonParser.parseString(nan).getAsJsonObject();
        PlayerDoomData p = assertDoesNotThrow(() -> PlayerDataCodec.decode(o, w));
        assertTrue(p.energy >= 0);
        assertTrue(Double.isFinite(p.heat) && Double.isFinite(p.focus));
    }

    /** Fuzz: randomly mutated documents always load (possibly with warnings) and re-encode. */
    @Test
    void randomlyCorruptedDocumentsAlwaysLoad() {
        String[] junk = {"null", "\"str\"", "-1", "1e308", "[]", "{}", "true", "[1,\"a\",null]", "{\"x\":{}}", "0.5"};
        JsonObject base = PlayerDataCodec.encode(sample());
        for (int seed = 0; seed < 2000; seed++) {
            Random r = new Random(seed);
            JsonObject doc = base.deepCopy();
            for (int k = 0; k < 1 + r.nextInt(4); k++) mutate(doc, r, junk);
            Warnings w = new Warnings();
            PlayerDoomData p = assertDoesNotThrow(() -> PlayerDataCodec.decode(reparse(doc), w), "seed " + seed + ": " + doc);
            assertTrue(p.energy >= 0 && p.heat >= 0 && p.focus >= 0, "seed " + seed);
            assertDoesNotThrow(() -> PlayerDataCodec.encode(p));
        }
    }

    static void mutate(JsonObject o, Random r, String[] junk) {
        List<String> keys = List.copyOf(o.keySet());
        if (keys.isEmpty()) return;
        String k = keys.get(r.nextInt(keys.size()));
        if (o.get(k).isJsonObject() && r.nextBoolean()) {
            mutate(o.getAsJsonObject(k), r, junk);
        } else if (r.nextInt(4) == 0) {
            o.remove(k);
        } else {
            o.add(k, JsonParser.parseString(junk[r.nextInt(junk.length)]));
        }
    }

    // ---- live objects through the mapper ---------------------------------------------------------------
    @Test
    void liveStateSurvivesCaptureEncodeDecodeRestore() {
        ResearchProgress research = new ResearchProgress(TREE);
        for (var n : List.of("latverian_metallurgy", "doom_engineering", "royal_armor", "vibranium_lattice"))
            research.restore(research.counters(), union(research.completed(), n), null, 0);
        research.record(new ResearchEvent(ResearchEvent.Type.SAMPLE_COLLECTED, "minecraft:blaze_rod", 3));
        Loadout loadout = new Loadout(CAT, CAT.frame("royal_mk2"));
        loadout.install("capacitor_dense", research.completed());
        loadout.install("thermal_management", research.completed());
        DoomSuit suit = new DoomSuit(loadout, research.completed());
        suit.energy().insert(31_000, false);
        suit.heat().addHeat(30);
        suit.focus().castInstant(20, 5);
        suit.cooldowns().tryUse("pulse", 100);
        AnalysisLedger ledger = new AnalysisLedger(PROFILES);
        ledger.observe("minecraft:blaze", ObservationMethod.SCAN, 0);
        ledger.observe("minecraft:blaze", ObservationMethod.OBSERVED_ATTACK, 0);

        PlayerDoomData captured = PlayerDataMapper.capture(new PlayerDoomData(), suit, research, ledger);
        PlayerDoomData loaded = PlayerDataCodec.decode(reparse(PlayerDataCodec.encode(captured)), new Warnings());

        ResearchProgress research2 = new ResearchProgress(TREE);
        DoomSuit suit2 = new DoomSuit(new Loadout(CAT, CAT.frame("royal_mk1")), Set.of());
        AnalysisLedger ledger2 = new AnalysisLedger(PROFILES);
        Warnings w = new Warnings();
        PlayerDataMapper.restore(loaded, suit2, research2, ledger2, CAT, w);
        assertTrue(w.isEmpty(), w.all().toString());
        assertEquals(research.completed(), research2.completed());
        assertEquals(research.counters(), research2.counters());
        assertEquals(suit.loadout().frame().id(), suit2.loadout().frame().id());
        assertEquals(suit.loadout().installed(), suit2.loadout().installed());
        assertEquals(suit.energy().capacity(), suit2.energy().capacity(), "dense capacitor restored before energy");
        assertEquals(suit.energy().stored(), suit2.energy().stored());
        assertEquals(suit.heat().heat(), suit2.heat().heat());
        assertEquals(suit.focus().current(), suit2.focus().current(), 1e-12);
        assertEquals(suit.cooldowns().get("pulse").nextChargeAt(), suit2.cooldowns().get("pulse").nextChargeAt());
        assertEquals(ledger.knowledge("minecraft:blaze"), ledger2.knowledge("minecraft:blaze"));
        assertEquals(ledger.entry("minecraft:blaze").orElseThrow().revealed(), ledger2.entry("minecraft:blaze").orElseThrow().revealed());
        assertEquals(ledger.entry("minecraft:blaze").orElseThrow().methodCounts(), ledger2.entry("minecraft:blaze").orElseThrow().methodCounts());
    }

    @Test
    void restoreDropsWhatNoLongerValidates() {
        PlayerDoomData d = sample();
        d.frame = "royal_mk9";
        d.modules = List.of("thermal_management", "gauntlet_focusing", "flux_capacitor");
        d.researchCompleted.add("removed_node");
        d.cooldowns.put("time_stop", new long[]{1, 2});
        d.analysis.get("minecraft:blaze").counts.put("TELEPATHY", 2);
        d.energy = 999_999;
        Warnings w = new Warnings();
        ResearchProgress research = new ResearchProgress(TREE);
        DoomSuit suit = new DoomSuit(new Loadout(CAT, CAT.frame("royal_mk1")), Set.of());
        PlayerDataMapper.restore(d, suit, research, new AnalysisLedger(PROFILES), CAT, w);
        assertEquals("royal_mk1", suit.loadout().frame().id());
        assertEquals(Set.of("thermal_management"), suit.loadout().installed());
        assertFalse(research.has("removed_node"));
        assertEquals(suit.energy().capacity(), suit.energy().stored(), "clamped to capacity");
        String all = String.join("\n", w.all());
        for (String expect : List.of("royal_mk9", "gauntlet_focusing", "flux_capacitor", "removed_node", "time_stop", "TELEPATHY", "energy"))
            assertTrue(all.contains(expect), "warning about " + expect + " in\n" + all);
    }

    private static Set<String> union(Set<String> a, String b) {
        java.util.LinkedHashSet<String> s = new java.util.LinkedHashSet<>(a);
        s.add(b);
        return s;
    }

    // ---- world documents -------------------------------------------------------------------------------
    static WorldDoomData world() {
        WorldDoomData d = new WorldDoomData();
        UUID owner = PLAYER;
        BotLocation home = new BotLocation("minecraft:overworld", 783, 79, -10258);
        d.bots.add(new WorldDoomData.BotRecord(new UUID(1, 1), owner, "standard", BotOrder.stay(home), home, home, 0, 0.75));
        d.bots.add(new WorldDoomData.BotRecord(new UUID(1, 2), owner, "standard",
                BotOrder.patrol(List.of(home, new BotLocation("minecraft:overworld", 800, 70, -10090))), home, null, 1, 1));
        d.bots.add(new WorldDoomData.BotRecord(new UUID(1, 3), owner, "standard", BotOrder.defend(home, 16), null, null, 0, 1));
        d.bots.add(new WorldDoomData.BotRecord(new UUID(1, 4), owner, "standard", BotOrder.attack(new UUID(9, 9)), null, null, 0, 1));
        AccessPolicy door = new AccessPolicy(owner, DeviceKind.SECURITY_DOOR);
        door.grant(SecurityIdentity.player(owner), new UUID(5, 5), Set.of(Permission.OPEN));
        d.devices.add(new WorldDoomData.DeviceRecord("minecraft:overworld@783,79,-10258", door));
        d.latveriaCenter = new BotLocation("minecraft:overworld", 799, 70, -10090);
        d.realmName = "Latveria";
        d.sovereign = owner;
        return d;
    }

    @Test
    void worldDataRoundTrips() {
        WorldDoomData d = world();
        Warnings w = new Warnings();
        WorldDoomData e = WorldDataCodec.decode(reparse(WorldDataCodec.encode(d)), w);
        assertTrue(w.isEmpty(), w.all().toString());
        assertEquals(d.bots, e.bots);
        assertEquals(d.latveriaCenter, e.latveriaCenter);
        assertEquals(d.sovereign, e.sovereign);
        assertEquals(d.realmName, e.realmName);
        assertEquals(1, e.devices.size());
        assertEquals(d.devices.get(0).id(), e.devices.get(0).id());
        assertEquals(d.devices.get(0).policy().trusted(), e.devices.get(0).policy().trusted());
        assertEquals(WorldDataCodec.encode(d).toString(), WorldDataCodec.encode(e).toString());
    }

    @Test
    void worldDataRepairsBadEntries() {
        JsonObject doc = WorldDataCodec.encode(world());
        var bots = doc.getAsJsonArray("bots");
        bots.add(bots.get(0).deepCopy()); // duplicate id
        JsonObject noOwner = bots.get(1).getAsJsonObject().deepCopy();
        noOwner.remove("owner");
        noOwner.addProperty("id", new UUID(1, 77).toString());
        bots.add(noOwner);
        bots.get(2).getAsJsonObject().getAsJsonObject("order").remove("radius"); // DEFEND_AREA without radius
        bots.get(1).getAsJsonObject().getAsJsonObject("order").addProperty("command", "DANCE");
        bots.get(0).getAsJsonObject().addProperty("health", 7);
        bots.add(JsonParser.parseString("42"));
        doc.addProperty("futureRealmTax", 12);
        Warnings w = new Warnings();
        WorldDoomData e = WorldDataCodec.decode(reparse(doc), w);
        assertEquals(4, e.bots.size(), "duplicates, ownerless and non-object entries dropped");
        assertEquals(1.0, e.bots.get(0).health(), "clamped");
        assertEquals(BotOrder.follow(), e.bots.get(1).order(), "unknown command falls back to FOLLOW");
        assertEquals(BotOrder.follow(), e.bots.get(2).order(), "an order that lost its parameters falls back to FOLLOW");
        assertEquals(12, WorldDataCodec.encode(e).get("futureRealmTax").getAsInt(), "unknown world fields preserved");
        assertTrue(w.all().size() >= 5, w.all().toString());
    }

    @Test
    void latveriaCentreIsOptional() {
        WorldDoomData d = new WorldDoomData();
        WorldDoomData e = WorldDataCodec.decode(reparse(WorldDataCodec.encode(d)), new Warnings());
        assertNull(e.latveriaCenter, "no hard-coded capital");
        assertNull(e.sovereign);
    }
}
