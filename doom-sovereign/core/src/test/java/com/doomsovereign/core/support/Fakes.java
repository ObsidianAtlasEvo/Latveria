package com.doomsovereign.core.support;

import com.doomsovereign.core.api.ArmorRuntimeAdapter;
import com.doomsovereign.core.api.FlightEnvironment;
import java.util.UUID;

/** Small mutable fakes for the integration interfaces. */
public final class Fakes {
    private Fakes() {
    }

    public static final class Env implements FlightEnvironment {
        public boolean onGround = true;
        public double vy;
        public double fall;
        public boolean fluid;
        public int clearance = 32;

        @Override public boolean onGround() { return onGround; }
        @Override public double verticalVelocity() { return vy; }
        @Override public double fallDistance() { return fall; }
        @Override public boolean inFluid() { return fluid; }
        @Override public int clearanceBelow() { return clearance; }

        public static Env ground() { return new Env(); }

        public static Env air() {
            Env e = new Env();
            e.onGround = false;
            return e;
        }
    }

    public static final class Wearer implements ArmorRuntimeAdapter {
        public final UUID id = UUID.randomUUID();
        public int pieces = 4;
        public double durability = 1;
        public long time;

        @Override public UUID playerId() { return id; }
        @Override public int equippedPieces() { return pieces; }
        @Override public double durability() { return durability; }
        @Override public long gameTime() { return time; }
    }
}
