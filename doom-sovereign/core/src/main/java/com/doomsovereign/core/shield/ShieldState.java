package com.doomsovereign.core.shield;

public enum ShieldState {
    OFF,
    /** Projector spinning up (a few ticks): not yet absorbing. */
    RAISING,
    ACTIVE,
    /** Below the flicker fraction: visuals flicker, audio warns. */
    FAILING,
    /** Collapsed: cannot be raised until the collapse cooldown passes. */
    COLLAPSED
}
