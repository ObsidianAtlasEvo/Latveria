package com.doomsovereign.core.persist;

import com.google.gson.JsonObject;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Everything persisted per player (attached to the player in the mod). A plain data object: the
 * mapper converts between this and live domain objects.
 */
public final class PlayerDoomData {
    public UUID player;
    // armour
    public long energy;
    public long lastDrainTick;
    public double heat;
    public boolean heatLocked;
    public boolean everInitialised;
    public String frame = "royal_mk1";
    public List<String> modules = new ArrayList<>();
    public Map<String, long[]> cooldowns = new LinkedHashMap<>(); // id -> {charges, nextChargeAt}
    // sorcery
    public double focus = 100;
    // research
    public Map<String, Integer> researchCounters = new LinkedHashMap<>();
    public Set<String> researchCompleted = new LinkedHashSet<>();
    public String researchActive;
    public int researchActiveTicks;
    // analysis
    public Map<String, AnalysisRecord> analysis = new LinkedHashMap<>();
    // sovereignty and travel
    public boolean sovereign;
    public long sovereignSince;
    public String title = "";
    public List<Waypoint> waypoints = new ArrayList<>();
    /** Fields written by a newer version that this version does not understand; written back unchanged. */
    public JsonObject extra = new JsonObject();

    public static final class AnalysisRecord {
        public double knowledge;
        public Map<String, Integer> counts = new LinkedHashMap<>();
        public Set<String> revealed = new LinkedHashSet<>();
        public Set<String> countermeasures = new LinkedHashSet<>();
    }

    public record Waypoint(String name, String dimension, double x, double y, double z) {
    }
}
