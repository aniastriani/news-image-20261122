"""The World in One Image - Sunday 22 November 2026.

A newspaper front page drawn entirely in code: a hand-built 5x7 pixel
font stored as rows of five bits, a small RGB canvas with its own
drawing primitives, simple pictograms for each story, and a from-scratch
PNG writer. Pure Python standard library only -- no network, no clock,
no randomness, no files read at run time. Every run writes the same
bytes to a deterministic 1024x1024 PNG.

Stories, all first reported on Sunday 22 November 2026:
  1. Trump lands in Shenzhen for the APEC summit; a trilateral meeting
     with Xi and Putin is planned.
  2. Estonia will close its border with Russia; Moscow warns of a new
     Iron Curtain.
  3. US airlines are warned of a possible al-Qaeda-linked attack plot
     ahead of Thanksgiving.
  4. France seeks UN Security Council action after Myanmar rejects the
     world court's genocide ruling.
  5. COP31 climate talks close in on a final deal as US tech giants
     skip the AI pledge.
  6. Mexico arrests "El Chapo Isidro", the FBI's most-wanted drug
     lord; 11 killed in violence in Sinaloa.
"""

import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

PAPER = (247, 242, 230)
PANEL = (255, 255, 255)
INK = (24, 24, 24)
RED = (168, 32, 32)
NAVY = (28, 52, 94)
TEAL = (18, 110, 96)
OCHRE = (178, 124, 32)
GOLD = (212, 175, 55)
SKY = (158, 196, 222)
GREY = (110, 110, 105)

# ---------------------------------------------------------------------------
# 5x7 bitmap font. Each glyph is seven rows; each row is a five-bit
# number, its most significant bit the leftmost cell. Drawn by hand.
# ---------------------------------------------------------------------------

FONT = {
    "A": (14, 17, 17, 31, 17, 17, 17),
    "B": (30, 17, 17, 30, 17, 17, 30),
    "C": (14, 17, 16, 16, 16, 17, 14),
    "D": (30, 17, 17, 17, 17, 17, 30),
    "E": (31, 16, 16, 30, 16, 16, 31),
    "F": (31, 16, 16, 30, 16, 16, 16),
    "G": (14, 17, 16, 23, 17, 17, 15),
    "H": (17, 17, 17, 31, 17, 17, 17),
    "I": (14, 4, 4, 4, 4, 4, 14),
    "J": (7, 2, 2, 2, 2, 18, 12),
    "K": (17, 18, 20, 24, 20, 18, 17),
    "L": (16, 16, 16, 16, 16, 16, 31),
    "M": (17, 27, 21, 21, 17, 17, 17),
    "N": (17, 25, 21, 19, 17, 17, 17),
    "O": (14, 17, 17, 17, 17, 17, 14),
    "P": (30, 17, 17, 30, 16, 16, 16),
    "Q": (14, 17, 17, 17, 21, 18, 13),
    "R": (30, 17, 17, 30, 20, 18, 17),
    "S": (15, 16, 16, 14, 1, 1, 30),
    "T": (31, 4, 4, 4, 4, 4, 4),
    "U": (17, 17, 17, 17, 17, 17, 14),
    "V": (17, 17, 17, 17, 17, 10, 4),
    "W": (17, 17, 17, 21, 21, 27, 17),
    "X": (17, 17, 10, 4, 10, 17, 17),
    "Y": (17, 17, 10, 4, 4, 4, 4),
    "Z": (31, 1, 2, 4, 8, 16, 31),
    "0": (14, 17, 19, 21, 25, 17, 14),
    "1": (4, 12, 4, 4, 4, 4, 14),
    "2": (14, 17, 1, 6, 8, 16, 31),
    "3": (31, 2, 4, 2, 1, 17, 14),
    "4": (2, 6, 10, 18, 31, 2, 2),
    "5": (31, 16, 30, 1, 1, 17, 14),
    "6": (6, 8, 16, 30, 17, 17, 14),
    "7": (31, 1, 2, 4, 8, 8, 8),
    "8": (14, 17, 17, 14, 17, 17, 14),
    "9": (14, 17, 17, 15, 1, 2, 12),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 12, 12),
    ",": (0, 0, 0, 0, 12, 4, 8),
    "'": (4, 4, 8, 0, 0, 0, 0),
    ":": (0, 12, 12, 0, 12, 12, 0),
    ";": (0, 12, 12, 0, 12, 4, 8),
    "-": (0, 0, 0, 14, 0, 0, 0),
    "/": (1, 2, 2, 4, 8, 8, 16),
    "(": (2, 4, 8, 8, 8, 4, 2),
    ")": (8, 4, 2, 2, 2, 4, 8),
    "!": (4, 4, 4, 4, 4, 0, 4),
    "?": (14, 17, 1, 6, 4, 0, 4),
    "%": (25, 26, 2, 4, 8, 11, 19),
    "&": (12, 18, 20, 8, 21, 18, 13),
    "+": (0, 4, 4, 31, 4, 4, 0),
    '"': (10, 10, 0, 0, 0, 0, 0),
    "=": (0, 0, 31, 0, 31, 0, 0),
}

