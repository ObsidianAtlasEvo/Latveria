package com.doomsovereign.core.persist;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonPrimitive;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Tolerant JSON readers: wrong types and missing values fall back to defaults with a warning. */
final class J {
    private J() {
    }

    static long getLong(JsonObject o, String k, long def, Warnings w, String path) {
        JsonElement e = o.get(k);
        if (e == null || e.isJsonNull()) return def;
        try {
            if (e.isJsonPrimitive() && e.getAsJsonPrimitive().isNumber()) {
                double d = e.getAsDouble();
                if (!Double.isFinite(d)) throw new NumberFormatException();
                return e.getAsLong();
            }
            if (e.isJsonPrimitive() && e.getAsJsonPrimitive().isString()) return Long.parseLong(e.getAsString().trim());
        } catch (RuntimeException ex) {
            // fall through
        }
        w.add(path + "." + k + ": expected integer, got " + e + "; using " + def);
        return def;
    }

    static int getInt(JsonObject o, String k, int def, Warnings w, String path) {
        long v = getLong(o, k, def, w, path);
        if (v > Integer.MAX_VALUE || v < Integer.MIN_VALUE) {
            w.add(path + "." + k + ": out of range; using " + def);
            return def;
        }
        return (int) v;
    }

    static double getDouble(JsonObject o, String k, double def, Warnings w, String path) {
        JsonElement e = o.get(k);
        if (e == null || e.isJsonNull()) return def;
        try {
            double d = e.isJsonPrimitive() && e.getAsJsonPrimitive().isString() ? Double.parseDouble(e.getAsString()) : e.getAsDouble();
            if (Double.isFinite(d)) return d;
        } catch (RuntimeException ex) {
            // fall through
        }
        w.add(path + "." + k + ": expected number, got " + e + "; using " + def);
        return def;
    }

    static boolean getBool(JsonObject o, String k, boolean def, Warnings w, String path) {
        JsonElement e = o.get(k);
        if (e == null || e.isJsonNull()) return def;
        if (e.isJsonPrimitive() && e.getAsJsonPrimitive().isBoolean()) return e.getAsBoolean();
        w.add(path + "." + k + ": expected boolean; using " + def);
        return def;
    }

    static String getString(JsonObject o, String k, String def, Warnings w, String path) {
        JsonElement e = o.get(k);
        if (e == null || e.isJsonNull()) return def;
        if (e.isJsonPrimitive()) return e.getAsString();
        w.add(path + "." + k + ": expected string; using " + def);
        return def;
    }

    static UUID getUuid(JsonObject o, String k, Warnings w, String path) {
        String s = getString(o, k, null, w, path);
        if (s == null) return null;
        try {
            return UUID.fromString(s);
        } catch (IllegalArgumentException ex) {
            w.add(path + "." + k + ": invalid UUID " + s);
            return null;
        }
    }

    static JsonObject obj(JsonObject o, String k, Warnings w, String path) {
        JsonElement e = o.get(k);
        if (e == null || e.isJsonNull()) return new JsonObject();
        if (e.isJsonObject()) return e.getAsJsonObject();
        w.add(path + "." + k + ": expected object; ignoring");
        return new JsonObject();
    }

    static JsonArray arr(JsonObject o, String k, Warnings w, String path) {
        JsonElement e = o.get(k);
        if (e == null || e.isJsonNull()) return new JsonArray();
        if (e.isJsonArray()) return e.getAsJsonArray();
        w.add(path + "." + k + ": expected array; ignoring");
        return new JsonArray();
    }

    static List<String> strings(JsonObject o, String k, Warnings w, String path) {
        List<String> out = new ArrayList<>();
        for (JsonElement e : arr(o, k, w, path)) {
            if (e.isJsonPrimitive() && e.getAsJsonPrimitive().isString()) out.add(e.getAsString());
            else w.add(path + "." + k + ": dropped non-string entry " + e);
        }
        return out;
    }

    static Map<String, Integer> intMap(JsonObject o, String k, Warnings w, String path) {
        Map<String, Integer> out = new LinkedHashMap<>();
        JsonObject m = obj(o, k, w, path);
        for (var e : m.entrySet()) {
            int v = getInt(m, e.getKey(), -1, w, path + "." + k);
            if (v >= 0) out.put(e.getKey(), v);
            else w.add(path + "." + k + "." + e.getKey() + ": negative/invalid count dropped");
        }
        return out;
    }

    static JsonArray toArray(Iterable<String> it) {
        JsonArray a = new JsonArray();
        for (String s : it) a.add(new JsonPrimitive(s));
        return a;
    }
}
