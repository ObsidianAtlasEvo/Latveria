package com.doomsovereign.core.module;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Random;
import java.util.Set;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class LoadoutTest {
    private static final ModuleCatalog CAT = ModuleCatalog.standard();
    private static final Set<String> ALL_RESEARCH = Set.of("repulsor_levitation", "afterburner_lattice", "vibranium_lattice",
            "pressure_hull", "omnidirectional_fields", "wardcraft", "coherent_emitters", "dimensional_theory", "veil_of_the_mask");

    private static Loadout on(String frame) {
        return new Loadout(CAT, CAT.frame(frame));
    }

    private static Set<LoadoutIssue.Kind> kinds(List<LoadoutIssue> issues) {
        Set<LoadoutIssue.Kind> k = new HashSet<>();
        for (LoadoutIssue i : issues) k.add(i.kind());
        return k;
    }

    @Test
    void catalogIsConsistent() {
        assertDoesNotThrow(CAT::validate);
        assertEquals(16, CAT.modules().size());
        assertEquals(5, CAT.frames().size());
        for (ModuleDef m : CAT.modules()) assertFalse(m.summary().isBlank(), m.id() + " needs a tooltip");
    }

    @Test
    void basicModulesInstallWithoutResearch() {
        Loadout l = on("royal_mk1");
        assertTrue(l.install("capacitor_standard", Set.of()).isEmpty());
        assertTrue(l.install("thermal_management", Set.of()).isEmpty());
        assertEquals(Set.of("capacitor_standard", "thermal_management"), l.installed());
        assertEquals(4, l.capacityUsed());
    }

    @Test
    void researchGatesModules() {
        Loadout l = on("royal_mk1");
        List<LoadoutIssue> issues = l.install("thruster_mk1", Set.of());
        assertEquals(Set.of(LoadoutIssue.Kind.MISSING_RESEARCH), kinds(issues));
        assertTrue(l.installed().isEmpty(), "refused installs change nothing");
        assertTrue(l.install("thruster_mk1", Set.of("repulsor_levitation")).isEmpty());
    }

    @Test
    void oneModulePerFamily() {
        Loadout l = on("royal_mk2");
        l.install("thruster_mk1", ALL_RESEARCH);
        assertTrue(kinds(l.check("thruster_mk2", ALL_RESEARCH)).contains(LoadoutIssue.Kind.SAME_FAMILY));
        assertTrue(kinds(on("royal_mk1").check("thruster_mk2", ALL_RESEARCH)).contains(LoadoutIssue.Kind.TIER_TOO_LOW));
    }

    @Test
    void conflictsAreSymmetric() {
        Loadout a = on("arcane_sovereign");
        assertTrue(a.install("arcane_insulation", ALL_RESEARCH).isEmpty());
        assertTrue(kinds(a.check("teleport_stabilizer", ALL_RESEARCH)).contains(LoadoutIssue.Kind.CONFLICT));
        Loadout b = on("arcane_sovereign");
        assertTrue(b.install("teleport_stabilizer", ALL_RESEARCH).isEmpty());
        assertTrue(kinds(b.check("arcane_insulation", ALL_RESEARCH)).contains(LoadoutIssue.Kind.CONFLICT));
    }

    @Test
    void requiredModulesMustBePresentAndCannotBeRemoved() {
        Loadout l = on("royal_mk2");
        assertTrue(kinds(l.check("gauntlet_focusing", ALL_RESEARCH)).contains(LoadoutIssue.Kind.MISSING_MODULE));
        l.install("thermal_management", ALL_RESEARCH);
        assertTrue(l.install("gauntlet_focusing", ALL_RESEARCH).isEmpty());
        assertFalse(l.remove("thermal_management"), "gauntlet focusing depends on it");
        assertTrue(l.remove("gauntlet_focusing"));
        assertTrue(l.remove("thermal_management"));
        assertFalse(l.remove("thermal_management"), "already gone");
    }

    @Test
    void slotsAndCapacityAreLimits() {
        Loadout l = on("royal_mk1");
        l.install("targeting_suite", Set.of());
        assertTrue(kinds(l.check("sensor_array", Set.of())).contains(LoadoutIssue.Kind.NO_FREE_SLOT));
        Loadout c = on("royal_mk1");
        for (String id : List.of("capacitor_standard", "thermal_management", "kinetic_dampener", "shield_emitter_directional"))
            assertTrue(c.install(id, Set.of()).isEmpty(), id);
        assertEquals(8, c.capacityUsed());
        assertEquals(Set.of(LoadoutIssue.Kind.OVER_CAPACITY), kinds(c.check("targeting_suite", Set.of())));
    }

    @Test
    void duplicatesAndUnknownsAreRefused() {
        Loadout l = on("royal_mk1");
        l.install("capacitor_standard", Set.of());
        assertTrue(kinds(l.check("capacitor_standard", Set.of())).contains(LoadoutIssue.Kind.DUPLICATE));
        assertEquals(Set.of(LoadoutIssue.Kind.UNKNOWN_MODULE), kinds(l.check("vibranium_toaster", Set.of())));
    }

    @Test
    void changingFramesKeepsWhatStillFits() {
        Loadout l = on("royal_mk2");
        for (String id : List.of("thermal_management", "gauntlet_focusing", "capacitor_standard", "targeting_suite"))
            assertTrue(l.install(id, ALL_RESEARCH).isEmpty(), id);
        List<String> dropped = l.changeFrame(CAT.frame("royal_mk1"), ALL_RESEARCH);
        assertEquals(List.of("gauntlet_focusing"), dropped, "tier 2 module cannot ride a tier 1 frame");
        assertEquals(Set.of("thermal_management", "capacitor_standard", "targeting_suite"), l.installed());
        assertEquals("royal_mk1", l.frame().id());
    }

    @Test
    void statsCombineFrameAndModules() {
        Loadout l = on("technological_supremacy");
        l.install("capacitor_standard", Set.of());
        SuitStats s = l.stats();
        assertEquals(1.3 * 1.5, s.get(Stat.ENERGY_CAPACITY_MULT), 1e-12);
        assertEquals(1.0, s.get(Stat.ENERGY_REGEN_ADD), 1e-12);
        assertEquals(1.0, s.massPenalty());
        Loadout siege = on("siege");
        assertEquals(0.8, siege.stats().get(Stat.CRUISE_SPEED_MULT), 1e-12);
        l.install("sensor_array", Set.of());
        assertTrue(l.stats().has(Capability.DEEP_SCAN));
        assertFalse(l.stats().has(Capability.BOOST));
    }

    @Test
    void heavyLoadoutsFlySlower() {
        Loadout l = on("technological_supremacy");
        for (String id : List.of("capacitor_dense", "thruster_mk2", "kinetic_dampener", "thermal_management", "sensor_array",
                "shield_emitter_spherical"))
            assertTrue(l.install(id, ALL_RESEARCH).isEmpty(), id);
        assertEquals(14, l.mass());
        SuitStats s = l.stats();
        assertEquals(12.0 / 14.0, s.massPenalty(), 1e-12);
        assertEquals(1.25 * 12.0 / 14.0, s.get(Stat.CRUISE_SPEED_MULT), 1e-12);
        assertTrue(s.has(Capability.BOOST) && s.has(Capability.SPHERICAL_SHIELD) && s.has(Capability.FALL_ARREST));
    }

    /** Property test: no sequence of installs, removals and frame swaps yields an invalid loadout. */
    @Test
    void randomOperationsNeverProduceAnInvalidLoadout() {
        List<String> ids = new ArrayList<>();
        for (ModuleDef m : CAT.modules()) ids.add(m.id());
        List<SuitFrame> frames = new ArrayList<>(CAT.frames());
        List<String> research = new ArrayList<>(ALL_RESEARCH);
        for (int seed = 0; seed < 500; seed++) {
            Random r = new Random(seed);
            Set<String> known = new HashSet<>();
            for (String s : research) if (r.nextBoolean()) known.add(s);
            Loadout l = new Loadout(CAT, frames.get(r.nextInt(frames.size())));
            for (int step = 0; step < 60; step++) {
                int op = r.nextInt(10);
                if (op < 6) l.install(ids.get(r.nextInt(ids.size())), known);
                else if (op < 9) l.remove(ids.get(r.nextInt(ids.size())));
                else l.changeFrame(frames.get(r.nextInt(frames.size())), known);
                assertValid(l, known, "seed " + seed + " step " + step);
            }
        }
    }

    private static void assertValid(Loadout l, Set<String> research, String where) {
        SuitFrame f = l.frame();
        assertTrue(l.capacityUsed() <= f.capacity(), where);
        Set<String> families = new HashSet<>();
        for (SlotKind k : SlotKind.values()) {
            long used = l.installed().stream().filter(id -> CAT.module(id).slot() == k).count();
            assertTrue(used <= f.slots(k), where + " slot " + k);
        }
        for (String id : l.installed()) {
            ModuleDef m = CAT.module(id);
            assertTrue(m.minTier() <= f.tier(), where);
            assertTrue(research.containsAll(m.requiresResearch()), where);
            assertTrue(l.installed().containsAll(m.requiresModules()), where + " " + id + " lost a prerequisite");
            for (String c : m.conflicts()) assertFalse(l.installed().contains(c), where);
            if (m.family() != null) assertTrue(families.add(m.family()), where + " two " + m.family());
        }
    }
}
