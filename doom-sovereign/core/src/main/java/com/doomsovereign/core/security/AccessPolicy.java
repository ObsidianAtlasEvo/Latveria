package com.doomsovereign.core.security;

import com.doomsovereign.core.api.SecurityIdentity;
import java.util.Collections;
import java.util.EnumSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

/**
 * Who may do what with one secured device (or a group linked to a Security Controller).
 *
 * <p>Rules: the owner may do everything; trusted players hold explicit permissions; members of the
 * owner's team get the team set; everyone else gets the public set. A trusted player with
 * CONFIGURE may grant only permissions they hold themselves and can never grant CONFIGURE, so
 * nobody can escalate their way into seizing someone else's robots. Server admins bypass
 * security only when the server config enables it.
 */
public final class AccessPolicy {
    private UUID owner;
    private final DeviceKind kind;
    private Optional<String> ownerTeam = Optional.empty();
    private final Map<UUID, EnumSet<Permission>> trusted = new LinkedHashMap<>();
    private EnumSet<Permission> teamPermissions;
    private EnumSet<Permission> publicPermissions;
    private boolean adminOverride;

    public AccessPolicy(UUID owner, DeviceKind kind) {
        this.owner = Objects.requireNonNull(owner);
        this.kind = kind;
        this.teamPermissions = kind.teamDefault();
        this.publicPermissions = kind.publicDefault();
    }

    public AccessDecision check(SecurityIdentity who, Permission p) {
        if (who.id().equals(owner)) return AccessDecision.allow("owner");
        if (who.serverAdmin() && adminOverride) return AccessDecision.allow("server admin override");
        EnumSet<Permission> t = trusted.get(who.id());
        if (t != null && t.contains(p)) return AccessDecision.allow("trusted");
        if (ownerTeam.isPresent() && who.team().equals(ownerTeam) && teamPermissions.contains(p)) return AccessDecision.allow("team");
        if (publicPermissions.contains(p)) return AccessDecision.allow("public");
        return AccessDecision.deny(t != null ? "trusted, but not for " + p : "not authorised");
    }

    public boolean can(SecurityIdentity who, Permission p) {
        return check(who, p).allowed();
    }

    /** Grants {@code perms} to {@code target} on behalf of {@code actor}. Returns false if refused. */
    public boolean grant(SecurityIdentity actor, UUID target, Set<Permission> perms) {
        if (target.equals(owner) || perms.isEmpty()) return false;
        boolean isOwner = actor.id().equals(owner);
        if (!isOwner) {
            if (!can(actor, Permission.CONFIGURE)) return false;
            if (perms.contains(Permission.CONFIGURE)) return false;
            for (Permission p : perms) if (!can(actor, p)) return false;
        }
        trusted.computeIfAbsent(target, k -> EnumSet.noneOf(Permission.class)).addAll(perms);
        return true;
    }

    /** Revokes permissions (or all trust when {@code perms} is null). Owner, or CONFIGURE holders for non-CONFIGURE perms. */
    public boolean revoke(SecurityIdentity actor, UUID target, Set<Permission> perms) {
        boolean isOwner = actor.id().equals(owner);
        EnumSet<Permission> t = trusted.get(target);
        if (t == null) return false;
        if (!isOwner) {
            if (!can(actor, Permission.CONFIGURE) || target.equals(actor.id())) return false;
            if (t.contains(Permission.CONFIGURE)) return false;
        }
        if (perms == null) trusted.remove(target);
        else {
            t.removeAll(perms);
            if (t.isEmpty()) trusted.remove(target);
        }
        return true;
    }

    /** Only the owner can transfer ownership. The previous owner keeps no rights. */
    public boolean transfer(SecurityIdentity actor, UUID newOwner) {
        if (!actor.id().equals(owner)) return false;
        trusted.remove(newOwner);
        owner = newOwner;
        return true;
    }

    public boolean setPublic(SecurityIdentity actor, Set<Permission> perms) {
        if (!actor.id().equals(owner)) return false;
        if (perms.contains(Permission.CONFIGURE) || perms.contains(Permission.COMMAND)) return false;
        publicPermissions = perms.isEmpty() ? EnumSet.noneOf(Permission.class) : EnumSet.copyOf(perms);
        return true;
    }

    public boolean setTeam(SecurityIdentity actor, String team, Set<Permission> perms) {
        if (!actor.id().equals(owner)) return false;
        if (perms.contains(Permission.CONFIGURE)) return false;
        ownerTeam = Optional.ofNullable(team);
        teamPermissions = perms.isEmpty() ? EnumSet.noneOf(Permission.class) : EnumSet.copyOf(perms);
        return true;
    }

    public void setAdminOverride(boolean enabled) {
        adminOverride = enabled;
    }

    public UUID owner() { return owner; }

    public DeviceKind kind() { return kind; }

    public Optional<String> ownerTeam() { return ownerTeam; }

    public Map<UUID, Set<Permission>> trusted() {
        Map<UUID, Set<Permission>> m = new LinkedHashMap<>();
        trusted.forEach((k, v) -> m.put(k, Collections.unmodifiableSet(EnumSet.copyOf(v))));
        return Collections.unmodifiableMap(m);
    }

    public Set<Permission> teamPermissions() { return Collections.unmodifiableSet(teamPermissions); }

    public Set<Permission> publicPermissions() { return Collections.unmodifiableSet(publicPermissions); }

    public boolean adminOverride() { return adminOverride; }

    /** Persistence: restores fields without permission checks (called by the codec only). */
    public void restore(Optional<String> team, EnumSet<Permission> teamPerms, EnumSet<Permission> publicPerms,
                        Map<UUID, EnumSet<Permission>> savedTrusted, boolean override) {
        ownerTeam = team;
        teamPermissions = EnumSet.copyOf(teamPerms);
        publicPermissions = EnumSet.copyOf(publicPerms);
        publicPermissions.remove(Permission.CONFIGURE);
        publicPermissions.remove(Permission.COMMAND);
        teamPermissions.remove(Permission.CONFIGURE);
        trusted.clear();
        savedTrusted.forEach((k, v) -> { if (!k.equals(owner) && !v.isEmpty()) trusted.put(k, EnumSet.copyOf(v)); });
        adminOverride = override;
    }
}
