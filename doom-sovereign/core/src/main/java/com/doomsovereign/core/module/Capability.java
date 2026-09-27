package com.doomsovereign.core.module;

/**
 * Behaviour a module switches on. Capabilities, not percentages, are what make module choices
 * matter: a thruster that enables boost changes how you travel; +5 % speed does not.
 */
public enum Capability {
    BOOST,
    FALL_ARREST,
    UNDERWATER_PROPULSION,
    WATER_BREATHING,
    FIRE_IMMUNITY,
    LAVA_WADING,
    SPHERICAL_SHIELD,
    SUSTAINED_BEAM,
    TARGET_LEAD,
    DEEP_SCAN,
    ORE_DENSITY_SCAN,
    TELEPORT_STABILISED,
    ARCANE_INSULATION,
    CLOAK_CONCEALMENT,
    GROUND_SLAM_AMPLIFIED
}
