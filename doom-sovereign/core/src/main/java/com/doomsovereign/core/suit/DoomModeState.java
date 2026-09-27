package com.doomsovereign.core.suit;

public enum DoomModeState {
    /** Not all Royal pieces worn: ordinary armour behaviour, vanilla HUD. */
    INACTIVE,
    /** Plates lock, gauntlets initialise, mask seals, HUD fades in. */
    INITIALISING,
    ACTIVE,
    /** A piece was removed: systems wind down (cloak settles, HUD fades out). */
    SHUTTING_DOWN
}
