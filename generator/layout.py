"""Master plan of Doomstadt and Castle Doom (all coordinates relative to origin).

Origin (0,0,0) is the centre of Doomstadt's great plaza, at the height of the
player's feet.  +x is east, +z is south.  Castle Doom stands on a crag to the
north (negative z); the town spreads south of it inside its own walls.

  y = -1     village ground surface
  y = 11     top of the castle crag (plateau surface)
  y = 12     castle courtyard walking level (G)
"""

# overall footprint that is cleared, grounded and force-loaded
X_MIN, X_MAX = -150, 150
Z_MIN, Z_MAX = -252, 112
CLEAR_TOP = 62               # air is cleared up to here over everything
CASTLE_CLEAR = (-100, 100, -252, -66, 130)   # x1,x2,z1,z2,ytop: higher clear over the castle

# crag / plateau
G = 12                        # castle walking level
PLAT = (-70, 70, -226, -94)   # plateau top rectangle (x1,x2,z1,z2) at y=11
CRAG_STEP = 2                 # each layer below widens by this much

# moat (outer rectangle and inner rectangle; water between)
MOAT_OUT = (-68, 68, -224, -96)
MOAT_IN = (-62, 62, -218, -102)

# curtain wall outer faces
WX1, WX2 = -52, 52
WZ1, WZ2 = -208, -112         # north face, south face
WALL_T = 3
WALL_TOP = 27                 # wall-walk floor block
KEEP = (-30, 30, -196, -150)  # x1,x2,z1,z2

# grand stair from the town up to the drawbridge
STAIR_X = 7                   # half width
STAIR_Z1, STAIR_Z2 = -94, -70

# town
TOWN_X = 144                  # town wall outer face at x = +-144
TOWN_ZS = 104                 # south wall outer face
TOWN_ZN = -70                 # north edge (meets the crag)
PLAZA_R = 24
