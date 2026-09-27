package com.doomsovereign.core.persist;

import com.doomsovereign.core.bot.BotCommand;
import com.doomsovereign.core.bot.BotLocation;
import com.doomsovereign.core.bot.BotOrder;
import com.doomsovereign.core.security.AccessPolicy;
import com.doomsovereign.core.security.DeviceKind;
import com.doomsovereign.core.security.Permission;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;

/** JSON form of {@link WorldDoomData}; schema v1. */
public final class WorldDataCodec {
    public static final int CURRENT = 1;
    private static final Set<String> KNOWN = Set.of("schema", "bots", "devices", "latveria", "realm", "sovereign");
    private static final Migrator MIGRATOR = new Migrator("schema", CURRENT);

    private WorldDataCodec() {
    }

    // ---- locations -----------------------------------------------------------------------------------
    static JsonObject loc(BotLocation l) {
        JsonObject o = new JsonObject();
        o.addProperty("dimension", l.dimension());
        o.addProperty("x", l.x());
        o.addProperty("y", l.y());
        o.addProperty("z", l.z());
        return o;
    }

    static BotLocation loc(JsonObject parent, String key, Warnings w, String path) {
        if (!parent.has(key) || parent.get(key).isJsonNull()) return null;
        JsonObject o = J.obj(parent, key, w, path);
        String dim = J.getString(o, "dimension", null, w, path + "." + key);
        double x = J.getDouble(o, "x", Double.NaN, w, path), y = J.getDouble(o, "y", Double.NaN, w, path), z = J.getDouble(o, "z", Double.NaN, w, path);
        if (dim == null || dim.isBlank() || Double.isNaN(x) || Double.isNaN(y) || Double.isNaN(z)) {
            w.add(path + "." + key + ": incomplete location dropped");
            return null;
        }
        return new BotLocation(dim, x, y, z);
    }

    static EnumSet<Permission> perms(JsonArray a, Warnings w, String path) {
        EnumSet<Permission> s = EnumSet.noneOf(Permission.class);
        for (JsonElement e : a) {
            try {
                s.add(Permission.valueOf(e.getAsString()));
            } catch (RuntimeException ex) {
                w.add(path + ": unknown permission " + e + " dropped");
            }
        }
        return s;
    }

    static JsonArray perms(Set<Permission> s) {
        JsonArray a = new JsonArray();
        for (Permission p : s) a.add(p.name());
        return a;
    }

    // ---- policy ------------------------------------------------------------------------------------------
    public static JsonObject policy(AccessPolicy p) {
        JsonObject o = new JsonObject();
        o.addProperty("owner", p.owner().toString());
        o.addProperty("kind", p.kind().name());
        p.ownerTeam().ifPresent(t -> o.addProperty("team", t));
        o.add("teamPerms", perms(p.teamPermissions()));
        o.add("publicPerms", perms(p.publicPermissions()));
        JsonObject tr = new JsonObject();
        p.trusted().forEach((k, v) -> tr.add(k.toString(), perms(v)));
        o.add("trusted", tr);
        o.addProperty("adminOverride", p.adminOverride());
        return o;
    }

    public static AccessPolicy policy(JsonObject o, Warnings w, String path) {
        UUID owner = J.getUuid(o, "owner", w, path);
        if (owner == null) {
            w.add(path + ": policy without a valid owner dropped");
            return null;
        }
        DeviceKind kind;
        try {
            kind = DeviceKind.valueOf(J.getString(o, "kind", "MACHINE", w, path));
        } catch (IllegalArgumentException ex) {
            w.add(path + ": unknown device kind, using MACHINE");
            kind = DeviceKind.MACHINE;
        }
        AccessPolicy p = new AccessPolicy(owner, kind);
        Map<UUID, EnumSet<Permission>> trusted = new LinkedHashMap<>();
        JsonObject tr = J.obj(o, "trusted", w, path);
        for (var e : tr.entrySet()) {
            try {
                UUID id = UUID.fromString(e.getKey());
                if (e.getValue().isJsonArray()) trusted.put(id, perms(e.getValue().getAsJsonArray(), w, path + ".trusted"));
            } catch (IllegalArgumentException ex) {
                w.add(path + ".trusted: invalid UUID " + e.getKey() + " dropped");
            }
        }
        p.restore(Optional.ofNullable(J.getString(o, "team", null, w, path)),
                o.has("teamPerms") ? perms(J.arr(o, "teamPerms", w, path), w, path) : kind.teamDefault(),
                o.has("publicPerms") ? perms(J.arr(o, "publicPerms", w, path), w, path) : kind.publicDefault(),
                trusted, J.getBool(o, "adminOverride", false, w, path));
        return p;
    }

    // ---- orders ------------------------------------------------------------------------------------------
    static JsonObject order(BotOrder o) {
        JsonObject j = new JsonObject();
        j.addProperty("command", o.command().name());
        if (o.target() != null) j.addProperty("target", o.target().toString());
        if (o.anchor() != null) j.add("anchor", loc(o.anchor()));
        if (o.radius() > 0) j.addProperty("radius", o.radius());
        if (!o.patrol().isEmpty()) {
            JsonArray a = new JsonArray();
            o.patrol().forEach(p -> a.add(loc(p)));
            j.add("patrol", a);
        }
        return j;
    }

