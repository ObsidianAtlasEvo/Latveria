package com.doomsovereign.core.persist;

import com.doomsovereign.core.analysis.AnalysisLedger;
import com.doomsovereign.core.analysis.KnowledgeEntry;
import com.doomsovereign.core.analysis.ObservationMethod;
import com.doomsovereign.core.cooldown.Cooldown;
import com.doomsovereign.core.module.LoadoutIssue;
import com.doomsovereign.core.module.ModuleCatalog;
import com.doomsovereign.core.module.SuitFrame;
import com.doomsovereign.core.research.ResearchProgress;
import com.doomsovereign.core.suit.DoomSuit;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;

/** Moves state between live domain objects and {@link PlayerDoomData}. */
public final class PlayerDataMapper {
    private PlayerDataMapper() {
    }

    public static PlayerDoomData capture(PlayerDoomData into, DoomSuit suit, ResearchProgress research, AnalysisLedger analysis) {
        into.energy = suit.energy().stored();
        into.lastDrainTick = suit.energy().lastDrainTick();
        into.heat = suit.heat().heat();
        into.heatLocked = suit.heat().locked();
        into.everInitialised = suit.everInitialised();
        into.frame = suit.loadout().frame().id();
        into.modules = List.copyOf(suit.loadout().installed());
        into.cooldowns.clear();
        suit.cooldowns().all().forEach((k, c) -> into.cooldowns.put(k, new long[]{c.storedCharges(), c.nextChargeAt()}));
        into.focus = suit.focus().current();
        into.researchCounters.clear();
        into.researchCounters.putAll(research.counters());
        into.researchCompleted.clear();
        into.researchCompleted.addAll(research.completed());
        into.researchActive = research.active();
        into.researchActiveTicks = research.activeTicks();
        into.analysis.clear();
        for (KnowledgeEntry e : analysis.entries().values()) {
            PlayerDoomData.AnalysisRecord r = new PlayerDoomData.AnalysisRecord();
            r.knowledge = e.knowledge();
            e.methodCounts().forEach((m, n) -> r.counts.put(m.name(), n));
            r.revealed.addAll(e.revealed());
            r.countermeasures.addAll(e.countermeasures());
            into.analysis.put(e.subjectId(), r);
        }
        return into;
    }

    /**
     * Applies saved state to freshly constructed domain objects. Research first (modules depend on
     * it); modules that no longer validate (removed from the catalog, research revoked) are
     * dropped with a warning instead of corrupting the loadout.
     */
    public static void restore(PlayerDoomData d, DoomSuit suit, ResearchProgress research, AnalysisLedger analysis,
                               ModuleCatalog catalog, Warnings w) {
        research.restore(d.researchCounters, d.researchCompleted, d.researchActive, d.researchActiveTicks);
        for (String s : d.researchCompleted)
            if (!research.has(s)) w.add("research: unknown node '" + s + "' dropped");
        SuitFrame frame = catalog.frame(d.frame);
        if (frame == null) {
            w.add("armor.frame: unknown frame '" + d.frame + "', using royal_mk1");
            frame = catalog.frame("royal_mk1");
        }
        suit.loadout().changeFrame(frame, research.completed());
        for (String m : d.modules) {
            List<LoadoutIssue> issues = suit.loadout().install(m, research.completed());
            if (!issues.isEmpty()) w.add("armor.modules: '" + m + "' not reinstalled (" + issues.get(0).detail() + ")");
        }
        suit.applyLoadout(research.completed());
        suit.energy().restore(d.energy, d.lastDrainTick);
        if (d.energy > suit.energy().capacity()) w.add("armor.energy above capacity; clamped");
        suit.heat().restore(d.heat, d.heatLocked);
        suit.focus().restore(d.focus);
        suit.restoreFlags(d.everInitialised);
        d.cooldowns.forEach((k, v) -> {
            if (suit.cooldowns().all().containsKey(k)) {
                Cooldown c = suit.cooldowns().get(k);
                c.restore((int) Math.min(Integer.MAX_VALUE, v[0]), v[1]);
            } else {
                w.add("armor.cooldowns: unknown ability '" + k + "' dropped");
            }
        });
        d.analysis.forEach((subject, rec) -> {
            Map<ObservationMethod, Integer> counts = new EnumMap<>(ObservationMethod.class);
            rec.counts.forEach((m, n) -> {
                try {
                    counts.put(ObservationMethod.valueOf(m), n);
                } catch (IllegalArgumentException ex) {
                    w.add("analysis." + subject + ": unknown method '" + m + "' dropped");
                }
            });
            analysis.restoreEntry(subject).restore(rec.knowledge, counts, rec.revealed, rec.countermeasures);
        });
    }
}
