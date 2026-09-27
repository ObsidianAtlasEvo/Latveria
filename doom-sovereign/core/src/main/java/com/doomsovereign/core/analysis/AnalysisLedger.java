package com.doomsovereign.core.analysis;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Doom Analysis (directive section 21): one player's knowledge of every creature they have studied.
 *
 * <p>Knowledge gain per observation is {@code base * DECAY^(times this method was used)}, never
 * below {@code MIN_GAIN}, and a method only counts once per its interval per subject. Varied
 * study (scan it, watch it attack, take a hit, defeat it, collect a sample) is therefore much
 * faster than repeating one thing - which is the Doom fantasy: preparation beats grind.
 */
public final class AnalysisLedger {
    public static final double DECAY = 0.8;
    public static final double MIN_GAIN = 0.5;

    private final ProfileRegistry profiles;
    private final Map<String, KnowledgeEntry> entries = new LinkedHashMap<>();

    public AnalysisLedger(ProfileRegistry profiles) {
        this.profiles = profiles;
    }

    public ObservationResult observe(String subjectId, ObservationMethod method, long now) {
        return observe(subjectId, method, now, 1.0);
    }

    /**
     * Records an observation.
     *
     * @param quality 0..1 multiplier (e.g. a scan interrupted early, a sensor array bonus above 1 is clamped)
     */
    public ObservationResult observe(String subjectId, ObservationMethod method, long now, double quality) {
        KnowledgeEntry e = entries.computeIfAbsent(subjectId, KnowledgeEntry::new);
        Long last = e.lastCounted(method);
        if (last != null && now - last < method.intervalTicks())
            return new ObservationResult(0, false, List.of(), List.of(), false);
        boolean wasComplete = e.complete();
        double q = Math.max(0, Math.min(1.5, Double.isFinite(quality) ? quality : 0));
        double gain = Math.max(MIN_GAIN, method.baseGain() * Math.pow(DECAY, e.count(method))) * q;
        e.count(method, now);
        double before = e.knowledge();
        e.add(gain);
        SubjectProfile p = profiles.profile(subjectId);
        List<String> revealed = new ArrayList<>();
        for (Trait t : p.traits()) {
            if (e.knowledge() + 1e-9 >= t.threshold() && (t.via() == null || e.used(t.via())) && e.reveal(t.id())) revealed.add(t.id());
        }
        List<String> unlocked = new ArrayList<>();
        for (Countermeasure c : p.countermeasures()) {
            if (e.knowledge() + 1e-9 >= c.minKnowledge() && e.revealed().containsAll(c.traits()) && e.unlock(c.id())) unlocked.add(c.id());
        }
        return new ObservationResult(e.knowledge() - before, true, revealed, unlocked, !wasComplete && e.complete());
    }

    public Optional<KnowledgeEntry> entry(String subjectId) {
        return Optional.ofNullable(entries.get(subjectId));
    }

    public double knowledge(String subjectId) {
        KnowledgeEntry e = entries.get(subjectId);
        return e == null ? 0 : e.knowledge();
    }

    /** Traits visible to the player for the HUD scan readout. */
    public List<Trait> visibleTraits(String subjectId) {
        KnowledgeEntry e = entries.get(subjectId);
        if (e == null) return List.of();
        return profiles.profile(subjectId).traits().stream().filter(t -> e.revealed().contains(t.id())).toList();
    }

    /** All countermeasures unlocked across every subject. */
    public List<String> allCountermeasures() {
        List<String> out = new ArrayList<>();
        for (KnowledgeEntry e : entries.values()) out.addAll(e.countermeasures());
        return out;
    }

    public Map<String, KnowledgeEntry> entries() {
        return Collections.unmodifiableMap(entries);
    }

    /** Used by persistence. */
    public KnowledgeEntry restoreEntry(String subjectId) {
        return entries.computeIfAbsent(subjectId, KnowledgeEntry::new);
    }

    public ProfileRegistry profiles() {
        return profiles;
    }
}
