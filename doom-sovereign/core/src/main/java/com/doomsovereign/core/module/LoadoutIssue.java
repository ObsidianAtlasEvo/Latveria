package com.doomsovereign.core.module;

/** Why a loadout (or a single install) is not valid; shown in the Armor Cradle UI. */
public record LoadoutIssue(Kind kind, String moduleId, String detail) {
    public enum Kind { UNKNOWN_MODULE, DUPLICATE, SAME_FAMILY, CONFLICT, MISSING_MODULE, MISSING_RESEARCH, TIER_TOO_LOW,
        NO_FREE_SLOT, OVER_CAPACITY }
}