GLYPH_W = 5
GLYPH_H = 7
GLYPH_ADVANCE = 6  # glyph width plus one blank column, in font units


def text_width(text, scale):
    """Width in pixels of text drawn at the given scale."""
    return len(text) * GLYPH_ADVANCE * scale - scale


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns a list of lines fitting max_width."""
    max_chars = max(1, max_width // (GLYPH_ADVANCE * scale))
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        line = ""
        for word in words:
            trial = word if not line else line + " " + word
            if len(trial) <= max_chars:
                line = trial
            else:
                if line:
                    lines.append(line)
                # A single word longer than the line: hard-split it.
                while len(word) > max_chars:
                    lines.append(word[:max_chars])
                    word = word[max_chars:]
                line = word
        if line:
            lines.append(line)
    return lines


# ---------------------------------------------------------------------------
# Tiny RGB canvas with its own drawing primitives.
# ---------------------------------------------------------------------------

class Canvas:
    def __init__(self, width, height, colour):
        self.width = width
        self.height = height
        self.pixels = bytearray(colour * (width * height))

    def set_px(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i] = colour[0]
            self.pixels[i + 1] = colour[1]
            self.pixels[i + 2] = colour[2]

    def fill_rect(self, x, y, w, h, colour):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        for yy in range(y0, y1):
            base = (yy * self.width + x0) * 3
            row = bytes(colour) * (x1 - x0)
            self.pixels[base:base + (x1 - x0) * 3] = row

    def rect(self, x, y, w, h, colour, thickness=1):
        self.fill_rect(x, y, w, thickness, colour)
        self.fill_rect(x, y + h - thickness, w, thickness, colour)
        self.fill_rect(x, y, thickness, h, colour)
        self.fill_rect(x + w - thickness, y, thickness, h, colour)

    def hline(self, x, y, w, colour, thickness=1):
        self.fill_rect(x, y, w, thickness, colour)

    def vline(self, x, y, h, colour, thickness=1):
        self.fill_rect(x, y, thickness, h, colour)

    def line(self, x0, y0, x1, y1, colour):
        """Bresenham line."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set_px(x0, y0, colour)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, colour):
        """Midpoint circle outline."""
        x = 0
        y = r
        d = 3 - 2 * r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                           (cx + x, cy - y), (cx - x, cy - y),
                           (cx + y, cy + x), (cx - y, cy + x),
                           (cx + y, cy - x), (cx - y, cy - x)):
                self.set_px(px, py, colour)
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1

    def fill_circle(self, cx, cy, r, colour):
        for yy in range(cy - r, cy + r + 1):
            half = int((r * r - (yy - cy) ** 2) ** 0.5)
            self.fill_rect(cx - half, yy, half * 2 + 1, 1, colour)

    def triangle(self, x0, y0, x1, y1, x2, y2, colour):
        """Filled triangle by scanline."""
        points = sorted(((x0, y0), (x1, y1), (x2, y2)), key=lambda p: p[1])
        (ax, ay), (bx, by), (cx, cy) = points
        if ay == cy:
            return
        for y in range(ay, cy + 1):
            if y < by:
                t1 = (y - ay) / (by - ay) if by != ay else 0.0
                xa = ax + (bx - ax) * t1
            else:
                t2 = (y - by) / (cy - by) if cy != by else 0.0
                xa = bx + (cx - bx) * t2
            t3 = (y - ay) / (cy - ay)
            xb = ax + (cx - ax) * t3
            lo, hi = (int(xa), int(xb)) if xa <= xb else (int(xb), int(xa))
            self.fill_rect(lo, y, hi - lo + 1, 1, colour)

    def draw_text(self, x, y, text, scale, colour):
        """Draw text; input is upper-cased, unknown glyphs become blank."""
        cx = x
        for ch in text.upper():
            rows = FONT.get(ch)
            if rows:
                for r in range(GLYPH_H):
                    bits = rows[r]
                    for c in range(GLYPH_W):
                        if (bits >> (GLYPH_W - 1 - c)) & 1:
                            self.fill_rect(cx + c * scale, y + r * scale,
                                           scale, scale, colour)
            cx += GLYPH_ADVANCE * scale
        return cx

    def draw_block(self, x, y, text, max_width, scale, colour,
                   line_gap=4):
        """Draw wrapped text; returns the y just below the last line."""
        lines = wrap_text(text, max_width, scale)
        for line in lines:
            self.draw_text(x, y, line, scale, colour)
            y += GLYPH_H * scale + line_gap
        return y


