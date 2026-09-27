"""A tiny pixel-art canvas that only accepts palette names (so nothing off-palette can be drawn)."""
import numpy as np

from .palette import COLORS


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.g = [[None] * w for _ in range(h)]

    def px(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            if c is not None and c not in COLORS:
                raise KeyError(c)
            self.g[y][x] = c
        return self

    def get(self, x, y):
        return self.g[y][x] if 0 <= x < self.w and 0 <= y < self.h else None

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.px(x, y, c)
        return self

    def frame(self, x0, y0, x1, y1, c):
        for x in range(x0, x1 + 1):
            self.px(x, y0, c).px(x, y1, c)
        for y in range(y0, y1 + 1):
            self.px(x0, y, c).px(x1, y, c)
        return self

    def hline(self, x0, x1, y, c):
        return self.rect(x0, y, x1, y, c)

    def vline(self, x, y0, y1, c):
        return self.rect(x, y0, x, y1, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.px(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy
        return self

    def disc(self, cx, cy, r, c):
        for y in range(self.h):
            for x in range(self.w):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + 0.3:
                    self.px(x, y, c)
        return self

    def ring(self, cx, cy, r, c):
        for y in range(self.h):
            for x in range(self.w):
                d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if abs(d - r) < 0.6:
                    self.px(x, y, c)
        return self

    def outline(self, c="steel_recess"):
        """Vanilla-style item outline: transparent pixels touching the shape become ``c``."""
        add = []
        for y in range(self.h):
            for x in range(self.w):
                if self.g[y][x] is None and any(self.get(x + dx, y + dy) not in (None, c) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    add.append((x, y))
        for x, y in add:
            self.g[y][x] = c
        return self

    def shade_edges(self, light="steel_hi", dark="steel_recess", only=None):
        """Top-left light, bottom-right shadow on the edge pixels of each filled region."""
        src = [row[:] for row in self.g]
        for y in range(self.h):
            for x in range(self.w):
                v = src[y][x]
                if v is None or (only and v not in only):
                    continue
                up = src[y - 1][x] if y > 0 else None
                left = src[y][x - 1] if x > 0 else None
                down = src[y + 1][x] if y + 1 < self.h else None
                right = src[y][x + 1] if x + 1 < self.w else None
                if up is None or left is None:
                    self.g[y][x] = light
                elif down is None or right is None:
                    self.g[y][x] = dark
        return self

    def array(self):
        a = np.zeros((self.h, self.w, 4), np.uint8)
        for y in range(self.h):
            for x in range(self.w):
                c = self.g[y][x]
                if c is not None:
                    a[y, x] = COLORS[c] + (255,)
        return a

    def save(self, path):
        from PIL import Image
        Image.fromarray(self.array(), "RGBA").save(path)
