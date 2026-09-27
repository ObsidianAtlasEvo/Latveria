package com.doomsovereign.core.bot;

import com.doomsovereign.core.api.BotWorldAdapter;
import com.doomsovereign.core.api.BotWorldAdapter.Contact;
import com.doomsovereign.core.api.SecurityIdentity;
import com.doomsovereign.core.security.AccessPolicy;
import com.doomsovereign.core.security.DeviceKind;
import com.doomsovereign.core.security.Permission;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

/**
 * Server-side command and decision logic for one Doombot (directive section 22). Pure: it reads a
 * {@link BotWorldAdapter} snapshot and returns an intent, so it can be run every few ticks without
 * scanning the world and tested deterministically.
 *
 * <p>Decision priority: passive mode never fights; critical damage retreats for repair; anything
 * attacking the bot or its owner is engaged (players only when PvP is enabled and they are not
 * trusted); then the standing order.
 */
public final class DoombotBrain {
    private final UUID botId;
    private final AccessPolicy policy;
    private final BotConfig cfg;
    private BotOrder order = BotOrder.follow();
    private BotOrder previousOrder = BotOrder.follow();
    private BotLocation home;
    private int patrolIndex;
    private long lastTeleport = Long.MIN_VALUE / 2;
    private long attackTargetLastSeen;
    private boolean awaitingOwner;
    private boolean repairing;
    private final Map<UUID, Threat> threats = new HashMap<>();

    record Threat(UUID id, double score, long lastSeen, BotLocation where, boolean player) {
    }

    public DoombotBrain(UUID botId, UUID owner, BotConfig cfg) {
        this.botId = botId;
        this.policy = new AccessPolicy(owner, DeviceKind.DOOMBOT);
        this.cfg = cfg;
    }

    // ---- commands ---------------------------------------------------------------------------------
    public CommandResult issue(SecurityIdentity issuer, BotOrder o, long now) {
        if (!policy.can(issuer, Permission.COMMAND)) return CommandResult.DENIED_NOT_AUTHORISED;
        switch (o.command()) {
            case ATTACK_TARGET, GUARD_ENTITY -> {
                if (o.target() == null || o.target().equals(botId)) return CommandResult.INVALID_ORDER;
                if (o.command() == BotCommand.ATTACK_TARGET && isFriendly(o.target())) return CommandResult.REFUSED_FRIENDLY_TARGET;
            }
            case PATROL -> {
                if (o.patrol().size() < 2) return CommandResult.INVALID_ORDER;
            }
            case DEFEND_AREA -> {
                if (o.anchor() == null || !(o.radius() > 0) || o.radius() > cfg.maxDefendRadius()) return CommandResult.INVALID_ORDER;
            }
            case STAY -> {
                if (o.anchor() == null) return CommandResult.INVALID_ORDER;
            }
            case RETURN_HOME -> {
                if (home == null) return CommandResult.INVALID_ORDER;
            }
            default -> {
            }
        }
        if (order.command() != BotCommand.ATTACK_TARGET) previousOrder = order;
        order = o;
        patrolIndex = 0;
        attackTargetLastSeen = now;
        repairing = false;
        return CommandResult.ACCEPTED;
    }

    private boolean isFriendly(UUID id) {
        return id.equals(policy.owner()) || policy.trusted().containsKey(id);
    }

    public boolean setHome(SecurityIdentity issuer, BotLocation loc) {
        if (!policy.can(issuer, Permission.CONFIGURE)) return false;
        home = loc;
        return true;
    }

