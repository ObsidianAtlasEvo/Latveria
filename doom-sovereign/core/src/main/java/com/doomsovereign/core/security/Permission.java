package com.doomsovereign.core.security;

public enum Permission {
    /** See status panels and read-only information. */
    VIEW,
    /** Operate a machine (start a craft, charge armour). */
    USE,
    /** Pass a security door or gate. */
    OPEN,
    /** Walk through a force field. */
    PASS_FIELD,
    /** Turrets and Doombots will not engage this identity. */
    TURRET_EXEMPT,
    /** Issue orders to Doombots. */
    COMMAND,
    /** Change settings and grant permissions the actor already holds. Only the owner can grant CONFIGURE. */
    CONFIGURE
}
