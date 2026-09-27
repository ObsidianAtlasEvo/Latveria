package com.doomsovereign.core.security;

import com.doomsovereign.core.api.SecurityIdentity;

/**
 * Should a turret or Doombot shoot at this player? Mobs are decided by the AI; players only when
 * PvP is enabled server-side, they are not exempt, and (unless the device is set to "hostile to
 * all intruders") they have actually attacked something the device protects.
 */
public final class EngagementRules {
    private EngagementRules() {
    }

    public static boolean mayEngagePlayer(AccessPolicy policy, SecurityIdentity player, boolean pvpEnabled,
                                          boolean playerIsAggressor, boolean hostileToIntruders) {
        if (!pvpEnabled) return false;
        if (player.id().equals(policy.owner())) return false;
        if (policy.can(player, Permission.TURRET_EXEMPT)) return false;
        return playerIsAggressor || hostileToIntruders;
    }
}
