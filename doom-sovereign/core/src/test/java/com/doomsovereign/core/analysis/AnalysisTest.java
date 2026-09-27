package com.doomsovereign.core.analysis;

import java.io.StringReader;
import java.util.List;
import java.util.Set;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class AnalysisTest {
    private static final ProfileRegistry DEFAULTS = ProfileRegistry.loadDefaults();

    @Test
    void defaultProfilesLoadAndAreConsistent() {
        assertEquals(16, DEFAULTS.size());
        for (String id : List.of("minecraft:blaze", "minecraft:warden", "minecraft:breeze", "minecraft:enderman")) assertTrue(DEFAULTS.known(id), id);
        for (String id : List.of("minecraft:blaze", "minecraft:guardian", "minecraft:enderman", "minecraft:witch", "minecraft:warden")) {
            SubjectProfile p = DEFAULTS.profile(id);
            assertFalse(p.traits().isEmpty(), id);
            for (Trait t : p.traits()) assertTrue(t.threshold() >= 0 && t.threshold() <= KnowledgeEntry.MAX, id + " " + t.id());
            for (Countermeasure c : p.countermeasures()) assertTrue(c.id().startsWith("counter:"), c.id());
        }
    }

    @Test
    void everyCountermeasureIsReachable() {
        // for every profile, a thorough study (each method many times) must unlock every countermeasure
        for (String id : List.of("minecraft:blaze", "minecraft:guardian", "minecraft:enderman", "minecraft:witch", "minecraft:evoker",
                "minecraft:vex", "minecraft:shulker", "minecraft:iron_golem", "minecraft:creeper", "minecraft:skeleton",
                "minecraft:wither_skeleton", "minecraft:ghast", "minecraft:phantom", "minecraft:warden", "minecraft:piglin_brute",
                "minecraft:breeze")) {
            AnalysisLedger l = new AnalysisLedger(DEFAULTS);
            long t = 0;
            for (int round = 0; round < 400 && !l.entry(id).map(KnowledgeEntry::complete).orElse(false); round++) {
                for (ObservationMethod m : ObservationMethod.values()) l.observe(id, m, t);
                t += 200;
            }
            SubjectProfile p = DEFAULTS.profile(id);
            KnowledgeEntry e = l.entry(id).orElseThrow();
            assertTrue(e.complete(), id);
            assertEquals(p.traits().size(), e.revealed().size(), id + " traits");
            assertEquals(p.countermeasures().size(), e.countermeasures().size(), id + " countermeasures");
        }
    }

    @Test
    void repeatedObservationHasDiminishingReturns() {
        AnalysisLedger l = new AnalysisLedger(DEFAULTS);
        double prev = Double.MAX_VALUE;
        for (int i = 0; i < 20; i++) {
            ObservationResult r = l.observe("minecraft:zombie", ObservationMethod.DEFEATED, i);
            assertTrue(r.counted());
            assertTrue(r.gained() <= prev + 1e-12);
            assertTrue(r.gained() >= AnalysisLedger.MIN_GAIN - 1e-12);
            prev = r.gained();
        }
        assertEquals(AnalysisLedger.MIN_GAIN, prev, 1e-12, "floors at the minimum gain");
    }

    @Test
    void methodsOnlyCountOncePerInterval() {
        AnalysisLedger l = new AnalysisLedger(DEFAULTS);
        assertTrue(l.observe("minecraft:blaze", ObservationMethod.SCAN, 0).counted());
        ObservationResult spam = l.observe("minecraft:blaze", ObservationMethod.SCAN, 99);
        assertFalse(spam.counted());
        assertEquals(0, spam.gained());
        assertTrue(l.observe("minecraft:blaze", ObservationMethod.SCAN, 100).counted());
        assertTrue(l.observe("minecraft:blaze", ObservationMethod.OBSERVED_ATTACK, 100).counted(), "intervals are per method");
        assertTrue(l.observe("minecraft:guardian", ObservationMethod.SCAN, 1).counted(), "and per subject");
    }

    @Test
    void someTraitsNeedTheRightKindOfObservation() {
        AnalysisLedger l = new AnalysisLedger(DEFAULTS);
        long t = 0;
        for (int i = 0; i < 40; i++, t += 200) l.observe("minecraft:blaze", ObservationMethod.DEEP_SCAN, t);
        assertTrue(l.knowledge("minecraft:blaze") > 50);
        Set<String> revealed = l.entry("minecraft:blaze").orElseThrow().revealed();
        assertTrue(revealed.contains("vitals"));
        assertFalse(revealed.contains("fire_immunity"), "you learn fire immunity by watching fire fail, not by scanning");
        ObservationResult r = l.observe("minecraft:blaze", ObservationMethod.OBSERVED_ATTACK, t);
        assertTrue(r.newlyRevealed().contains("fire_immunity"));
    }

    @Test
    void variedStudyBeatsGrinding() {
        AnalysisLedger grind = new AnalysisLedger(DEFAULTS);
        long t = 0;
        int grindScans = 0;
        while (!grind.entry("minecraft:blaze").map(KnowledgeEntry::complete).orElse(false)) {
            grind.observe("minecraft:blaze", ObservationMethod.SCAN, t);
            t += 100;
            grindScans++;
        }
        long grindTicks = t;
        AnalysisLedger varied = new AnalysisLedger(DEFAULTS);
        t = 0;
        while (!varied.entry("minecraft:blaze").map(KnowledgeEntry::complete).orElse(false)) {
            for (ObservationMethod m : ObservationMethod.values()) varied.observe("minecraft:blaze", m, t);
            t += 200;
        }
        assertTrue(grindScans > 100, "grinding one scan takes " + grindScans + " scans");
        assertTrue(t * 10 < grindTicks, "varied " + t + " ticks vs grind " + grindTicks);
    }

    @Test
    void countermeasuresUnlockOnceWithTheirTraits() {
        AnalysisLedger l = new AnalysisLedger(DEFAULTS);
        long t = 0;
        boolean thermal = false;
        int unlockEvents = 0;
        for (int round = 0; round < 50; round++, t += 200) {
            for (ObservationMethod m : ObservationMethod.values()) {
                ObservationResult r = l.observe("minecraft:blaze", m, t);
                if (r.newlyUnlocked().contains("counter:thermal_plating")) {
                    unlockEvents++;
                    KnowledgeEntry e = l.entry("minecraft:blaze").orElseThrow();
                    assertTrue(e.knowledge() >= 80 - 1e-9);
                    assertTrue(e.revealed().containsAll(Set.of("fire_immunity", "rod_core")));
                    thermal = true;
                }
            }
        }
        assertTrue(thermal);
        assertEquals(1, unlockEvents);
        assertTrue(l.allCountermeasures().contains("counter:coolant_bolts"));
    }

    @Test
    void completionFiresExactlyOnce() {
        AnalysisLedger l = new AnalysisLedger(DEFAULTS);
        int completions = 0;
        for (int i = 0; i < 400; i++) if (l.observe("minecraft:creeper", ObservationMethod.DEFEATED, i).becameComplete()) completions++;
        assertEquals(1, completions);
        assertEquals(KnowledgeEntry.MAX, l.knowledge("minecraft:creeper"), 1e-12);
    }

    @Test
    void unknownCreaturesGetAGenericProfile() {
        AnalysisLedger l = new AnalysisLedger(DEFAULTS);
        assertFalse(DEFAULTS.known("othermod:gloop"));
        ObservationResult r = l.observe("othermod:gloop", ObservationMethod.SCAN, 0);
        assertTrue(r.newlyRevealed().contains("health"));
        assertEquals(1, l.visibleTraits("othermod:gloop").size());
    }

    @Test
    void qualityScalesGainAndGarbageIsHarmless() {
        AnalysisLedger l = new AnalysisLedger(DEFAULTS);
        assertEquals(5, l.observe("a:a", ObservationMethod.SCAN, 0, 0.5).gained(), 1e-12);
        assertEquals(0, l.observe("a:b", ObservationMethod.SCAN, 0, Double.NaN).gained());
        assertEquals(15, l.observe("a:c", ObservationMethod.SCAN, 0, 99).gained(), 1e-12, "quality clamps at 1.5");
    }

    @Test
    void malformedProfilesNameTheSubject() {
        String bad = "[{\"subject\":\"x:broken\",\"name\":\"B\",\"traits\":[{\"id\":\"a\",\"category\":\"NOPE\",\"text\":\"t\",\"threshold\":5}]}]";
        IllegalArgumentException e = assertThrows(IllegalArgumentException.class, () -> new ProfileRegistry().load(new StringReader(bad)));
        assertTrue(e.getMessage().contains("x:broken"));
        String range = "[{\"subject\":\"x:r\",\"name\":\"R\",\"traits\":[{\"id\":\"a\",\"category\":\"VITALS\",\"text\":\"t\",\"threshold\":500}]}]";
        assertThrows(IllegalArgumentException.class, () -> new ProfileRegistry().load(new StringReader(range)));
        String dangling = "[{\"subject\":\"x:d\",\"name\":\"D\",\"traits\":[],\"countermeasures\":[{\"id\":\"counter:x\",\"title\":\"X\","
                + "\"description\":\"d\",\"knowledge\":10,\"traits\":[\"ghost\"]}]}]";
        assertThrows(IllegalArgumentException.class, () -> new ProfileRegistry().load(new StringReader(dangling)));
    }
}
