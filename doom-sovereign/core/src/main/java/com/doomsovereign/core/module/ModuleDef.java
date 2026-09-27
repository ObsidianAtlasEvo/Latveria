package com.doomsovereign.core.module;

import java.util.Map;
import java.util.Set;

/**
 * A module design.
 *
 * @param id               stable id (also the item id suffix)
 * @param family           mutually exclusive group (two thrusters cannot both be installed); may be null
 * @param slot             slot kind it occupies
 * @param capacityCost     power-budget points it uses
 * @param mass             added mass (heavy loadouts fly slower)
 * @param minTier          minimum suit tier
 * @param conflicts        module ids that cannot be installed alongside
 * @param requiresModules  module ids that must be installed too
 * @param requiresResearch research unlocks needed to install
 * @param stats            numeric effects
 * @param grants           behaviours switched on
 * @param summary          tooltip line describing the actual effect
 */
public record ModuleDef(String id, String family, SlotKind slot, int capacityCost, int mass, int minTier,
                        Set<String> conflicts, Set<String> requiresModules, Set<String> requiresResearch,
                        Map<Stat, Double> stats, Set<Capability> grants, String summary) {
    public ModuleDef {
        if (id == null || id.isBlank()) throw new IllegalArgumentException("id");
        if (capacityCost < 0 || mass < 0 || minTier < 1) throw new IllegalArgumentException("costs");
        conflicts = Set.copyOf(conflicts);
        requiresModules = Set.copyOf(requiresModules);
        requiresResearch = Set.copyOf(requiresResearch);
        stats = Map.copyOf(stats);
        grants = grants.isEmpty() ? Set.of() : Set.copyOf(grants);
    }
}
