package com.doomsovereign.core.research;

import com.doomsovereign.core.api.ResearchEvent;
import com.doomsovereign.core.api.ResearchEvent.Type;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.Set;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class ResearchTest {
    private static final ResearchTree TREE = DoomResearch.standard();

    private static void satisfy(ResearchProgress p, String id) {
        for (Requirement r : TREE.node(id).requirements()) p.record(new ResearchEvent(r.type(), r.key(), r.count()));
    }

    /** Completes a node the way a player would: requirements, then console time. */
    private static void research(ResearchProgress p, String id) {
        satisfy(p, id);
        if (p.has(id)) return;
        assertEquals(ResearchProgress.Status.READY, p.status(id), id + " " + p.missing(id));
        assertTrue(p.begin(id));
        String done = null;
        for (int i = 0; i < TREE.node(id).consoleTicks() && done == null; i++) done = p.tickConsole();
        assertEquals(id, done);
    }

    @Test
    void standardTreeIsWellFormed() {
        assertEquals(22, TREE.nodes().size());
        List<ResearchNode> order = TREE.topological();
        Set<String> seen = new HashSet<>();
        for (ResearchNode n : order) {
            assertTrue(seen.containsAll(n.prerequisites()), n.id());
            seen.add(n.id());
            assertFalse(n.description().isBlank());
        }
        assertTrue(TREE.ancestors("temporal_mechanics").containsAll(Set.of("royal_armor", "apprentice_of_the_arts", "translocation")));
    }

    @Test
    void sorceryIsAParallelPathNotBehindTechnology() {
        for (ResearchNode n : TREE.nodes()) {
            if (n.branch() != Branch.SORCERY) continue;
            for (String a : TREE.ancestors(n.id()))
                assertEquals(Branch.SORCERY, TREE.node(a).branch(), n.id() + " should not need " + a);
        }
    }

    @Test
    void cyclesDanglingReferencesAndDuplicatesAreRejected() {
        ResearchNode a = new ResearchNode("a", Branch.SCIENCE, "A", "a", Set.of("b"), List.of(), 1);
        ResearchNode b = new ResearchNode("b", Branch.SCIENCE, "B", "b", Set.of("c"), List.of(), 1);
        ResearchNode c = new ResearchNode("c", Branch.SCIENCE, "C", "c", Set.of("a"), List.of(), 1);
        assertThrows(IllegalArgumentException.class, () -> new ResearchTree(List.of(a, b, c)));
        assertThrows(IllegalArgumentException.class, () -> new ResearchTree(List.of(a)));
        ResearchNode d = new ResearchNode("d", Branch.SCIENCE, "D", "d", Set.of(), List.of(), 1);
        assertThrows(IllegalArgumentException.class, () -> new ResearchTree(List.of(d, d)));
        ResearchNode self = new ResearchNode("s", Branch.SCIENCE, "S", "s", Set.of("s"), List.of(), 1);
        assertThrows(IllegalArgumentException.class, () -> new ResearchTree(List.of(self)));
    }

    @Test
    void diamondShapedPrerequisitesAreNotACycle() {
        ResearchNode root = new ResearchNode("root", Branch.SCIENCE, "R", "r", Set.of(), List.of(), 1);
        ResearchNode l = new ResearchNode("l", Branch.SCIENCE, "L", "l", Set.of("root"), List.of(), 1);
        ResearchNode r = new ResearchNode("r", Branch.SCIENCE, "R", "r", Set.of("root", "l"), List.of(), 1);
        ResearchNode top = new ResearchNode("top", Branch.SCIENCE, "T", "t", Set.of("l", "r", "root"), List.of(), 1);
        assertDoesNotThrow(() -> new ResearchTree(List.of(top, r, l, root)));
    }

    @Test
    void automaticNodesCompleteFromEventsAlone() {
        ResearchProgress p = new ResearchProgress(TREE);
        p.record(new ResearchEvent(Type.SAMPLE_COLLECTED, "minecraft:iron_ingot", 32));
        p.record(new ResearchEvent(Type.SAMPLE_COLLECTED, "minecraft:copper_ingot", 32));
        assertFalse(p.has("latverian_metallurgy"));
        assertEquals(2.0 / 3.0, p.requirementProgress("latverian_metallurgy"), 1e-12);
        List<String> done = p.record(new ResearchEvent(Type.SAMPLE_COLLECTED, "minecraft:quartz", 8));
        assertEquals(List.of("latverian_metallurgy"), done);
    }

    @Test
    void prerequisitesGateAndStatusesExplainWhy() {
        ResearchProgress p = new ResearchProgress(TREE);
        assertEquals(ResearchProgress.Status.LOCKED, p.status("royal_armor"));
        assertEquals(ResearchProgress.Status.LOCKED, p.status("afterburner_lattice"));
        satisfy(p, "royal_armor");
        assertEquals(ResearchProgress.Status.LOCKED, p.status("royal_armor"), "requirements alone do not skip prerequisites");
        assertFalse(p.begin("royal_armor"));
        assertTrue(p.missing("royal_armor").contains("Research Doom Engineering"));
        research(p, "latverian_metallurgy");
        research(p, "doom_engineering");
        assertEquals(ResearchProgress.Status.READY, p.status("royal_armor"));
        research(p, "royal_armor");
        research(p, "repulsor_levitation");
        assertEquals(ResearchProgress.Status.BLOCKED_BY_PREREQUISITES, p.status("afterburner_lattice"), "one of two prerequisites done");
    }

    @Test
    void consoleResearchTakesTimeAndOneProjectAtATime() {
        ResearchProgress p = new ResearchProgress(TREE);
        research(p, "latverian_metallurgy");
        satisfy(p, "doom_engineering");
        satisfy(p, "apprentice_of_the_arts");
        assertTrue(p.has("apprentice_of_the_arts"));
        satisfy(p, "wardcraft");
        assertTrue(p.begin("doom_engineering"));
        assertFalse(p.begin("wardcraft"), "console busy");
        assertEquals(ResearchProgress.Status.RESEARCHING, p.status("doom_engineering"));
        for (int i = 0; i < 300; i++) assertNull(p.tickConsole());
        assertEquals(0.5, p.consoleProgress(), 1e-12);
        p.cancel();
        assertEquals(0, p.consoleProgress());
        assertEquals(ResearchProgress.Status.READY, p.status("doom_engineering"), "cancel loses progress but not eligibility");
        assertTrue(p.begin("wardcraft"));
    }

    @Test
    void automaticFollowUpsCompleteWhenTheirPrerequisiteFinishes() {
        ResearchProgress p = new ResearchProgress(TREE);
        p.record(ResearchEvent.of(Type.ACHIEVEMENT, "doom_sovereign:survive_long_fall"));
        for (String id : List.of("latverian_metallurgy", "doom_engineering", "royal_armor")) research(p, id);
        assertFalse(p.has("emergency_repulsors"));
        research(p, "repulsor_levitation");
        assertTrue(p.has("emergency_repulsors"), "achievement recorded earlier still counts");
    }

    @Test
    void countersSaturateInsteadOfOverflowing() {
        ResearchProgress p = new ResearchProgress(TREE);
        Requirement r = Requirement.sample("minecraft:redstone", 1);
        p.record(new ResearchEvent(Type.SAMPLE_COLLECTED, "minecraft:redstone", Integer.MAX_VALUE));
        p.record(new ResearchEvent(Type.SAMPLE_COLLECTED, "minecraft:redstone", Integer.MAX_VALUE));
        assertEquals(Integer.MAX_VALUE, p.count(r));
        assertThrows(IllegalArgumentException.class, () -> new ResearchEvent(Type.SAMPLE_COLLECTED, "x", 0));
        assertThrows(IllegalArgumentException.class, () -> p.status("no_such_node"));
    }

    @Test
    void restoreDropsUnknownNodesAndStaleProjects() {
        ResearchProgress p = new ResearchProgress(TREE);
        p.restore(Map.of("SAMPLE_COLLECTED|minecraft:quartz", 3, "bad", -4), Set.of("latverian_metallurgy", "removed_in_update"),
                "latverian_metallurgy", 40);
        assertEquals(Set.of("latverian_metallurgy"), p.completed());
        assertNull(p.active(), "an already-complete project cannot be active");
        assertFalse(p.counters().containsKey("bad"));
        p.restore(Map.of(), Set.of("latverian_metallurgy"), "doom_engineering", -5);
        assertEquals("doom_engineering", p.active());
        assertEquals(0, p.activeTicks());
    }

    /** Property test: random play never completes a node whose prerequisites or requirements are unmet. */
    @Test
    void randomPlayRespectsTheGraph() {
        List<Requirement> allReqs = new ArrayList<>();
        for (ResearchNode n : TREE.nodes()) allReqs.addAll(n.requirements());
        List<String> ids = TREE.nodes().stream().map(ResearchNode::id).toList();
        for (int seed = 0; seed < 200; seed++) {
            Random r = new Random(seed);
            ResearchProgress p = new ResearchProgress(TREE);
            for (int step = 0; step < 3000; step++) {
                int op = r.nextInt(10);
                if (op < 4) {
                    Requirement q = allReqs.get(r.nextInt(allReqs.size()));
                    p.record(new ResearchEvent(q.type(), q.key(), 1 + r.nextInt(q.count())));
                } else if (op < 5) {
                    p.begin(ids.get(r.nextInt(ids.size())));
                } else if (op < 9) {
                    for (int k = 0; k < 200; k++) p.tickConsole();
                } else if (r.nextInt(10) == 0) {
                    p.cancel();
                }
                for (String c : p.completed()) {
                    ResearchNode n = TREE.node(c);
                    assertTrue(p.completed().containsAll(n.prerequisites()), "seed " + seed + ": " + c);
                    for (Requirement q : n.requirements()) assertTrue(p.count(q) >= q.count(), "seed " + seed + ": " + c);
                }
                if (p.active() != null) assertFalse(p.has(p.active()));
            }
        }
    }
}
