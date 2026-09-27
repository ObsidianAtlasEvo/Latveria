package com.doomsovereign.core.shield;

/**
 * Outcome of one hit against the field.
 *
 * @param absorbed      damage the field took
 * @param passedThrough damage that reaches the wearer (armour and vanilla handling still apply)
 * @param collapsed     this hit collapsed the field
 * @param ripple        0..1 visual/audio strength for the impact effect at {@code bearingDeg}
 * @param bearingDeg    where on the field the impact landed (relative to facing)
 */
public record AbsorbResult(double absorbed, double passedThrough, boolean collapsed, double ripple, double bearingDeg) {
    public static AbsorbResult untouched(double amount, double bearing) {
        return new AbsorbResult(0, amount, false, 0, bearing);
    }
}
