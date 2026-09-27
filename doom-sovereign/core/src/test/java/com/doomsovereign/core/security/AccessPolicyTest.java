package com.doomsovereign.core.security;

import com.doomsovereign.core.api.SecurityIdentity;
import com.doomsovereign.core.persist.Warnings;
import com.doomsovereign.core.persist.WorldDataCodec;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.util.EnumSet;
import java.util.List;
import java.util.Optional;
import java.util.Random;
import java.util.Set;
import java.util.UUID;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class AccessPolicyTest {
    static final UUID OWNER = new UUID(7, 1);
    static final UUID ALICE = new UUID(7, 2);
    static final UUID BOB = new UUID(7, 3);
    static final UUID EVE = new UUID(7, 4);
    static final SecurityIdentity O = SecurityIdentity.player(OWNER);
    static final SecurityIdentity A = SecurityIdentity.player(ALICE);
    static final SecurityIdentity B = SecurityIdentity.player(BOB);
    static final SecurityIdentity E = SecurityIdentity.player(EVE);

    @Test
    void ownerMayDoEverythingStrangersNothing() {
        AccessPolicy p = new AccessPolicy(OWNER, DeviceKind.DOOMBOT);
        for (Permission x : Permission.values()) {
            assertTrue(p.can(O, x));
            assertFalse(p.can(E, x), x.name());
        }
        assertEquals("not authorised", p.check(E, Permission.COMMAND).reason());
    }

    @Test
    void deviceDefaultsDiffer() {
        AccessPolicy machine = new AccessPolicy(OWNER, DeviceKind.MACHINE);
        assertTrue(machine.can(E, Permission.VIEW), "machines show their status publicly");
        assertFalse(machine.can(E, Permission.USE));
        AccessPolicy door = new AccessPolicy(OWNER, DeviceKind.SECURITY_DOOR);
        assertTrue(door.setTeam(O, "latveria", Set.of(Permission.OPEN)));
        assertTrue(door.can(SecurityIdentity.player(ALICE, "latveria"), Permission.OPEN));
        assertFalse(door.can(SecurityIdentity.player(ALICE, "symkaria"), Permission.OPEN));
        assertFalse(door.can(A, Permission.OPEN));
    }

    @Test
    void trustedPlayersCannotEscalate() {
        AccessPolicy p = new AccessPolicy(OWNER, DeviceKind.DOOMBOT);
        assertTrue(p.grant(O, ALICE, Set.of(Permission.CONFIGURE, Permission.VIEW, Permission.COMMAND)));
        assertTrue(p.grant(A, BOB, Set.of(Permission.VIEW)), "may pass on what she holds");
        assertFalse(p.grant(A, BOB, Set.of(Permission.CONFIGURE)), "never CONFIGURE");
        assertFalse(p.grant(A, BOB, Set.of(Permission.PASS_FIELD)), "not something she lacks");
        assertFalse(p.grant(B, EVE, Set.of(Permission.VIEW)), "Bob cannot configure");
        assertFalse(p.grant(O, OWNER, Set.of(Permission.VIEW)), "owner is not a trustee");
        assertFalse(p.grant(O, BOB, Set.of()), "empty grants are refused");
    }

    @Test
    void revocationRules() {
        AccessPolicy p = new AccessPolicy(OWNER, DeviceKind.MACHINE);
        p.grant(O, ALICE, Set.of(Permission.CONFIGURE, Permission.USE));
        p.grant(O, BOB, Set.of(Permission.USE, Permission.VIEW));
        assertTrue(p.revoke(A, BOB, Set.of(Permission.USE)));
        assertEquals(Set.of(Permission.VIEW), p.trusted().get(BOB));
        assertFalse(p.revoke(A, ALICE, null), "cannot revoke herself");
        p.grant(O, EVE, Set.of(Permission.CONFIGURE));
        assertFalse(p.revoke(A, EVE, null), "cannot revoke another configurer");
        assertTrue(p.revoke(O, EVE, null));
        assertFalse(p.trusted().containsKey(EVE));
        assertTrue(p.revoke(O, BOB, Set.of(Permission.VIEW)));
        assertFalse(p.trusted().containsKey(BOB), "empty trust entries disappear");
    }

    @Test
    void publicAndTeamCanNeverCarryControl() {
        AccessPolicy p = new AccessPolicy(OWNER, DeviceKind.DOOMBOT);
        assertFalse(p.setPublic(O, Set.of(Permission.COMMAND)));
        assertFalse(p.setPublic(O, Set.of(Permission.CONFIGURE)));
        assertFalse(p.setTeam(O, "t", Set.of(Permission.CONFIGURE)));
        assertFalse(p.setPublic(A, Set.of(Permission.VIEW)), "only the owner");
        assertTrue(p.setPublic(O, Set.of(Permission.VIEW)));
        assertTrue(p.can(E, Permission.VIEW));
    }

    @Test
    void adminOverrideIsOptIn() {
        AccessPolicy p = new AccessPolicy(OWNER, DeviceKind.TURRET);
        SecurityIdentity admin = new SecurityIdentity(EVE, Optional.empty(), true);
        assertFalse(p.can(admin, Permission.CONFIGURE));
        p.setAdminOverride(true);
        assertTrue(p.can(admin, Permission.CONFIGURE));
        assertFalse(p.can(E, Permission.CONFIGURE), "the flag on the identity is what matters");
    }

    @Test
    void transferLeavesTheOldOwnerWithNothing() {
        AccessPolicy p = new AccessPolicy(OWNER, DeviceKind.DOOMBOT);
        p.grant(O, ALICE, Set.of(Permission.VIEW));
        assertFalse(p.transfer(A, ALICE));
        assertTrue(p.transfer(O, ALICE));
        assertEquals(ALICE, p.owner());
        assertFalse(p.can(O, Permission.COMMAND));
        assertFalse(p.trusted().containsKey(ALICE), "the new owner is no longer a trustee");
    }

    @Test
    void engagementRulesProtectOwnersAndExemptPlayers() {
        AccessPolicy p = new AccessPolicy(OWNER, DeviceKind.TURRET);
        p.grant(O, ALICE, Set.of(Permission.TURRET_EXEMPT));
        assertFalse(EngagementRules.mayEngagePlayer(p, E, false, true, true), "PvP off");
        assertFalse(EngagementRules.mayEngagePlayer(p, O, true, true, true));
        assertFalse(EngagementRules.mayEngagePlayer(p, A, true, true, true));
        assertFalse(EngagementRules.mayEngagePlayer(p, E, true, false, false), "an innocent passer-by");
        assertTrue(EngagementRules.mayEngagePlayer(p, E, true, true, false));
        assertTrue(EngagementRules.mayEngagePlayer(p, E, true, false, true));
    }

    @Test
    void policiesSurviveSerialisation() {
        AccessPolicy p = new AccessPolicy(OWNER, DeviceKind.FORCE_FIELD);
        p.setTeam(O, "latveria", Set.of(Permission.PASS_FIELD, Permission.VIEW));
        p.setPublic(O, Set.of(Permission.VIEW));
        p.grant(O, ALICE, Set.of(Permission.CONFIGURE, Permission.PASS_FIELD));
        p.grant(O, BOB, Set.of(Permission.TURRET_EXEMPT));
        p.setAdminOverride(true);
        String json = WorldDataCodec.policy(p).toString();
        Warnings w = new Warnings();
        AccessPolicy q = WorldDataCodec.policy(JsonParser.parseString(json).getAsJsonObject(), w, "p");
        assertTrue(w.isEmpty(), w.all().toString());
        assertEquals(p.owner(), q.owner());
        assertEquals(p.kind(), q.kind());
        assertEquals(p.ownerTeam(), q.ownerTeam());
        assertEquals(p.teamPermissions(), q.teamPermissions());
        assertEquals(p.publicPermissions(), q.publicPermissions());
        assertEquals(p.trusted(), q.trusted());
        assertEquals(p.adminOverride(), q.adminOverride());
    }

    @Test
    void tamperedPoliciesAreSanitisedOnLoad() {
        String json = "{\"owner\":\"" + OWNER + "\",\"kind\":\"DOOMBOT\",\"publicPerms\":[\"COMMAND\",\"CONFIGURE\",\"VIEW\",\"FLY\"],"
                + "\"teamPerms\":[\"CONFIGURE\"],\"trusted\":{\"" + OWNER + "\":[\"VIEW\"],\"not-a-uuid\":[\"VIEW\"],\"" + ALICE + "\":[]}}";
        Warnings w = new Warnings();
        AccessPolicy q = WorldDataCodec.policy(JsonParser.parseString(json).getAsJsonObject(), w, "p");
        assertEquals(EnumSet.of(Permission.VIEW), EnumSet.copyOf(q.publicPermissions()), "control can never be public");
        assertTrue(q.teamPermissions().isEmpty());
        assertTrue(q.trusted().isEmpty());
        assertFalse(w.isEmpty());
        assertFalse(q.can(E, Permission.COMMAND));
        JsonObject noOwner = JsonParser.parseString("{\"kind\":\"TURRET\"}").getAsJsonObject();
        assertNull(WorldDataCodec.policy(noOwner, new Warnings(), "p"), "a policy without an owner is dropped, never ownerless-open");
    }

    /** Property test: random grant/revoke/transfer sequences by random actors never let a non-owner gain CONFIGURE by delegation. */
    @Test
    void randomDelegationNeverEscalates() {
        List<UUID> people = List.of(OWNER, ALICE, BOB, EVE);
        Permission[] all = Permission.values();
        for (int seed = 0; seed < 1000; seed++) {
            Random r = new Random(seed);
            AccessPolicy p = new AccessPolicy(OWNER, DeviceKind.values()[r.nextInt(DeviceKind.values().length)]);
            // only the owner ever hands out CONFIGURE; remember who received it from the owner
            java.util.Set<UUID> configurers = new java.util.HashSet<>();
            for (int step = 0; step < 50; step++) {
                SecurityIdentity actor = SecurityIdentity.player(people.get(r.nextInt(people.size())));
                UUID target = people.get(r.nextInt(people.size()));
                EnumSet<Permission> perms = EnumSet.noneOf(Permission.class);
                for (Permission x : all) if (r.nextInt(4) == 0) perms.add(x);
                boolean ownerActing = actor.id().equals(p.owner());
                switch (r.nextInt(5)) {
                    case 0, 1 -> {
                        if (p.grant(actor, target, perms) && perms.contains(Permission.CONFIGURE)) {
                            assertTrue(ownerActing, "seed " + seed + ": CONFIGURE granted by a non-owner");
                            configurers.add(target);
                        }
                    }
                    case 2 -> p.revoke(actor, target, r.nextBoolean() ? null : perms);
                    case 3 -> p.setPublic(actor, perms);
                    default -> { if (r.nextInt(10) == 0) p.transfer(actor, target); }
                }
                for (UUID u : people) {
                    if (u.equals(p.owner())) continue;
                    if (p.trusted().getOrDefault(u, Set.of()).contains(Permission.CONFIGURE))
                        assertTrue(configurers.contains(u), "seed " + seed + ": " + u + " configures without an owner grant");
                    assertFalse(p.publicPermissions().contains(Permission.COMMAND));
                }
            }
        }
    }
}
