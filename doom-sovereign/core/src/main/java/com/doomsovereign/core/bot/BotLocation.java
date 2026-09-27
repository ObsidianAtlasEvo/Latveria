package com.doomsovereign.core.bot;

/** A position in a named dimension. Distances across dimensions are infinite. */
public record BotLocation(String dimension, double x, double y, double z) {
    public BotLocation {
        if (dimension == null || dimension.isBlank()) throw new IllegalArgumentException("dimension");
        if (!Double.isFinite(x) || !Double.isFinite(y) || !Double.isFinite(z)) throw new IllegalArgumentException("coordinates");
    }

    public double distance(BotLocation o) {
        if (!dimension.equals(o.dimension)) return Double.POSITIVE_INFINITY;
        return Math.sqrt((x - o.x) * (x - o.x) + (y - o.y) * (y - o.y) + (z - o.z) * (z - o.z));
    }

    public boolean sameDimension(BotLocation o) {
        return dimension.equals(o.dimension);
    }
}
