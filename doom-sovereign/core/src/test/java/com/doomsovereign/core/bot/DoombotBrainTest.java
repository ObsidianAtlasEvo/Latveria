package com.doomsovereign.core.bot;

import com.doomsovereign.core.api.BotWorldAdapter;
import com.doomsovereign.core.api.SecurityIdentity;
import com.doomsovereign.core.security.Permission;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Random;
import java.util.Set;
import java.util.UUID;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class DoombotBrainTest {
    static final UUID OWNER = new UUID(0, 1);
    static final UUID STRANGER = new UUID(0, 2);
    static final UUID FRIEND = new UUID(0, 3);
    static final UUID BOT = new UUID(0, 100);
    static final SecurityIdentity OWNER_ID = SecurityIdentity.player(OWNER);

    static BotLocation at(double x, double z) {
        return new BotLocation("minecraft:overworld", x, 64, z);
    }

    static final class World implements BotWorldAdapter {
        long time;
        BotLocation self = at(0, 0);
        BotLocation owner = at(2, 0);
        double health = 1;
        final Map<UUID, BotLocation> entities = new HashMap<>();
        final List<Contact> contacts = new ArrayList<>();

        @Override public long gameTime() { return time; }
        @Override public BotLocation selfLocation() { return self; }
        @Override public Optional<BotLocation> ownerLocation() { return Optional.ofNullable(owner); }
        @Override public Optional<BotLocation> locate(UUID e) { return Optional.ofNullable(entities.get(e)); }
        @Override public List<Contact> contacts() { return contacts; }
        @Override public double selfHealth() { return health; }

        void mob(UUID id, BotLocation where, boolean attackingOwner, boolean attackingSelf) {
            entities.put(id, where);
            contacts.add(new Contact(id, where, true, attackingOwner, attackingSelf, false));
        }
    }

    static DoombotBrain brain() {
        return new DoombotBrain(BOT, OWNER, BotConfig.defaults());
    }

    @Test
    void onlyAuthorisedIdentitiesMayCommand() {
        DoombotBrain b = brain();
        assertEquals(CommandResult.DENIED_NOT_AUTHORISED, b.issue(SecurityIdentity.player(STRANGER), BotOrder.passive(), 0));
        assertEquals(BotCommand.FOLLOW, b.order().command());
        assertEquals(CommandResult.ACCEPTED, b.issue(OWNER_ID, BotOrder.passive(), 0));
        assertTrue(b.policy().grant(OWNER_ID, FRIEND, Set.of(Permission.COMMAND)));
        assertEquals(CommandResult.ACCEPTED, b.issue(SecurityIdentity.player(FRIEND), BotOrder.follow(), 1));
        assertFalse(b.setHome(SecurityIdentity.player(FRIEND), at(5, 5)), "COMMAND is not CONFIGURE");
        assertTrue(b.setHome(OWNER_ID, at(5, 5)));
    }

    @Test
    void invalidOrdersAreRejected() {
        DoombotBrain b = brain();
        assertEquals(CommandResult.INVALID_ORDER, b.issue(OWNER_ID, BotOrder.attack(null), 0));
        assertEquals(CommandResult.INVALID_ORDER, b.issue(OWNER_ID, BotOrder.attack(BOT), 0), "cannot attack itself");
        assertEquals(CommandResult.INVALID_ORDER, b.issue(OWNER_ID, BotOrder.patrol(List.of(at(1, 1))), 0));
        assertEquals(CommandResult.INVALID_ORDER, b.issue(OWNER_ID, BotOrder.defend(at(0, 0), 0), 0));
        assertEquals(CommandResult.INVALID_ORDER, b.issue(OWNER_ID, BotOrder.defend(at(0, 0), 49), 0), "radius over server max");
        assertEquals(CommandResult.INVALID_ORDER, b.issue(OWNER_ID, BotOrder.stay(null), 0));
        assertEquals(CommandResult.INVALID_ORDER, b.issue(OWNER_ID, BotOrder.returnHome(), 0), "no home set");
        assertEquals(CommandResult.REFUSED_FRIENDLY_TARGET, b.issue(OWNER_ID, BotOrder.attack(OWNER), 0));
        b.policy().grant(OWNER_ID, FRIEND, Set.of(Permission.VIEW));
        assertEquals(CommandResult.REFUSED_FRIENDLY_TARGET, b.issue(OWNER_ID, BotOrder.attack(FRIEND), 0));
        assertEquals(BotCommand.FOLLOW, b.order().command(), "rejections leave the order untouched");
    }

    @Test
    void followKeepsCloseAndTeleportsWhenFarBehind() {
        DoombotBrain b = brain();
        World w = new World();
        assertEquals(BotIntent.Type.IDLE, b.decide(w).type());
        w.owner = at(10, 0);
        BotIntent i = b.decide(w);
        assertEquals(BotIntent.Type.MOVE_TO, i.type());
        assertEquals(w.owner, i.location());
        w.owner = at(40, 0);
        w.time = 200;
        assertEquals(BotIntent.Type.TELEPORT_TO_OWNER, b.decide(w).type());
        w.time = 250;
        assertEquals(BotIntent.Type.MOVE_TO, b.decide(w).type(), "teleport cooldown");
        w.time = 300;
        assertEquals(BotIntent.Type.TELEPORT_TO_OWNER, b.decide(w).type());
    }

    @Test
    void neverChasesAcrossDimensions() {
        DoombotBrain b = brain();
        World w = new World();
        w.owner = new BotLocation("minecraft:the_nether", 1, 64, 1);
        for (long t = 0; t < 400; t += 10) {
            w.time = t;
            BotIntent i = b.decide(w);
            assertEquals(BotIntent.Type.HOLD, i.type(), "tick " + t);
        }
        w.owner = null;
        assertEquals(BotIntent.Type.HOLD, b.decide(w).type());
        assertTrue(b.awaitingOwner());
    }

    @Test
    void defendsTheOwnerFromAttackers() {
        DoombotBrain b = brain();
        World w = new World();
        UUID zombie = UUID.randomUUID();
        w.mob(zombie, at(6, 0), true, false);
        BotIntent i = b.decide(w);
        assertEquals(BotIntent.Type.ATTACK, i.type());
        assertEquals(zombie, i.target());
    }

    @Test
    void prefersTheMostDangerousThreat() {
        DoombotBrain b = brain();
        World w = new World();
        UUID idle = UUID.randomUUID(), hittingMe = UUID.randomUUID(), hittingOwner = UUID.randomUUID();
        w.mob(idle, at(3, 0), false, false);
        w.mob(hittingMe, at(4, 0), false, true);
        w.mob(hittingOwner, at(8, 0), true, false);
        assertEquals(hittingOwner, b.decide(w).target());
    }

    @Test
    void playersAreOnlyEngagedWithPvpAndProvocation() {
        World w = new World();
        UUID griefer = UUID.randomUUID();
        w.entities.put(griefer, at(5, 0));
        w.contacts.add(new BotWorldAdapter.Contact(griefer, at(5, 0), false, true, false, true));
        assertNotEquals(BotIntent.Type.ATTACK, brain().decide(w).type(), "PvP off by default");
        BotConfig pvp = new BotConfig(4, 28, 100, 12, 6, 48, 0.25, 200, 600, true);
        DoombotBrain b = new DoombotBrain(BOT, OWNER, pvp);
        assertEquals(BotIntent.Type.ATTACK, b.decide(w).type());
        World w2 = new World();
        w2.contacts.add(new BotWorldAdapter.Contact(STRANGER, at(5, 0), false, false, false, true));
        assertNotEquals(BotIntent.Type.ATTACK, new DoombotBrain(BOT, OWNER, pvp).decide(w2).type(), "bystanders are safe");
        World w3 = new World();
        w3.contacts.add(new BotWorldAdapter.Contact(OWNER, at(1, 0), true, true, true, true));
        assertNotEquals(BotIntent.Type.ATTACK, new DoombotBrain(BOT, OWNER, pvp).decide(w3).type(), "never the owner");
    }

    @Test
    void passiveBotsNeverFight() {
        DoombotBrain b = brain();
        b.issue(OWNER_ID, BotOrder.passive(), 0);
        World w = new World();
        w.mob(UUID.randomUUID(), at(2, 0), true, true);
        assertNotEquals(BotIntent.Type.ATTACK, b.decide(w).type());
    }

    @Test
    void stayHoldsPostAndDefendsOnlyNearby() {
        DoombotBrain b = brain();
        BotLocation post = at(20, 20);
        b.issue(OWNER_ID, BotOrder.stay(post), 0);
        World w = new World();
        w.self = at(10, 10);
        assertEquals(BotIntent.Type.MOVE_TO, b.decide(w).type());
        w.self = post;
        assertEquals(BotIntent.Type.HOLD, b.decide(w).type());
        w.mob(UUID.randomUUID(), at(40, 20), false, false);
        assertEquals(BotIntent.Type.HOLD, b.decide(w).type(), "a distant idle mob is ignored");
        UUID near = UUID.randomUUID();
        w.mob(near, at(24, 20), false, false);
        assertEquals(near, b.decide(w).target());
    }

    @Test
    void patrolCyclesWaypoints() {
        DoombotBrain b = brain();
        List<BotLocation> route = List.of(at(0, 0), at(10, 0), at(10, 10));
        assertEquals(CommandResult.ACCEPTED, b.issue(OWNER_ID, BotOrder.patrol(route), 0));
        World w = new World();
        w.self = at(0, 0);
        assertEquals(route.get(1), b.decide(w).location());
        w.self = at(10, 0);
        assertEquals(route.get(2), b.decide(w).location());
        w.self = at(10, 10);
        assertEquals(route.get(0), b.decide(w).location(), "wraps around");
    }

    @Test
    void attackOrdersGiveUpAndResumeThePreviousOrder() {
        DoombotBrain b = brain();
        BotLocation post = at(5, 5);
        b.issue(OWNER_ID, BotOrder.stay(post), 0);
        UUID target = UUID.randomUUID();
        assertEquals(CommandResult.ACCEPTED, b.issue(OWNER_ID, BotOrder.attack(target), 0));
        World w = new World();
        w.entities.put(target, at(9, 9));
        assertEquals(BotIntent.Type.ATTACK, b.decide(w).type());
        w.entities.remove(target);
        w.time = 100;
        assertEquals(BotIntent.Type.HOLD, b.decide(w).type(), "searching");
        w.time = 201;
        b.decide(w);
        assertEquals(BotCommand.STAY, b.order().command(), "target lost: back to its post");
    }

    @Test
    void criticalDamageRetreatsUntilRepaired() {
        DoombotBrain b = brain();
        BotLocation home = at(-30, 0);
        b.setHome(OWNER_ID, home);
        World w = new World();
        w.mob(UUID.randomUUID(), at(3, 0), true, true);
        w.health = 0.2;
        BotIntent i = b.decide(w);
        assertEquals(BotIntent.Type.RETREAT_FOR_REPAIR, i.type());
        assertEquals(home, i.location());
        w.health = 0.6;
        assertEquals(BotIntent.Type.RETREAT_FOR_REPAIR, b.decide(w).type(), "stays retreating until repaired");
        w.health = 0.95;
        assertEquals(BotIntent.Type.ATTACK, b.decide(w).type());
    }

    @Test
    void returnHomeBecomesStayOnArrival() {
        DoombotBrain b = brain();
        BotLocation home = at(30, 0);
        b.setHome(OWNER_ID, home);
        assertEquals(CommandResult.ACCEPTED, b.issue(OWNER_ID, BotOrder.returnHome(), 0));
        World w = new World();
        assertEquals(BotIntent.Type.MOVE_TO, b.decide(w).type());
        w.self = at(29, 0);
        assertEquals(BotIntent.Type.HOLD, b.decide(w).type());
        assertEquals(BotCommand.STAY, b.order().command());
    }

    @Test
    void threatsAreForgotten() {
        DoombotBrain b = brain();
        World w = new World();
        w.mob(UUID.randomUUID(), at(3, 0), true, false);
        b.decide(w);
        assertEquals(1, b.threatCount());
        w.contacts.clear();
        w.time = 25;
        assertNotEquals(BotIntent.Type.ATTACK, b.decide(w).type(), "unseen for more than a second: not engaged");
        w.time = 601;
        b.decide(w);
        assertEquals(0, b.threatCount());
    }

    @Test
    void ownershipTransferMovesControl() {
        DoombotBrain b = brain();
        assertTrue(b.policy().transfer(OWNER_ID, STRANGER));
        assertEquals(STRANGER, b.owner());
        assertEquals(CommandResult.DENIED_NOT_AUTHORISED, b.issue(OWNER_ID, BotOrder.passive(), 0));
        assertEquals(CommandResult.ACCEPTED, b.issue(SecurityIdentity.player(STRANGER), BotOrder.passive(), 0));
    }

    /** Property test: random worlds never make a bot attack its owner or a trusted player, or path across dimensions. */
    @Test
    void randomWorldsNeverTurnBotsOnFriends() {
        for (int seed = 0; seed < 300; seed++) {
            Random r = new Random(seed);
            BotConfig cfg = new BotConfig(4, 28, 100, 12, 6, 48, 0.25, 200, 600, r.nextBoolean());
            DoombotBrain b = new DoombotBrain(BOT, OWNER, cfg);
            b.policy().grant(OWNER_ID, FRIEND, Set.of(Permission.VIEW));
            b.setHome(OWNER_ID, at(r.nextInt(50), r.nextInt(50)));
            World w = new World();
            for (int step = 0; step < 200; step++) {
                w.time += 1 + r.nextInt(30);
                w.self = at(r.nextInt(60) - 30, r.nextInt(60) - 30);
                w.owner = r.nextInt(8) == 0 ? null : r.nextInt(8) == 0 ? new BotLocation("minecraft:the_end", 0, 64, 0)
                        : at(r.nextInt(80) - 40, r.nextInt(80) - 40);
                w.health = r.nextDouble();
                w.contacts.clear();
                int n = r.nextInt(5);
                for (int k = 0; k < n; k++) {
                    UUID id = switch (r.nextInt(6)) {
                        case 0 -> OWNER;
                        case 1 -> FRIEND;
                        default -> new UUID(1, r.nextInt(20));
                    };
                    BotLocation where = at(w.self.x() + r.nextInt(30) - 15, w.self.z() + r.nextInt(30) - 15);
                    w.entities.put(id, where);
                    w.contacts.add(new BotWorldAdapter.Contact(id, where, r.nextBoolean(), r.nextBoolean(), r.nextBoolean(), r.nextBoolean()));
                }
                if (r.nextInt(10) == 0) {
                    BotOrder o = switch (r.nextInt(6)) {
                        case 0 -> BotOrder.follow();
                        case 1 -> BotOrder.stay(w.self);
                        case 2 -> BotOrder.attack(r.nextBoolean() ? OWNER : new UUID(1, r.nextInt(20)));
                        case 3 -> BotOrder.defend(w.self, 1 + r.nextInt(60));
                        case 4 -> BotOrder.returnHome();
                        default -> BotOrder.passive();
                    };
                    b.issue(r.nextBoolean() ? OWNER_ID : SecurityIdentity.player(STRANGER), o, w.time);
                }
                BotIntent i = b.decide(w);
                String where = "seed " + seed + " step " + step;
                assertNotNull(i, where);
                if (i.type() == BotIntent.Type.ATTACK) {
                    assertNotEquals(OWNER, i.target(), where);
                    assertNotEquals(FRIEND, i.target(), where);
                    assertNotEquals(BOT, i.target(), where);
                }
                if (i.location() != null) assertTrue(i.location().sameDimension(w.self), where + " " + i);
            }
        }
    }
}
