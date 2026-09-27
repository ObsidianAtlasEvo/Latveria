package com.doomsovereign.core.analysis;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Subject profiles, loaded from JSON. In the mod these come from a datapack path
 * ({@code data/<ns>/doom_analysis/*.json}) so servers and other mods can add creatures; the core
 * ships the defaults at {@code /doom_sovereign/analysis/vanilla.json}.
 */
public final class ProfileRegistry {
    private final Map<String, SubjectProfile> profiles = new LinkedHashMap<>();

    public SubjectProfile profile(String subjectId) {
        SubjectProfile p = profiles.get(subjectId);
        return p != null ? p : SubjectProfile.generic(subjectId);
    }

    public boolean known(String subjectId) {
        return profiles.containsKey(subjectId);
    }

    public int size() {
        return profiles.size();
    }

    public void register(SubjectProfile p) {
        profiles.put(p.subjectId(), p);
    }

    public static ProfileRegistry loadDefaults() {
        try (InputStream in = ProfileRegistry.class.getResourceAsStream("/doom_sovereign/analysis/vanilla.json")) {
            if (in == null) throw new IllegalStateException("default analysis profiles missing");
            ProfileRegistry r = new ProfileRegistry();
            r.load(new InputStreamReader(in, StandardCharsets.UTF_8));
            return r;
        } catch (IOException e) {
            throw new IllegalStateException(e);
        }
    }

    /** Parses a JSON array of profiles; malformed entries throw with the subject named. */
    public void load(Reader reader) {
        JsonArray arr = JsonParser.parseReader(reader).getAsJsonArray();
        for (JsonElement el : arr) register(parse(el.getAsJsonObject()));
    }

    static SubjectProfile parse(JsonObject o) {
        String id = o.get("subject").getAsString();
        try {
            List<Trait> traits = new ArrayList<>();
            for (JsonElement t : o.getAsJsonArray("traits")) {
                JsonObject to = t.getAsJsonObject();
                ObservationMethod via = to.has("via") ? ObservationMethod.valueOf(to.get("via").getAsString()) : null;
                double th = to.get("threshold").getAsDouble();
                if (th < 0 || th > KnowledgeEntry.MAX) throw new IllegalArgumentException("threshold out of range");
                traits.add(new Trait(to.get("id").getAsString(), TraitCategory.valueOf(to.get("category").getAsString()),
                        to.get("text").getAsString(), th, via));
            }
            List<Countermeasure> cms = new ArrayList<>();
            if (o.has("countermeasures")) {
                for (JsonElement c : o.getAsJsonArray("countermeasures")) {
                    JsonObject co = c.getAsJsonObject();
                    Set<String> needs = new HashSet<>();
                    if (co.has("traits")) for (JsonElement n : co.getAsJsonArray("traits")) needs.add(n.getAsString());
                    cms.add(new Countermeasure(co.get("id").getAsString(), co.get("title").getAsString(),
                            co.get("description").getAsString(), co.get("knowledge").getAsDouble(), needs));
                }
            }
            return new SubjectProfile(id, o.get("name").getAsString(), traits, cms);
        } catch (RuntimeException e) {
            throw new IllegalArgumentException("bad analysis profile " + id + ": " + e.getMessage(), e);
        }
    }
}
