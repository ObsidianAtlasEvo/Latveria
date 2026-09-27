package com.doomsovereign.core.persist;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** Problems met while loading. Loading never throws for bad values: it repairs and reports. */
public final class Warnings {
    private final List<String> list = new ArrayList<>();

    public void add(String w) {
        list.add(w);
    }

    public List<String> all() {
        return Collections.unmodifiableList(list);
    }

    public boolean isEmpty() {
        return list.isEmpty();
    }
}
