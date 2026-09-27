package com.doomsovereign.core.analysis;

import java.util.Collections;
import java.util.EnumMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;

/** Everything one player knows about one subject. */
public final class KnowledgeEntry {
    public static final double MAX = 100;
    private final String subjectId;
    private double knowledge;
    private final Map<ObservationMethod, Integer> counts = new EnumMap<>(ObservationMethod.class);
    private final Map<ObservationMethod, Long> lastCounted = new EnumMap<>(ObservationMethod.class);
    private final LinkedHashSet<String> revealed = new LinkedHashSet<>();
    private final LinkedHashSet<String> countermeasures = new LinkedHashSet<>();

    public KnowledgeEntry(String subjectId) {
        this.subjectId = subjectId;
    }

    public String subjectId() { return subjectId; }

    public double knowledge() { return knowledge; }

    public boolean complete() { return knowledge >= MAX - 1e-9; }

    public int count(ObservationMethod m) { return counts.getOrDefault(m, 0); }

    public boolean used(ObservationMethod m) { return count(m) > 0; }

    public Set<String> revealed() { return Collections.unmodifiableSet(revealed); }

    public Set<String> countermeasures() { return Collections.unmodifiableSet(countermeasures); }

    Long lastCounted(ObservationMethod m) { return lastCounted.get(m); }

    void count(ObservationMethod m, long now) {
        counts.merge(m, 1, Integer::sum);
        lastCounted.put(m, now);
    }

    void add(double k) {
        knowledge = Math.min(MAX, knowledge + k);
    }

    boolean reveal(String trait) { return revealed.add(trait); }

    boolean unlock(String cm) { return countermeasures.add(cm); }

    Map<ObservationMethod, Integer> counts() { return counts; }

    /** Restores persisted state with clamping. */
    public void restore(double k, Map<ObservationMethod, Integer> savedCounts, Set<String> savedRevealed, Set<String> savedCms) {
        knowledge = Double.isFinite(k) ? Math.max(0, Math.min(MAX, k)) : 0;
        counts.clear();
        savedCounts.forEach((m, c) -> { if (c != null && c > 0) counts.put(m, c); });
        revealed.clear();
        revealed.addAll(savedRevealed);
        countermeasures.clear();
        countermeasures.addAll(savedCms);
    }

    public Map<ObservationMethod, Integer> methodCounts() {
        return Collections.unmodifiableMap(counts);
    }
}
