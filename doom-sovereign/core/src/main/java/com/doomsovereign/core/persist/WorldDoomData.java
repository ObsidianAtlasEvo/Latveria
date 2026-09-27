package com.doomsovereign.core.persist;

import com.doomsovereign.core.bot.BotLocation;
import com.doomsovereign.core.bot.BotOrder;
import com.doomsovereign.core.security.AccessPolicy;
import com.google.gson.JsonObject;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/** Everything persisted per world (SavedData in the mod): robots, secured devices, the realm. */
public final class WorldDoomData {
    public List<BotRecord> bots = new ArrayList<>();
    public List<DeviceRecord> devices = new ArrayList<>();
    /** Registered Latveria centre (/doom latveria setcenter). Optional. */
    public BotLocation latveriaCenter;
    public String realmName = "Latveria";
    /** Sovereign player in strict single-sovereign mode. Optional. */
    public UUID sovereign;
    public JsonObject extra = new JsonObject();

    /** A Doombot's durable state; the entity itself is saved by Minecraft, this is the owner-side registry. */
    public record BotRecord(UUID id, UUID owner, String type, BotOrder order, BotLocation home, BotLocation lastKnown,
                            int patrolIndex, double health) {
    }

    /** A secured device, keyed by a stable id (dimension + position for blocks). */
    public record DeviceRecord(String id, AccessPolicy policy) {
    }
}
