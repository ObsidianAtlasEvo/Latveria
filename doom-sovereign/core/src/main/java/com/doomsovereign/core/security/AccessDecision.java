package com.doomsovereign.core.security;

/** Result of a permission check, with a reason the UI can show. */
public record AccessDecision(boolean allowed, String reason) {
    public static AccessDecision allow(String why) {
        return new AccessDecision(true, why);
    }

    public static AccessDecision deny(String why) {
        return new AccessDecision(false, why);
    }
}
