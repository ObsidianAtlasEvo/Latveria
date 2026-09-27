package com.doomsovereign.core.persist;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import java.util.Set;

/**
 * JSON form of {@link PlayerDoomData}. Schema history:
 * <ul>
 *   <li>v1 (prototype): {@code energyFraction} 0..1, {@code research} as a flat list,
 *       {@code knownMobs} as subject -> knowledge.</li>
 *   <li>v2 (current): absolute energy in DE, research counters/active project, full analysis
 *       records, armour configuration, sovereignty, waypoints.</li>
 * </ul>
 * In the mod the JSON is stored as a string or converted to NBT by the attachment codec; the schema
 * and migrations are the same either way.
 */
public final class PlayerDataCodec {
    public static final int CURRENT = 2;
    static final long V1_CAPACITY = 20_000;
    private static final Set<String> KNOWN = Set.of("schema", "player", "armor", "focus", "research", "analysis",
            "sovereignty", "waypoints");

    private static final Migrator MIGRATOR = new Migrator("schema", CURRENT).add(new Migration() {
        @Override
        public int from() {
            return 1;
        }

        @Override
        public void apply(JsonObject d, Warnings w) {
            JsonObject armor = new JsonObject();
            double frac = J.getDouble(d, "energyFraction", 1.0, w, "v1");
            frac = Math.max(0, Math.min(1, frac));
            armor.addProperty("energy", Math.round(frac * V1_CAPACITY));
            d.remove("energyFraction");
            d.add("armor", armor);
            JsonObject research = new JsonObject();
            research.add("completed", J.toArray(J.strings(d, "research", w, "v1")));
            d.remove("research");
            d.add("research", research);
            JsonObject analysis = new JsonObject();
            JsonObject known = J.obj(d, "knownMobs", w, "v1");
            for (var e : known.entrySet()) {
                JsonObject rec = new JsonObject();
                rec.addProperty("knowledge", J.getDouble(known, e.getKey(), 0, w, "v1.knownMobs"));
                analysis.add(e.getKey(), rec);
            }
            d.remove("knownMobs");
            d.add("analysis", analysis);
        }
    });

    private PlayerDataCodec() {
    }

    public static JsonObject encode(PlayerDoomData p) {
        JsonObject d = new JsonObject();
        for (var e : p.extra.entrySet()) d.add(e.getKey(), e.getValue().deepCopy());
        d.addProperty("schema", CURRENT);
        if (p.player != null) d.addProperty("player", p.player.toString());
        JsonObject a = new JsonObject();
        a.addProperty("energy", p.energy);
        a.addProperty("lastDrain", p.lastDrainTick);
        a.addProperty("heat", p.heat);
        a.addProperty("heatLocked", p.heatLocked);
        a.addProperty("initialised", p.everInitialised);
        a.addProperty("frame", p.frame);
        a.add("modules", J.toArray(p.modules));
        JsonObject cds = new JsonObject();
        p.cooldowns.forEach((k, v) -> {
            JsonObject c = new JsonObject();
            c.addProperty("charges", v[0]);
            c.addProperty("next", v[1]);
            cds.add(k, c);
        });
        a.add("cooldowns", cds);
        d.add("armor", a);
        d.addProperty("focus", p.focus);
        JsonObject r = new JsonObject();
        JsonObject counters = new JsonObject();
        p.researchCounters.forEach(counters::addProperty);
        r.add("counters", counters);
        r.add("completed", J.toArray(p.researchCompleted));
        if (p.researchActive != null) {
            r.addProperty("active", p.researchActive);
            r.addProperty("activeTicks", p.researchActiveTicks);
        }
        d.add("research", r);
        JsonObject an = new JsonObject();
        p.analysis.forEach((subject, rec) -> {
            JsonObject o = new JsonObject();
            o.addProperty("knowledge", rec.knowledge);
            JsonObject counts = new JsonObject();
            rec.counts.forEach(counts::addProperty);
            o.add("counts", counts);
            o.add("revealed", J.toArray(rec.revealed));
            o.add("countermeasures", J.toArray(rec.countermeasures));
            an.add(subject, o);
        });
        d.add("analysis", an);
        JsonObject s = new JsonObject();
        s.addProperty("sovereign", p.sovereign);
        s.addProperty("since", p.sovereignSince);
        s.addProperty("title", p.title);
        d.add("sovereignty", s);
        JsonArray wps = new JsonArray();
        for (PlayerDoomData.Waypoint wp : p.waypoints) {
            JsonObject o = new JsonObject();
            o.addProperty("name", wp.name());
            o.addProperty("dimension", wp.dimension());
            o.addProperty("x", wp.x());
            o.addProperty("y", wp.y());
            o.addProperty("z", wp.z());
            wps.add(o);
        }
        d.add("waypoints", wps);
        return d;
    }

