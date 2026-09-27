package com.doomsovereign.core.module;

import java.util.ArrayList;
import java.util.Collections;
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Modules installed in one suit. Installation is validated against the frame, the catalog and the
 * owner's research; nothing invalid can be installed, so the stat computation never has to guess.
 */
public final class Loadout {
    private final ModuleCatalog catalog;
    private SuitFrame frame;
    private final LinkedHashSet<String> installed = new LinkedHashSet<>();

    public Loadout(ModuleCatalog catalog, SuitFrame frame) {
        this.catalog = catalog;
        this.frame = frame;
    }

    /** Issues that would arise from adding {@code id}; empty means it can be installed. */
    public List<LoadoutIssue> check(String id, Set<String> research) {
        List<LoadoutIssue> out = new ArrayList<>();
        ModuleDef m = catalog.module(id);
        if (m == null) {
            out.add(new LoadoutIssue(LoadoutIssue.Kind.UNKNOWN_MODULE, id, "no such module"));
            return out;
        }
        if (installed.contains(id)) out.add(new LoadoutIssue(LoadoutIssue.Kind.DUPLICATE, id, "already installed"));
        if (m.minTier() > frame.tier())
            out.add(new LoadoutIssue(LoadoutIssue.Kind.TIER_TOO_LOW, id, "needs suit tier " + m.minTier()));
        for (String other : installed) {
            ModuleDef o = catalog.module(other);
            if (m.family() != null && m.family().equals(o.family()))
                out.add(new LoadoutIssue(LoadoutIssue.Kind.SAME_FAMILY, id, "replaces " + other + " (" + m.family() + ")"));
            if (m.conflicts().contains(other) || o.conflicts().contains(id))
                out.add(new LoadoutIssue(LoadoutIssue.Kind.CONFLICT, id, "conflicts with " + other));
        }
        for (String req : m.requiresModules())
            if (!installed.contains(req)) out.add(new LoadoutIssue(LoadoutIssue.Kind.MISSING_MODULE, id, "requires " + req));
        for (String r : m.requiresResearch())
            if (!research.contains(r)) out.add(new LoadoutIssue(LoadoutIssue.Kind.MISSING_RESEARCH, id, "requires research " + r));
        long usedSlots = installed.stream().map(catalog::module).filter(o -> o.slot() == m.slot()).count();
        if (usedSlots >= frame.slots(m.slot()))
            out.add(new LoadoutIssue(LoadoutIssue.Kind.NO_FREE_SLOT, id, "no free " + m.slot() + " slot"));
        if (capacityUsed() + m.capacityCost() > frame.capacity())
            out.add(new LoadoutIssue(LoadoutIssue.Kind.OVER_CAPACITY, id,
                    "needs " + m.capacityCost() + ", " + (frame.capacity() - capacityUsed()) + " free"));
        return out;
    }

    public List<LoadoutIssue> install(String id, Set<String> research) {
        List<LoadoutIssue> issues = check(id, research);
        if (issues.isEmpty()) installed.add(id);
        return issues;
    }

    /**
     * Removes a module. Refused (returns false) if another installed module requires it, so a
     * loadout can never become invalid by removal.
     */
    public boolean remove(String id) {
        if (!installed.contains(id)) return false;
        for (String other : installed)
            if (!other.equals(id) && catalog.module(other).requiresModules().contains(id)) return false;
        return installed.remove(id);
    }

    /** Changing frames keeps only modules that still fit, in install order. Returns dropped ids. */
    public List<String> changeFrame(SuitFrame newFrame, Set<String> research) {
        List<String> keep = new ArrayList<>(installed);
        installed.clear();
        frame = newFrame;
        List<String> dropped = new ArrayList<>();
        boolean progress = true;
        // retry until stable so modules whose prerequisites appear later still install
        while (progress) {
            progress = false;
            for (var it = keep.iterator(); it.hasNext(); ) {
                String id = it.next();
                if (check(id, research).isEmpty()) {
                    installed.add(id);
                    it.remove();
                    progress = true;
                }
            }
        }
        dropped.addAll(keep);
        return dropped;
    }

    public int capacityUsed() {
        return installed.stream().mapToInt(id -> catalog.module(id).capacityCost()).sum();
    }

    public int mass() {
        return installed.stream().mapToInt(id -> catalog.module(id).mass()).sum();
    }

    public Set<String> installed() {
        return Collections.unmodifiableSet(installed);
    }

    public SuitFrame frame() {
        return frame;
    }

    public SuitStats stats() {
        Map<Stat, Double> v = new EnumMap<>(Stat.class);
        for (Stat s : Stat.values()) v.put(s, s.identity());
        Set<Capability> caps = EnumSet.noneOf(Capability.class);
        apply(v, frame.base());
        for (String id : installed) {
            ModuleDef m = catalog.module(id);
            apply(v, m.stats());
            caps.addAll(m.grants());
        }
        int mass = mass();
        double penalty = 1.0;
        if (mass > frame.comfortableMass()) penalty = Math.max(0.5, frame.comfortableMass() / (double) mass);
        for (Stat s : EnumSet.of(Stat.CRUISE_SPEED_MULT, Stat.BOOST_SPEED_MULT, Stat.ACCELERATION_MULT))
            v.put(s, v.get(s) * penalty);
        return new SuitStats(v, caps, mass, capacityUsed(), penalty);
    }

    private static void apply(Map<Stat, Double> v, Map<Stat, Double> add) {
        for (var e : add.entrySet()) {
            Stat s = e.getKey();
            v.put(s, s.multiplicative() ? v.get(s) * e.getValue() : v.get(s) + e.getValue());
        }
    }
}
