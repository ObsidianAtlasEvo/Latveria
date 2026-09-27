package com.doomsovereign.core.cooldown;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

/** Named cooldowns for one wearer, so abilities share one tested mechanism instead of ad hoc timers. */
public final class CooldownSet {
    private final Map<String, Cooldown> cooldowns = new LinkedHashMap<>();

    public Cooldown define(String ability, int ticks, int charges) {
        return cooldowns.computeIfAbsent(ability, k -> new Cooldown(ticks, charges));
    }

    public Cooldown get(String ability) {
        Cooldown c = cooldowns.get(ability);
        if (c == null) throw new IllegalArgumentException("unknown ability: " + ability);
        return c;
    }

    public boolean tryUse(String ability, long now) {
        return get(ability).tryUse(now);
    }

    public boolean ready(String ability, long now) {
        return get(ability).ready(now);
    }

    public void setReduction(double r) {
        cooldowns.values().forEach(c -> c.setReduction(r));
    }

    public Map<String, Cooldown> all() {
        return Collections.unmodifiableMap(cooldowns);
    }
}
