package com.doomsovereign.core.module;

import java.util.Collection;
import java.util.Collections;
import java.util.EnumSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

import static com.doomsovereign.core.module.SlotKind.*;
import static com.doomsovereign.core.module.Stat.*;

/**
 * The module and frame designs. Kept in code (not JSON) because every entry is paired with game
 * logic that reads its capabilities; numbers are easy to move to data later if wanted.
 */
public final class ModuleCatalog {
    private final Map<String, ModuleDef> modules = new LinkedHashMap<>();
    private final Map<String, SuitFrame> frames = new LinkedHashMap<>();

    public ModuleDef module(String id) {
        return modules.get(id);
    }

    public SuitFrame frame(String id) {
        return frames.get(id);
    }

    public Collection<ModuleDef> modules() {
        return Collections.unmodifiableCollection(modules.values());
    }

    public Collection<SuitFrame> frames() {
        return Collections.unmodifiableCollection(frames.values());
    }

    public void add(ModuleDef m) {
        if (modules.putIfAbsent(m.id(), m) != null) throw new IllegalArgumentException("duplicate module " + m.id());
    }

    public void add(SuitFrame f) {
        if (frames.putIfAbsent(f.id(), f) != null) throw new IllegalArgumentException("duplicate frame " + f.id());
    }

    /** Validates cross references: every conflict/requirement names a real module. */
    public void validate() {
        for (ModuleDef m : modules.values()) {
            for (String c : m.conflicts()) if (!modules.containsKey(c)) throw new IllegalStateException(m.id() + " conflicts with unknown " + c);
            for (String r : m.requiresModules()) if (!modules.containsKey(r)) throw new IllegalStateException(m.id() + " requires unknown " + r);
            if (m.requiresModules().contains(m.id()) || m.conflicts().contains(m.id())) throw new IllegalStateException("self reference " + m.id());
        }
    }

    private static ModuleDef def(String id, String family, SlotKind slot, int cost, int mass, int tier, Set<String> conflicts,
                                 Set<String> reqMods, Set<String> reqResearch, Map<Stat, Double> stats, Set<Capability> caps,
                                 String summary) {
        return new ModuleDef(id, family, slot, cost, mass, tier, conflicts, reqMods, reqResearch, stats, caps, summary);
    }

    private static Set<Capability> caps(Capability... c) {
        return c.length == 0 ? Set.of() : EnumSet.of(c[0], c);
    }

