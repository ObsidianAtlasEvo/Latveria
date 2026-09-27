package com.doomsovereign.core.energy;

/** Coarse state shown on the HUD and used to gate behaviour. */
public enum EnergyStatus {
    NOMINAL,
    /** Below the warning fraction: HUD turns amber, a single chime plays. */
    LOW,
    /** Only the emergency reserve remains: weapons and thrusters are refused. */
    RESERVE,
    /** Empty. The suit is still armour; only powered systems stop. */
    DEPLETED
}
