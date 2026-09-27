package com.doomsovereign.core.persist;

import com.google.gson.JsonObject;

/** Upgrades a document from {@code from()} to {@code from() + 1} in place. */
public interface Migration {
    int from();

    void apply(JsonObject doc, Warnings w);
}
