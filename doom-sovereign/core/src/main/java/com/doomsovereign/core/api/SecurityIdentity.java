package com.doomsovereign.core.api;

import java.util.Optional;
import java.util.UUID;

/**
 * Who is trying to use something. Identity is always a UUID, never a name.
 *
 * @param id          player (or bot) UUID
 * @param team        optional team/ally group id (scoreboard team, faction, ...)
 * @param serverAdmin true for operators when the server config lets admins override security
 */
public record SecurityIdentity(UUID id, Optional<String> team, boolean serverAdmin) {
    public SecurityIdentity {
        java.util.Objects.requireNonNull(id, "id");
        team = team == null ? Optional.empty() : team;
    }

    public static SecurityIdentity player(UUID id) {
        return new SecurityIdentity(id, Optional.empty(), false);
    }

    public static SecurityIdentity player(UUID id, String team) {
        return new SecurityIdentity(id, Optional.ofNullable(team), false);
    }
}