    static BotOrder order(JsonObject j, Warnings w, String path) {
        BotCommand c;
        try {
            c = BotCommand.valueOf(J.getString(j, "command", "FOLLOW", w, path));
        } catch (IllegalArgumentException ex) {
            w.add(path + ": unknown command, using FOLLOW");
            return BotOrder.follow();
        }
        List<BotLocation> pts = new ArrayList<>();
        for (JsonElement e : J.arr(j, "patrol", w, path)) {
            JsonObject wrap = new JsonObject();
            wrap.add("p", e);
            BotLocation l = loc(wrap, "p", w, path + ".patrol");
            if (l != null) pts.add(l);
        }
        BotOrder o = new BotOrder(c, J.getUuid(j, "target", w, path), loc(j, "anchor", w, path), J.getDouble(j, "radius", 0, w, path), pts);
        // an order that lost its parameters falls back to something safe
        boolean ok = switch (c) {
            case ATTACK_TARGET, GUARD_ENTITY -> o.target() != null;
            case PATROL -> o.patrol().size() >= 2;
            case DEFEND_AREA -> o.anchor() != null && o.radius() > 0;
            case STAY -> o.anchor() != null;
            default -> true;
        };
        if (!ok) {
            w.add(path + ": " + c + " missing parameters; bot set to FOLLOW");
            return BotOrder.follow();
        }
        return o;
    }

    // ---- document ----------------------------------------------------------------------------------------
    public static JsonObject encode(WorldDoomData d) {
        JsonObject o = new JsonObject();
        for (var e : d.extra.entrySet()) o.add(e.getKey(), e.getValue().deepCopy());
        o.addProperty("schema", CURRENT);
        JsonArray bots = new JsonArray();
        for (WorldDoomData.BotRecord b : d.bots) {
            JsonObject j = new JsonObject();
            j.addProperty("id", b.id().toString());
            j.addProperty("owner", b.owner().toString());
            j.addProperty("type", b.type());
            j.add("order", order(b.order()));
            if (b.home() != null) j.add("home", loc(b.home()));
            if (b.lastKnown() != null) j.add("lastKnown", loc(b.lastKnown()));
            j.addProperty("patrolIndex", b.patrolIndex());
            j.addProperty("health", b.health());
            bots.add(j);
        }
        o.add("bots", bots);
        JsonArray devs = new JsonArray();
        for (WorldDoomData.DeviceRecord r : d.devices) {
            JsonObject j = new JsonObject();
            j.addProperty("id", r.id());
            j.add("policy", policy(r.policy()));
            devs.add(j);
        }
        o.add("devices", devs);
        if (d.latveriaCenter != null) o.add("latveria", loc(d.latveriaCenter));
        o.addProperty("realm", d.realmName);
        if (d.sovereign != null) o.addProperty("sovereign", d.sovereign.toString());
        return o;
    }

    public static WorldDoomData decode(JsonObject raw, Warnings w) {
        JsonObject o = MIGRATOR.migrate(raw.deepCopy(), w);
        WorldDoomData d = new WorldDoomData();
        for (var e : o.entrySet()) if (!KNOWN.contains(e.getKey())) d.extra.add(e.getKey(), e.getValue().deepCopy());
        java.util.Set<UUID> seen = new java.util.HashSet<>();
        int i = 0;
        for (JsonElement e : J.arr(o, "bots", w, "$")) {
            String path = "bots[" + (i++) + "]";
            if (!e.isJsonObject()) { w.add(path + ": not an object"); continue; }
            JsonObject j = e.getAsJsonObject();
            UUID id = J.getUuid(j, "id", w, path), owner = J.getUuid(j, "owner", w, path);
            if (id == null || owner == null) { w.add(path + ": missing id/owner; dropped"); continue; }
            if (!seen.add(id)) { w.add(path + ": duplicate bot id " + id + "; dropped"); continue; }
            BotOrder order = j.has("order") ? order(J.obj(j, "order", w, path), w, path + ".order") : BotOrder.follow();
            double hp = Math.max(0, Math.min(1, J.getDouble(j, "health", 1, w, path)));
            d.bots.add(new WorldDoomData.BotRecord(id, owner, J.getString(j, "type", "standard", w, path), order,
                    loc(j, "home", w, path), loc(j, "lastKnown", w, path), Math.max(0, J.getInt(j, "patrolIndex", 0, w, path)), hp));
        }
        i = 0;
        for (JsonElement e : J.arr(o, "devices", w, "$")) {
            String path = "devices[" + (i++) + "]";
            if (!e.isJsonObject()) continue;
            JsonObject j = e.getAsJsonObject();
            String id = J.getString(j, "id", null, w, path);
            AccessPolicy p = policy(J.obj(j, "policy", w, path), w, path + ".policy");
            if (id != null && p != null) d.devices.add(new WorldDoomData.DeviceRecord(id, p));
        }
        d.latveriaCenter = loc(o, "latveria", w, "$");
        d.realmName = J.getString(o, "realm", "Latveria", w, "$");
        d.sovereign = J.getUuid(o, "sovereign", w, "$");
        return d;
    }
}