# ---------------------------------------------------------------------------
# PNG writer: colour type 2 (RGB), filter 0 on every scanline, no ancillary
# chunks, so the output is fully deterministic.
# ---------------------------------------------------------------------------

def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(canvas, path):
    raw = bytearray()
    stride = canvas.width * 3
    for y in range(canvas.height):
        raw.append(0)
        start = y * stride
        raw += canvas.pixels[start:start + stride]
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", canvas.width,
                                       canvas.height, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


# ---------------------------------------------------------------------------
# Pictograms, one per story. Each draws inside a small box (x, y, w, h).
# ---------------------------------------------------------------------------

def draw_flags(c, x, y, w, h):
    """Three flagpoles: United States, China, Russia."""
    pole_y = y + 8
    pole_h = h - 30
    flag_w = (w - 40) // 3
    specs = [
        ("us", (178, 34, 34), (255, 255, 255)),
        ("cn", (222, 41, 16), (255, 215, 0)),
        ("ru", (255, 255, 255), (0, 57, 166)),
    ]
    for i, (name, main, accent) in enumerate(specs):
        px = x + 10 + i * (flag_w + 10)
        c.vline(px, pole_y, pole_h, INK, 3)
        fx, fy = px + 3, pole_y
        fw, fh = flag_w - 3, 44
        if name == "us":
            for s in range(7):
                c.fill_rect(fx, fy + s * 6, fw, 6,
                            main if s % 2 == 0 else (255, 255, 255))
            c.fill_rect(fx, fy, fw // 2, 24, NAVY)
            for dy in (4, 12, 20):
                for dx in (4, 14, 24):
                    c.fill_rect(fx + dx, fy + dy, 3, 3, (255, 255, 255))
        elif name == "cn":
            c.fill_rect(fx, fy, fw, fh, main)
            c.fill_circle(fx + 14, fy + 12, 5, accent)
            for dx, dy in ((28, 8), (34, 14), (34, 22), (28, 26)):
                c.fill_rect(fx + dx, fy + dy, 3, 3, accent)
        else:
            third = fh // 3
            c.fill_rect(fx, fy, fw, third, (255, 255, 255))
            c.fill_rect(fx, fy + third, fw, third, accent)
            c.fill_rect(fx, fy + 2 * third, fw, fh - 2 * third, RED)
            c.rect(fx, fy, fw, fh, INK, 1)
        c.fill_circle(px, pole_y - 2, 3, GOLD)
    # Shenzhen skyline behind the table.
    sky_base = y + h - 40
    for bx, bw, bh in ((8, 34, 70), (48, 26, 100), (80, 40, 58),
                       (126, 26, 92), (158, 30, 64), (194, 34, 108),
                       (234, 26, 76), (266, 40, 58), (312, 28, 84)):
        c.fill_rect(x + bx, sky_base - bh, bw, bh, (214, 222, 232))
        for wy in range(sky_base - bh + 8, sky_base - 6, 12):
            for wx in range(x + bx + 6, x + bx + bw - 4, 10):
                c.fill_rect(wx, wy, 3, 4, NAVY)
    # Table with three seated figures below the flags.
    ty = y + h - 34
    c.fill_rect(x + 8, ty, w - 16, 6, (120, 82, 40))
    c.fill_rect(x + 16, ty + 6, 8, 26, (120, 82, 40))
    c.fill_rect(x + w - 24, ty + 6, 8, 26, (120, 82, 40))
    for i, suit in enumerate((NAVY, RED, TEAL)):
        fx = x + 40 + i * ((w - 80) // 2)
        c.fill_circle(fx, ty - 22, 11, (232, 196, 160))
        c.triangle(fx - 18, ty - 4, fx + 18, ty - 4, fx, ty - 26, suit)


def draw_fence(c, x, y, w, h):
    """A border fence with a striped barrier."""
    base = y + h - 14
    c.fill_rect(x, base, w, 6, (90, 90, 90))
    for i in range(7):
        px = x + 12 + i * ((w - 24) // 6)
        c.fill_rect(px, y + 8, 5, base - y - 8, INK)
    c.fill_rect(x, y + 22, w, 5, INK)
    c.fill_rect(x, y + 48, w, 5, INK)
    c.line(x + 6, y + 8, x + w - 6, base, RED)
    c.line(x + w - 6, y + 8, x + 6, base, RED)
    # Barrier stripe across the bottom.
    for i in range(10):
        col = RED if i % 2 == 0 else (255, 255, 255)
        c.fill_rect(x + 10 + i * ((w - 20) // 10), base + 8,
                    (w - 20) // 10, 10, col)


def draw_plane(c, x, y, w, h):
    """An airliner under a warning triangle."""
    cy = y + 30
    # Tail fin.
    c.triangle(x + 18, cy - 8, x + 34, cy - 28, x + 44, cy - 8, NAVY)
    # Fuselage with a pointed nose.
    c.fill_rect(x + 16, cy - 11, w - 96, 22, SKY)
    c.fill_circle(x + 16, cy, 11, SKY)
    c.triangle(x + w - 80, cy - 11, x + w - 52, cy,
               x + w - 80, cy + 11, SKY)
    # Windows along the fuselage.
    for i in range(9):
        c.fill_rect(x + 34 + i * 30, cy - 4, 8, 6, NAVY)
    # Main wing sweeping down, tailplane sweeping up behind.
    c.triangle(x + w // 2 - 24, cy + 11, x + w // 2 + 24, cy + 11,
               x + w // 2 + 58, cy + 26, NAVY)
    c.triangle(x + 44, cy - 11, x + 66, cy - 11, x + 88, cy - 26, NAVY)
    # Warning triangle, top right.
    tx, ty = x + w - 44, y + 2
    c.triangle(tx, ty + 34, tx + 18, ty, tx + 36, ty + 34, GOLD)
    c.triangle(tx + 4, ty + 30, tx + 18, ty + 6, tx + 32, ty + 30, INK)
    c.draw_text(tx + 14, ty + 12, "!", 2, GOLD)


def draw_scales(c, x, y, w, h):
    """Scales of justice for the world court."""
    cx = x + w // 2
    top = y + 6
    base = y + h - 8
    c.vline(cx, top, base - top, INK, 4)
    c.fill_rect(cx - 26, base, 52, 5, INK)
    c.fill_rect(cx - 14, top - 4, 28, 5, INK)
    c.hline(cx - 52, top + 8, 104, INK, 3)
    for sx in (cx - 52, cx + 52):
        c.line(sx, top + 8, sx - 14, top + 34, INK)
        c.line(sx, top + 8, sx + 14, top + 34, INK)
        c.triangle(sx - 18, top + 34, sx + 18, top + 34, sx, top + 52,
                   OCHRE)
    c.fill_circle(cx, top, 5, GOLD)


def draw_globe(c, x, y, w, h):
    """A globe with a leaf for the climate talks."""
    cx, cy = x + w // 2, y + h // 2
    r = min(w, h) // 2 - 6
    c.fill_circle(cx, cy, r, SKY)
    c.circle(cx, cy, r, INK)
    c.fill_circle(cx - r // 3, cy - r // 4, r // 3, TEAL)
    c.fill_circle(cx + r // 3, cy + r // 4, r // 4, TEAL)
    c.fill_circle(cx + r // 5, cy - r // 2, r // 5, TEAL)
    # Two leaves sprouting from the top of the globe.
    lx, ly = cx + r // 3, cy - r + 2
    c.line(lx, ly + 6, lx, ly - 6, TEAL)
    c.triangle(lx, ly - 6, lx - 14, ly - 14, lx - 2, ly - 2, TEAL)
    c.triangle(lx, ly - 6, lx + 14, ly - 14, lx + 2, ly - 2, TEAL)


def draw_handcuffs(c, x, y, w, h):
    """Handcuffs and a star badge."""
    cy = y + h // 2
    c.fill_circle(x + 26, cy, 20, GREY)
    c.fill_circle(x + 26, cy, 13, PANEL)
    c.fill_circle(x + w - 26, cy, 20, GREY)
    c.fill_circle(x + w - 26, cy, 13, PANEL)
    c.line(x + 26, cy - 20, x + w - 26, cy - 20, INK)
    c.fill_circle(x + w // 2, cy - 20, 4, INK)
    # Star badge below the chain.
    bx, by = x + w // 2, y + h - 26
    c.triangle(bx, by - 14, bx - 5, by + 2, bx + 5, by + 2, GOLD)
    c.triangle(bx - 12, by - 4, bx + 12, by - 4, bx, by + 12, GOLD)
    c.fill_circle(bx, by, 6, GOLD)


# ---------------------------------------------------------------------------
# Page layout.
# ---------------------------------------------------------------------------

MARGIN = 28
CONTENT_W = WIDTH - 2 * MARGIN


def panel(c, x, y, w, h):
    c.fill_rect(x, y, w, h, PANEL)
    c.rect(x, y, w, h, INK, 2)


def kicker_headline_body(c, x, y, w, kicker, headline, body,
                         head_scale=3, body_scale=2, art=None, art_h=0):
    """One story block: red kicker, headline, body text, optional art."""
    inner = x + 16
    width = w - 32
    c.draw_text(inner, y, kicker, 2, RED)
    y += 22
    y = c.draw_block(inner, y, headline, width, head_scale, INK, 3)
    y += 4
    y = c.draw_block(inner, y, body, width, body_scale, INK, 4)
    if art is not None:
        art(c, x + 16, y + 2, width, art_h)
    return y


def build_page():
    c = Canvas(WIDTH, HEIGHT, PAPER)

    # Masthead.
    title = "THE WORLD IN ONE IMAGE"
    c.draw_text((WIDTH - text_width(title, 5)) // 2, 30, title, 5, INK)
    c.hline(MARGIN, 82, CONTENT_W, INK, 3)
    date = "SUNDAY 22 NOVEMBER 2026"
    c.draw_text((WIDTH - text_width(date, 3)) // 2, 96, date, 3, RED)
    sub = "SIX STORIES THAT SHAPED THE DAY"
    c.draw_text((WIDTH - text_width(sub, 2)) // 2, 128, sub, 2, INK)
    c.hline(MARGIN, 152, CONTENT_W, INK, 6)

    # Lead story: the Shenzhen summit.
    ly, lh = 168, 284
    panel(c, MARGIN, ly, CONTENT_W, lh)
    tx = MARGIN + 20
    tw = 560
    c.draw_text(tx, ly + 18, "SUMMIT IN CHINA", 2, RED)
    y = c.draw_block(tx, ly + 46, "Trump lands in Shenzhen",
                     tw, 5, INK, 4)
    y = c.draw_block(tx, y + 2,
                     "APEC summit opens in China. A trilateral meeting "
                     "with Xi and Putin is planned.",
                     tw, 3, INK, 5)
    y = c.draw_block(tx, y + 6,
                     "Leaders from across Asia and the Pacific gather "
                     "in Shenzhen.",
                     tw, 3, INK, 5)
    draw_flags(c, MARGIN + 600, ly + 16, CONTENT_W - 620, lh - 32)

    # Middle row: Estonia and the airlines warning.
    my, mh = 468, 204
    mw = (CONTENT_W - 16) // 2
    panel(c, MARGIN, my, mw, mh)
    kicker_headline_body(
        c, MARGIN, my + 12, mw, "EUROPE",
        "Estonia to shut border",
        "Tallinn will close its frontier with Russia. Moscow warns of "
        "a new Iron Curtain.",
        art=draw_fence, art_h=56)
    panel(c, MARGIN + mw + 16, my, mw, mh)
    kicker_headline_body(
        c, MARGIN + mw + 16, my + 12, mw, "UNITED STATES",
        "Airlines warned of threat",
        "Carriers are told of a possible al-Qaeda-linked attack plot "
        "ahead of Thanksgiving.",
        art=draw_plane, art_h=56)

    # Bottom row: Myanmar, COP31, Mexico.
    by, bh = 688, 204
    bw = (CONTENT_W - 26) // 3
    panel(c, MARGIN, by, bw, bh)
    kicker_headline_body(
        c, MARGIN, by + 12, bw, "THE HAGUE",
        "France seeks UN action",
        "Paris turns to the Security Council after Myanmar rejects "
        "the world court's genocide ruling.",
        head_scale=2, art=draw_scales, art_h=52)
    panel(c, MARGIN + bw + 13, by, bw, bh)
    kicker_headline_body(
        c, MARGIN + bw + 13, by + 12, bw, "CLIMATE",
        "COP31 nears a deal",
        "Climate talks close in on a final text as US tech giants "
        "skip the AI pledge.",
        head_scale=2, art=draw_globe, art_h=52)
    panel(c, MARGIN + 2 * bw + 26, by, bw, bh)
    kicker_headline_body(
        c, MARGIN + 2 * bw + 26, by + 12, bw, "MEXICO",
        "Cartel kingpin seized",
        "Mexico arrests 'El Chapo Isidro', the FBI's most-wanted drug "
        "lord; 11 killed in Sinaloa.",
        head_scale=2, art=draw_handcuffs, art_h=52)

    # Footer.
    c.hline(MARGIN, 908, CONTENT_W, INK, 3)
    foot = "DRAWN ENTIRELY IN CODE - NO PHOTOGRAPHS - MAKE.FUN NEWS-IMAGE-20261122"
    c.draw_text((WIDTH - text_width(foot, 2)) // 2, 926, foot, 2, INK)
    foot2 = "SUNDAY 22 NOVEMBER 2026 - SIX STORIES, ONE PAGE"
    c.draw_text((WIDTH - text_width(foot2, 2)) // 2, 956, foot2, 2, GREY)
    return c


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "out")
    os.makedirs(out_dir, exist_ok=True)
    page = build_page()
    write_png(page, os.path.join(out_dir, "entry.png"))


if __name__ == "__main__":
    main()
