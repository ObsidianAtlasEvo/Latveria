package com.doomsovereign.core.persist;

import com.google.gson.JsonObject;
import java.util.Map;
import java.util.TreeMap;

/** Runs the migration chain for one document type. */
public final class Migrator {
    private final String versionKey;
    private final int current;
    private final Map<Integer, Migration> steps = new TreeMap<>();

    public Migrator(String versionKey, int current) {
        this.versionKey = versionKey;
        this.current = current;
    }

    public Migrator add(Migration m) {
        steps.put(m.from(), m);
        return this;
    }

    public int current() {
        return current;
    }

    /**
     * Brings {@code doc} to the current version. Documents from a newer mod version are loaded as-is
     * (best effort) with a warning, so downgrading never wipes data.
     */
    public JsonObject migrate(JsonObject doc, Warnings w) {
        int v = J.getInt(doc, versionKey, 1, w, "$");
        if (v < 1) {
            w.add("invalid schema version " + v + ", treating as 1");
            v = 1;
        }
        if (v > current) {
            w.add("document is from a newer version (" + v + " > " + current + "); loading best-effort");
            return doc;
        }
        while (v < current) {
            Migration m = steps.get(v);
            if (m == null) throw new IllegalStateException("no migration from " + v);
            m.apply(doc, w);
            v++;
            doc.addProperty(versionKey, v);
        }
        return doc;
    }
}