    /** Decodes any supported version. Never throws on bad values; see {@code warnings}. */
    public static PlayerDoomData decode(JsonObject raw, Warnings w) {
        JsonObject d = MIGRATOR.migrate(raw.deepCopy(), w);
        PlayerDoomData p = new PlayerDoomData();
        for (var e : d.entrySet()) if (!KNOWN.contains(e.getKey())) p.extra.add(e.getKey(), e.getValue().deepCopy());
        p.player = J.getUuid(d, "player", w, "$");
        JsonObject a = J.obj(d, "armor", w, "$");
        p.energy = Math.max(0, J.getLong(a, "energy", 0, w, "armor"));
        p.lastDrainTick = J.getLong(a, "lastDrain", 0, w, "armor");
        double heat = J.getDouble(a, "heat", 0, w, "armor");
        if (heat < 0) { w.add("armor.heat negative; reset to 0"); heat = 0; }
        p.heat = heat;
        p.heatLocked = J.getBool(a, "heatLocked", false, w, "armor");
        p.everInitialised = J.getBool(a, "initialised", false, w, "armor");
        p.frame = J.getString(a, "frame", "royal_mk1", w, "armor");
        p.modules = J.strings(a, "modules", w, "armor");
        JsonObject cds = J.obj(a, "cooldowns", w, "armor");
        for (var e : cds.entrySet()) {
            if (!e.getValue().isJsonObject()) { w.add("armor.cooldowns." + e.getKey() + ": not an object"); continue; }
            JsonObject c = e.getValue().getAsJsonObject();
            p.cooldowns.put(e.getKey(), new long[]{Math.max(0, J.getLong(c, "charges", 1, w, "cooldown")), J.getLong(c, "next", 0, w, "cooldown")});
        }
        double focus = J.getDouble(d, "focus", 100, w, "$");
        p.focus = focus < 0 ? 0 : focus;
        JsonObject r = J.obj(d, "research", w, "$");
        p.researchCounters.putAll(J.intMap(r, "counters", w, "research"));
        p.researchCompleted.addAll(J.strings(r, "completed", w, "research"));
        p.researchActive = J.getString(r, "active", null, w, "research");
        p.researchActiveTicks = Math.max(0, J.getInt(r, "activeTicks", 0, w, "research"));
        JsonObject an = J.obj(d, "analysis", w, "$");
        for (var e : an.entrySet()) {
            JsonElement v = e.getValue();
            if (!v.isJsonObject()) { w.add("analysis." + e.getKey() + ": not an object; dropped"); continue; }
            JsonObject o = v.getAsJsonObject();
            PlayerDoomData.AnalysisRecord rec = new PlayerDoomData.AnalysisRecord();
            rec.knowledge = Math.max(0, Math.min(100, J.getDouble(o, "knowledge", 0, w, "analysis." + e.getKey())));
            rec.counts.putAll(J.intMap(o, "counts", w, "analysis." + e.getKey()));
            rec.revealed.addAll(J.strings(o, "revealed", w, "analysis." + e.getKey()));
            rec.countermeasures.addAll(J.strings(o, "countermeasures", w, "analysis." + e.getKey()));
            p.analysis.put(e.getKey(), rec);
        }
        JsonObject s = J.obj(d, "sovereignty", w, "$");
        p.sovereign = J.getBool(s, "sovereign", false, w, "sovereignty");
        p.sovereignSince = J.getLong(s, "since", 0, w, "sovereignty");
        p.title = J.getString(s, "title", "", w, "sovereignty");
        for (JsonElement e : J.arr(d, "waypoints", w, "$")) {
            if (!e.isJsonObject()) { w.add("waypoints: dropped non-object"); continue; }
            JsonObject o = e.getAsJsonObject();
            String dim = J.getString(o, "dimension", null, w, "waypoint");
            double x = J.getDouble(o, "x", Double.NaN, w, "waypoint"), y = J.getDouble(o, "y", Double.NaN, w, "waypoint"),
                    z = J.getDouble(o, "z", Double.NaN, w, "waypoint");
            if (dim == null || Double.isNaN(x) || Double.isNaN(y) || Double.isNaN(z)) { w.add("waypoints: incomplete entry dropped"); continue; }
            p.waypoints.add(new PlayerDoomData.Waypoint(J.getString(o, "name", "Waypoint", w, "waypoint"), dim, x, y, z));
        }
        return p;
    }
}
