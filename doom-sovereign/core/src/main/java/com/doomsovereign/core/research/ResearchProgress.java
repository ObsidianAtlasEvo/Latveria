package com.doomsovereign.core.research;

import com.doomsovereign.core.api.ResearchEvent;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * One player's research state: recorded accomplishments, completed nodes and the project running
 * on the console. Recording events never completes a node on its own unless the node is marked
 * automatic (consoleTicks == 0): research is something Doom <em>does</em>.
 */
public final class ResearchProgress {
    public enum Status { LOCKED, BLOCKED_BY_PREREQUISITES, IN_PROGRESS_REQUIREMENTS, READY, RESEARCHING, COMPLETE }

    private final ResearchTree tree;
    private final Map<String, Integer> counters = new HashMap<>();
    private final LinkedHashSet<String> completed = new LinkedHashSet<>();
    private String active;
    private int activeTicks;

    public ResearchProgress(ResearchTree tree) {
        this.tree = tree;
    }

    /** Records an event; returns node ids that completed automatically as a result. */
    public List<String> record(ResearchEvent e) {
        counters.merge(e.type() + "|" + e.key(), e.amount(), (a, b) -> (int) Math.min(Integer.MAX_VALUE, (long) a + b));
        return autoComplete();
    }

    private List<String> autoComplete() {
        List<String> done = new java.util.ArrayList<>();
        boolean changed = true;
        while (changed) {
            changed = false;
            for (ResearchNode n : tree.nodes()) {
                if (n.consoleTicks() == 0 && status(n.id()) == Status.READY) {
                    completed.add(n.id());
                    done.add(n.id());
                    changed = true;
                }
            }
        }
        return done;
    }

    public int count(Requirement r) {
        return counters.getOrDefault(r.counterKey(), 0);
    }

    /** 0..1 progress of a node's requirements. */
    public double requirementProgress(String id) {
        ResearchNode n = tree.node(id);
        if (n.requirements().isEmpty()) return 1.0;
        double sum = 0;
        for (Requirement r : n.requirements()) sum += Math.min(1.0, count(r) / (double) r.count());
        return sum / n.requirements().size();
    }

    public Status status(String id) {
        ResearchNode n = tree.node(id);
        if (n == null) throw new IllegalArgumentException("unknown research " + id);
        if (completed.contains(id)) return Status.COMPLETE;
        if (id.equals(active)) return Status.RESEARCHING;
        if (!completed.containsAll(n.prerequisites())) {
            boolean anyPrereqStarted = n.prerequisites().stream().anyMatch(completed::contains);
            return anyPrereqStarted || n.prerequisites().isEmpty() ? Status.BLOCKED_BY_PREREQUISITES : Status.LOCKED;
        }
        for (Requirement r : n.requirements()) if (count(r) < r.count()) return Status.IN_PROGRESS_REQUIREMENTS;
        return Status.READY;
    }

    /** Starts console research on a READY node. Returns false if not ready or another project runs. */
    public boolean begin(String id) {
        if (active != null || status(id) != Status.READY) return false;
        active = id;
        activeTicks = 0;
        return true;
    }

    /** Advances console research by one tick while the console is powered and attended. */
    public String tickConsole() {
        if (active == null) return null;
        activeTicks++;
        if (activeTicks >= tree.node(active).consoleTicks()) {
            String done = active;
            completed.add(done);
            active = null;
            activeTicks = 0;
            autoComplete();
            return done;
        }
        return null;
    }

    public void cancel() {
        active = null;
        activeTicks = 0;
    }

    public double consoleProgress() {
        return active == null ? 0 : activeTicks / (double) tree.node(active).consoleTicks();
    }

    /** Human-readable reasons a node is not yet available (for tooltips: no mystery failures). */
    public List<String> missing(String id) {
        ResearchNode n = tree.node(id);
        List<String> out = new java.util.ArrayList<>();
        for (String p : n.prerequisites())
            if (!completed.contains(p)) out.add("Research " + tree.node(p).title());
        for (Requirement r : n.requirements())
            if (count(r) < r.count()) out.add(r.type() + " " + r.key() + " " + count(r) + "/" + r.count());
        return out;
    }

    public Set<String> completed() {
        return Collections.unmodifiableSet(completed);
    }

    public boolean has(String id) {
        return completed.contains(id);
    }

    public Set<String> available() {
        return tree.nodes().stream().map(ResearchNode::id).filter(i -> status(i) == Status.READY).collect(Collectors.toCollection(LinkedHashSet::new));
    }

    public String active() { return active; }

    public int activeTicks() { return activeTicks; }

    public Map<String, Integer> counters() { return Collections.unmodifiableMap(counters); }

    public ResearchTree tree() { return tree; }

    /** Restores persisted state; unknown node ids are dropped rather than failing the load. */
    public void restore(Map<String, Integer> savedCounters, Set<String> savedCompleted, String savedActive, int savedTicks) {
        counters.clear();
        savedCounters.forEach((k, v) -> { if (v != null && v > 0) counters.put(k, v); });
        completed.clear();
        for (String s : savedCompleted) if (tree.node(s) != null) completed.add(s);
        active = savedActive != null && tree.node(savedActive) != null && !completed.contains(savedActive) ? savedActive : null;
        activeTicks = active == null ? 0 : Math.max(0, savedTicks);
    }
}
