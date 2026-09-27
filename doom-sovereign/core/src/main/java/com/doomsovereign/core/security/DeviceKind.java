package com.doomsovereign.core.security;

import java.util.EnumSet;
import java.util.Set;

/** Each kind of secured thing starts with sensible defaults for team and public access. */
public enum DeviceKind {
    MACHINE(EnumSet.of(Permission.VIEW, Permission.USE), EnumSet.of(Permission.VIEW)),
    SECURITY_DOOR(EnumSet.of(Permission.OPEN), EnumSet.noneOf(Permission.class)),
    TURRET(EnumSet.of(Permission.TURRET_EXEMPT, Permission.VIEW), EnumSet.noneOf(Permission.class)),
    FORCE_FIELD(EnumSet.of(Permission.PASS_FIELD), EnumSet.noneOf(Permission.class)),
    DOOMBOT(EnumSet.of(Permission.TURRET_EXEMPT, Permission.VIEW), EnumSet.noneOf(Permission.class)),
    SECURITY_CONTROLLER(EnumSet.of(Permission.VIEW), EnumSet.noneOf(Permission.class));

    private final Set<Permission> teamDefault;
    private final Set<Permission> publicDefault;

    DeviceKind(Set<Permission> teamDefault, Set<Permission> publicDefault) {
        this.teamDefault = teamDefault;
        this.publicDefault = publicDefault;
    }

    public EnumSet<Permission> teamDefault() {
        return teamDefault.isEmpty() ? EnumSet.noneOf(Permission.class) : EnumSet.copyOf(teamDefault);
    }

    public EnumSet<Permission> publicDefault() {
        return publicDefault.isEmpty() ? EnumSet.noneOf(Permission.class) : EnumSet.copyOf(publicDefault);
    }
}