    public static ModuleCatalog standard() {
        ModuleCatalog c = new ModuleCatalog();
        // --- mobility -----------------------------------------------------------------------------
        c.add(def("thruster_mk1", "thrusters", MOBILITY, 2, 2, 1, Set.of(), Set.of(), Set.of("repulsor_levitation"),
                Map.of(), caps(), "Standard repulsor thrusters. Enables controlled flight."));
        c.add(def("thruster_mk2", "thrusters", MOBILITY, 4, 3, 2, Set.of(), Set.of(), Set.of("afterburner_lattice"),
                Map.of(CRUISE_SPEED_MULT, 1.25, BOOST_SPEED_MULT, 1.35, ACCELERATION_MULT, 1.3, FLIGHT_COST_MULT, 1.15),
                caps(Capability.BOOST), "Afterburner thrusters. Unlocks boost; faster, hungrier."));
        c.add(def("kinetic_dampener", null, MOBILITY, 2, 2, 1, Set.of(), Set.of(), Set.of(),
                Map.of(FALL_DAMAGE_MULT, 0.4, KNOCKBACK_RESIST_ADD, 0.25), caps(Capability.FALL_ARREST, Capability.GROUND_SLAM_AMPLIFIED),
                "Absorbs impacts. Emergency fall arrest and a harder ground slam."));
        c.add(def("aquatic_impellers", null, MOBILITY, 2, 1, 1, Set.of(), Set.of("environmental_seal"), Set.of("pressure_hull"),
                Map.of(), caps(Capability.UNDERWATER_PROPULSION), "Water-jet impellers for full-speed underwater movement."));
        // --- core ---------------------------------------------------------------------------------
        c.add(def("capacitor_standard", "capacitor", CORE, 2, 2, 1, Set.of(), Set.of(), Set.of(),
                Map.of(ENERGY_CAPACITY_MULT, 1.5), caps(), "Adds 50 % armour energy capacity."));
        c.add(def("capacitor_dense", "capacitor", CORE, 4, 5, 2, Set.of(), Set.of(), Set.of("vibranium_lattice"),
                Map.of(ENERGY_CAPACITY_MULT, 2.5, ENERGY_REGEN_ADD, 1.0), caps(),
                "Dense capacitor: 2.5x capacity and faster self-charge, but heavy."));
        c.add(def("thermal_management", null, CORE, 2, 1, 1, Set.of(), Set.of(), Set.of(),
                Map.of(PASSIVE_COOLING_ADD, 0.25, ACTIVE_COOLING_ADD, 1.0), caps(Capability.FIRE_IMMUNITY),
                "Coolant loops: gauntlets shed heat quickly after firing; immune to fire."));
        c.add(def("environmental_seal", null, CORE, 2, 1, 1, Set.of(), Set.of(), Set.of("pressure_hull"),
                Map.of(), caps(Capability.WATER_BREATHING), "Sealed suit: breathe underwater and in foul air."));
        // --- defense ------------------------------------------------------------------------------
        c.add(def("shield_emitter_directional", "shield_emitter", DEFENSE, 2, 1, 1, Set.of(), Set.of(), Set.of(),
                Map.of(SHIELD_CAPACITY_MULT, 1.3), caps(), "Focused frontal field: +30 % capacity, facing matters."));
        c.add(def("shield_emitter_spherical", "shield_emitter", DEFENSE, 4, 2, 2, Set.of(), Set.of(), Set.of("omnidirectional_fields"),
                Map.of(SHIELD_COST_MULT, 1.1), caps(Capability.SPHERICAL_SHIELD), "Spherical field projector: protects from every side."));
        c.add(def("arcane_insulation", null, DEFENSE, 3, 1, 2, Set.of("teleport_stabilizer"), Set.of(), Set.of("wardcraft"),
                Map.of(ARCANE_INSULATION_ADD, 0.5, FOCUS_RECOVERY_MULT, 0.8), caps(Capability.ARCANE_INSULATION),
                "Warded lining: the field stops sorcery too. Dulls your own focus recovery."));
        // --- weapons ------------------------------------------------------------------------------
        c.add(def("gauntlet_focusing", null, WEAPON, 3, 1, 2, Set.of(), Set.of("thermal_management"), Set.of("coherent_emitters"),
                Map.of(WEAPON_DAMAGE_MULT, 1.25, CHARGE_TIME_MULT, 0.75), caps(Capability.SUSTAINED_BEAM),
                "Focusing lenses: sustained beam, faster charge. Needs coolant loops."));
        c.add(def("targeting_suite", null, SENSOR, 1, 0, 1, Set.of(), Set.of(), Set.of(),
                Map.of(WEAPON_COST_MULT, 0.9), caps(Capability.TARGET_LEAD), "Ballistic computer: leads moving targets."));
        c.add(def("sensor_array", null, SENSOR, 2, 1, 1, Set.of(), Set.of(), Set.of(),
                Map.of(SENSOR_RANGE_ADD, 24.0), caps(Capability.DEEP_SCAN, Capability.ORE_DENSITY_SCAN),
                "Deep sensors: longer scans, weak-point readout and ore density."));
        // --- arcane -------------------------------------------------------------------------------
        c.add(def("teleport_stabilizer", null, ARCANE, 3, 1, 2, Set.of("arcane_insulation"), Set.of(), Set.of("dimensional_theory"),
                Map.of(TELEPORT_RANGE_ADD, 16.0), caps(Capability.TELEPORT_STABILISED),
                "Anchors translocation: longer, safer teleports. Incompatible with arcane insulation."));
        c.add(def("cloak_concealment", null, ARCANE, 2, 0, 3, Set.of(), Set.of(), Set.of("veil_of_the_mask"),
                Map.of(), caps(Capability.CLOAK_CONCEALMENT), "Enchanted cloak: mobs lose track of you while you stand still."));
        // --- frames -------------------------------------------------------------------------------
        c.add(new SuitFrame("royal_mk1", 1, 8, 8, Map.of(CORE, 2, MOBILITY, 2, DEFENSE, 1, WEAPON, 1, SENSOR, 1, ARCANE, 0), Map.of()));
        c.add(new SuitFrame("royal_mk2", 2, 14, 11, Map.of(CORE, 2, MOBILITY, 2, DEFENSE, 2, WEAPON, 1, SENSOR, 2, ARCANE, 1), Map.of()));
        c.add(new SuitFrame("siege", 2, 14, 16, Map.of(CORE, 3, MOBILITY, 1, DEFENSE, 3, WEAPON, 2, SENSOR, 1, ARCANE, 0),
                Map.of(KNOCKBACK_RESIST_ADD, 0.5, SHIELD_CAPACITY_MULT, 1.3, CRUISE_SPEED_MULT, 0.8)));
        c.add(new SuitFrame("arcane_sovereign", 3, 14, 10, Map.of(CORE, 2, MOBILITY, 2, DEFENSE, 2, WEAPON, 1, SENSOR, 1, ARCANE, 3),
                Map.of(FOCUS_RECOVERY_MULT, 1.5, ARCANE_INSULATION_ADD, 0.2)));
        c.add(new SuitFrame("technological_supremacy", 3, 18, 12, Map.of(CORE, 3, MOBILITY, 2, DEFENSE, 2, WEAPON, 2, SENSOR, 2, ARCANE, 0),
                Map.of(ENERGY_CAPACITY_MULT, 1.3, ENERGY_REGEN_ADD, 1.0)));
        c.validate();
        return c;
    }
}