    // ---- decisions ----------------------------------------------------------------------------------
    public BotIntent decide(BotWorldAdapter w) {
        long now = w.gameTime();
        BotLocation self = w.selfLocation();
        rememberThreats(w, now);
        Optional<BotLocation> owner = w.ownerLocation();
        awaitingOwner = order.command() == BotCommand.FOLLOW && owner.isEmpty();

        if (order.command() == BotCommand.PASSIVE) return owner.map(o -> followOwner(self, o, now)).orElse(BotIntent.hold(self, "passive, owner away"));

        if (w.selfHealth() < cfg.criticalHealth()) {
            repairing = true;
            if (home != null) return new BotIntent(BotIntent.Type.RETREAT_FOR_REPAIR, home, null, "critical damage");
            return BotIntent.hold(self, "critical damage, no home");
        }
        if (repairing && w.selfHealth() >= 0.9) repairing = false;
        if (repairing && home != null) return new BotIntent(BotIntent.Type.RETREAT_FOR_REPAIR, home, null, "repairing");

        // explicit attack order takes precedence over opportunistic threats
        if (order.command() == BotCommand.ATTACK_TARGET) {
            Optional<BotLocation> t = w.locate(order.target());
            if (t.isPresent()) {
                attackTargetLastSeen = now;
                return BotIntent.attack(order.target(), t.get(), "ordered attack");
            }
            if (now - attackTargetLastSeen > cfg.targetLostTicks()) {
                order = previousOrder;
            } else {
                return BotIntent.hold(self, "searching for target");
            }
        }

        BotLocation leashCentre = switch (order.command()) {
            case STAY, DEFEND_AREA -> order.anchor();
            case GUARD_ENTITY -> w.locate(order.target()).orElse(self);
            case FOLLOW -> owner.orElse(self);
            case PATROL -> self;
            case RETURN_HOME -> self;
            default -> self;
        };
        double leash = switch (order.command()) {
            case STAY -> cfg.stayEngageRange();
            case DEFEND_AREA -> order.radius();
            case RETURN_HOME -> 4;
            default -> cfg.engageRange();
        };
        Optional<Threat> best = bestThreat(leashCentre, leash, now);
        if (best.isPresent()) return BotIntent.attack(best.get().id(), best.get().where(), "engaging threat");

        return switch (order.command()) {
            case FOLLOW -> owner.map(o -> followOwner(self, o, now)).orElse(BotIntent.hold(self, "awaiting owner"));
            case STAY -> self.distance(order.anchor()) > 1.5 ? BotIntent.move(order.anchor(), "returning to post") : BotIntent.hold(order.anchor(), "holding post");
            case DEFEND_AREA -> self.distance(order.anchor()) > order.radius() ? BotIntent.move(order.anchor(), "returning to area") : BotIntent.idle("guarding area");
            case GUARD_ENTITY -> w.locate(order.target()).map(g -> self.distance(g) > cfg.followDistance()
                    ? BotIntent.move(g, "escorting") : BotIntent.idle("escorting")).orElse(BotIntent.hold(self, "ward not found"));
            case PATROL -> {
                BotLocation wp = order.patrol().get(patrolIndex);
                if (self.distance(wp) <= 1.5) {
                    patrolIndex = (patrolIndex + 1) % order.patrol().size();
                    wp = order.patrol().get(patrolIndex);
                }
                yield BotIntent.move(wp, "patrolling");
            }
            case RETURN_HOME -> {
                if (self.distance(home) <= 2) {
                    order = BotOrder.stay(home);
                    yield BotIntent.hold(home, "home");
                }
                yield BotIntent.move(home, "returning home");
            }
            default -> BotIntent.idle("idle");
        };
    }

    private BotIntent followOwner(BotLocation self, BotLocation owner, long now) {
        // never path toward a position in another dimension; the owner has to come back (or take the bot through)
        if (!self.sameDimension(owner)) return BotIntent.hold(self, "owner in another dimension");
        double d = self.distance(owner);
        if (d > cfg.teleportDistance() && now - lastTeleport >= cfg.teleportCooldown()) {
            lastTeleport = now;
            return new BotIntent(BotIntent.Type.TELEPORT_TO_OWNER, owner, null, "catching up");
        }
        if (d > cfg.followDistance()) return BotIntent.move(owner, "following");
        return BotIntent.idle("at owner's side");
    }

    private void rememberThreats(BotWorldAdapter w, long now) {
        for (Contact c : w.contacts()) {
            if (isFriendly(c.id())) continue;
            if (c.player() && !(cfg.pvp() && (c.attackingOwner() || c.attackingSelf()))) continue;
            double score = (c.attackingOwner() ? 50 : 0) + (c.attackingSelf() ? 30 : 0) + (c.hostile() ? 10 : 0);
            if (score <= 0) continue;
            Threat old = threats.get(c.id());
            double s = old == null ? score : Math.max(score, old.score() * 0.9);
            threats.put(c.id(), new Threat(c.id(), s, now, c.location(), c.player()));
        }
        threats.values().removeIf(t -> now - t.lastSeen() > cfg.memoryTicks());
    }

    private Optional<Threat> bestThreat(BotLocation centre, double radius, long now) {
        return threats.values().stream()
                .filter(t -> now - t.lastSeen() <= 20)
                .filter(t -> t.where().distance(centre) <= radius || t.score() >= 30)
                .filter(t -> t.where().distance(centre) <= Math.max(radius, cfg.engageRange()) * 1.5)
                .max(Comparator.comparingDouble(Threat::score).thenComparing(t -> -t.where().distance(centre)));
    }

    // ---- state ----------------------------------------------------------------------------------------
    public UUID botId() { return botId; }

    public UUID owner() { return policy.owner(); }

    public AccessPolicy policy() { return policy; }

    public BotOrder order() { return order; }

    public BotLocation home() { return home; }

    public boolean awaitingOwner() { return awaitingOwner; }

    public boolean repairing() { return repairing; }

    public int threatCount() { return threats.size(); }

    public int patrolIndex() { return patrolIndex; }

    /** Persistence only. */
    public void restore(BotOrder savedOrder, BotLocation savedHome, int savedPatrolIndex) {
        order = savedOrder == null ? BotOrder.follow() : savedOrder;
        home = savedHome;
        patrolIndex = order.patrol().isEmpty() ? 0 : Math.floorMod(savedPatrolIndex, order.patrol().size());
    }
}
