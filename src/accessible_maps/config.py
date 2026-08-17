from __future__ import annotations

from dataclasses import dataclass

from .constants import GEOFABRIK_ENGLAND, GEOFABRIK_EUROPE, GEOFABRIK_UK


@dataclass(frozen=True, slots=True)
class Region:
    name: str
    source_url: str
    boundary: tuple[tuple[float, float], ...] = ()


REGIONS: tuple[Region, ...] = (
    Region(
        "scotland",
        f"{GEOFABRIK_UK}/scotland-latest-free.gpkg.zip",
        boundary=((-14.0155, 54.434), (-0.3209, 54.434), (-0.3209, 61.061), (-14.0155, 61.061), (-14.0155, 54.434)),
    ),
    Region(
        "wales",
        f"{GEOFABRIK_UK}/wales-latest-free.gpkg.zip",
        boundary=((-5.8077, 51.229), (-2.6499, 51.229), (-2.6499, 53.635), (-5.8077, 53.635), (-5.8077, 51.229)),
    ),
    Region(
        "northern-ireland",
        f"{GEOFABRIK_EUROPE}/ireland-and-northern-ireland-latest-free.gpkg.zip",
        boundary=((-8.1775, 53.8702), (-5.0778, 53.8702), (-5.0778, 55.4436), (-8.1775, 55.4436), (-8.1775, 53.8702)),
    ),
    Region(
        "isle-of-man",
        f"{GEOFABRIK_EUROPE}/isle-of-man-latest-free.gpkg.zip",
        boundary=((-5.1707, 53.845), (-3.9654, 53.845), (-3.9654, 54.5534), (-5.1707, 54.5534), (-5.1707, 53.845)),
    ),
    Region(
        "guernsey-jersey",
        f"{GEOFABRIK_EUROPE}/guernsey-jersey-latest-free.gpkg.zip",
        boundary=((-2.6761, 48.9549), (-1.9124, 48.9549), (-1.9124, 49.7378), (-2.6761, 49.7378), (-2.6761, 48.9549)),
    ),
    Region(
        "bedfordshire",
        f"{GEOFABRIK_ENGLAND}/bedfordshire-latest-free.gpkg.zip",
        boundary=((-0.7022, 51.8051), (-0.144, 51.8051), (-0.144, 52.323), (-0.7022, 52.323), (-0.7022, 51.8051)),
    ),
    Region(
        "berkshire",
        f"{GEOFABRIK_ENGLAND}/berkshire-latest-free.gpkg.zip",
        boundary=((-1.5881, 51.329), (-0.49, 51.329), (-0.49, 51.5778), (-1.5881, 51.5778), (-1.5881, 51.329)),
    ),
    Region(
        "bristol",
        f"{GEOFABRIK_ENGLAND}/bristol-latest-free.gpkg.zip",
        boundary=((-3.1178, 51.3416), (-2.5104, 51.3416), (-2.5104, 51.5444), (-3.1178, 51.5444), (-3.1178, 51.3416)),
    ),
    Region(
        "buckinghamshire",
        f"{GEOFABRIK_ENGLAND}/buckinghamshire-latest-free.gpkg.zip",
        boundary=((-1.1407, 51.4855), (-0.4766, 51.4855), (-0.4766, 52.1963), (-1.1407, 52.1963), (-1.1407, 51.4855)),
    ),
    Region(
        "cambridgeshire",
        f"{GEOFABRIK_ENGLAND}/cambridgeshire-latest-free.gpkg.zip",
        boundary=((-0.4999, 52.0058), (0.5145, 52.0058), (0.5145, 52.74), (-0.4999, 52.74), (-0.4999, 52.0058)),
    ),
    Region(
        "cheshire",
        f"{GEOFABRIK_ENGLAND}/cheshire-latest-free.gpkg.zip",
        boundary=((-3.1283, 52.9472), (-1.9748, 52.9472), (-1.9748, 53.4809), (-3.1283, 53.4809), (-3.1283, 52.9472)),
    ),
    Region(
        "cornwall",
        f"{GEOFABRIK_ENGLAND}/cornwall-latest-free.gpkg.zip",
        boundary=((-6.4458, 49.8646), (-4.1649, 49.8646), (-4.1649, 50.9313), (-6.4458, 50.9313), (-6.4458, 49.8646)),
    ),
    Region(
        "cumbria",
        f"{GEOFABRIK_ENGLAND}/cumbria-latest-free.gpkg.zip",
        boundary=((-3.6406, 54.0396), (-2.159, 54.0396), (-2.159, 55.189), (-3.6406, 55.189), (-3.6406, 54.0396)),
    ),
    Region(
        "derbyshire",
        f"{GEOFABRIK_ENGLAND}/derbyshire-latest-free.gpkg.zip",
        boundary=((-2.0341, 52.6965), (-1.1665, 52.6965), (-1.1665, 53.5405), (-2.0341, 53.5405), (-2.0341, 52.6965)),
    ),
    Region(
        "devon",
        f"{GEOFABRIK_ENGLAND}/devon-latest-free.gpkg.zip",
        boundary=((-4.681, 50.2014), (-2.8866, 50.2014), (-2.8866, 51.2468), (-4.681, 51.2468), (-4.681, 50.2014)),
    ),
    Region(
        "dorset",
        f"{GEOFABRIK_ENGLAND}/dorset-latest-free.gpkg.zip",
        boundary=((-2.9616, 50.5127), (-1.6817, 50.5127), (-1.6817, 51.081), (-2.9616, 51.081), (-2.9616, 50.5127)),
    ),
    Region(
        "durham",
        f"{GEOFABRIK_ENGLAND}/durham-latest-free.gpkg.zip",
        boundary=((-2.3557, 54.4515), (-1.2397, 54.4515), (-1.2397, 54.9187), (-2.3557, 54.9187), (-2.3557, 54.4515)),
    ),
    Region(
        "east-sussex",
        f"{GEOFABRIK_ENGLAND}/east-sussex-latest-free.gpkg.zip",
        boundary=((-0.2451, 50.7334), (0.8679, 50.7334), (0.8679, 51.1475), (-0.2451, 51.1475), (-0.2451, 50.7334)),
    ),
    Region(
        "east-yorkshire-with-hull",
        f"{GEOFABRIK_ENGLAND}/east-yorkshire-with-hull-latest-free.gpkg.zip",
        boundary=((-1.1036, 53.5706), (0.1498, 53.5706), (0.1498, 54.1765), (-1.1036, 54.1765), (-1.1036, 53.5706)),
    ),
    Region(
        "essex",
        f"{GEOFABRIK_ENGLAND}/essex-latest-free.gpkg.zip",
        boundary=((-0.0198, 51.4483), (1.2966, 51.4483), (1.2966, 52.0927), (-0.0198, 52.0927), (-0.0198, 51.4483)),
    ),
    Region(
        "gloucestershire",
        f"{GEOFABRIK_ENGLAND}/gloucestershire-latest-free.gpkg.zip",
        boundary=((-2.7107, 51.4159), (-1.6152, 51.4159), (-1.6152, 52.1126), (-2.7107, 52.1126), (-2.7107, 51.4159)),
    ),
    Region(
        "greater-london",
        f"{GEOFABRIK_ENGLAND}/greater-london-latest-free.gpkg.zip",
        boundary=((-0.5104, 51.2868), (0.334, 51.2868), (0.334, 51.6919), (-0.5104, 51.6919), (-0.5104, 51.2868)),
    ),
    Region(
        "greater-manchester",
        f"{GEOFABRIK_ENGLAND}/greater-manchester-latest-free.gpkg.zip",
        boundary=((-2.7304, 53.3273), (-1.9096, 53.3273), (-1.9096, 53.6857), (-2.7304, 53.6857), (-2.7304, 53.3273)),
    ),
    Region(
        "hampshire",
        f"{GEOFABRIK_ENGLAND}/hampshire-latest-free.gpkg.zip",
        boundary=((-1.9573, 50.706), (-0.7293, 50.706), (-0.7293, 51.3839), (-1.9573, 51.3839), (-1.9573, 50.706)),
    ),
    Region(
        "herefordshire",
        f"{GEOFABRIK_ENGLAND}/herefordshire-latest-free.gpkg.zip",
        boundary=((-3.1419, 51.8259), (-2.338, 51.8259), (-2.338, 52.3955), (-3.1419, 52.3955), (-3.1419, 51.8259)),
    ),
    Region(
        "hertfordshire",
        f"{GEOFABRIK_ENGLAND}/hertfordshire-latest-free.gpkg.zip",
        boundary=((-0.7458, 51.5996), (0.1956, 51.5996), (0.1956, 52.0805), (-0.7458, 52.0805), (-0.7458, 51.5996)),
    ),
    Region(
        "isle-of-wight",
        f"{GEOFABRIK_ENGLAND}/isle-of-wight-latest-free.gpkg.zip",
        boundary=((-1.5918, 50.5747), (-1.0627, 50.5747), (-1.0627, 50.7676), (-1.5918, 50.7676), (-1.5918, 50.5747)),
    ),
    Region(
        "kent",
        f"{GEOFABRIK_ENGLAND}/kent-latest-free.gpkg.zip",
        boundary=((0.0335, 50.9105), (1.4518, 50.9105), (1.4518, 51.5037), (0.0335, 51.5037), (0.0335, 50.9105)),
    ),
    Region(
        "lancashire",
        f"{GEOFABRIK_ENGLAND}/lancashire-latest-free.gpkg.zip",
        boundary=((-3.0845, 53.4828), (-2.0451, 53.4828), (-2.0451, 54.2396), (-3.0845, 54.2396), (-3.0845, 53.4828)),
    ),
    Region(
        "leicestershire",
        f"{GEOFABRIK_ENGLAND}/leicestershire-latest-free.gpkg.zip",
        boundary=((-1.5975, 52.3922), (-0.6641, 52.3922), (-0.6641, 52.9777), (-1.5975, 52.9777), (-1.5975, 52.3922)),
    ),
    Region(
        "lincolnshire",
        f"{GEOFABRIK_ENGLAND}/lincolnshire-latest-free.gpkg.zip",
        boundary=((-0.95, 52.6402), (0.358, 52.6402), (0.358, 53.7245), (-0.95, 53.7245), (-0.95, 52.6402)),
    ),
    Region(
        "merseyside",
        f"{GEOFABRIK_ENGLAND}/merseyside-latest-free.gpkg.zip",
        boundary=((-3.2638, 53.2864), (-2.5767, 53.2864), (-2.5767, 53.7044), (-3.2638, 53.7044), (-3.2638, 53.2864)),
    ),
    Region(
        "norfolk",
        f"{GEOFABRIK_ENGLAND}/norfolk-latest-free.gpkg.zip",
        boundary=((0.1536, 52.3553), (1.7458, 52.3553), (1.7458, 52.9916), (0.1536, 52.9916), (0.1536, 52.3553)),
    ),
    Region(
        "north-yorkshire",
        f"{GEOFABRIK_ENGLAND}/north-yorkshire-latest-free.gpkg.zip",
        boundary=((-2.5647, 53.6211), (-0.2124, 53.6211), (-0.2124, 54.648), (-2.5647, 54.648), (-2.5647, 53.6211)),
    ),
    Region(
        "northamptonshire",
        f"{GEOFABRIK_ENGLAND}/northamptonshire-latest-free.gpkg.zip",
        boundary=((-1.3324, 51.9773), (-0.3416, 51.9773), (-0.3416, 52.6436), (-1.3324, 52.6436), (-1.3324, 51.9773)),
    ),
    Region(
        "northumberland",
        f"{GEOFABRIK_ENGLAND}/northumberland-latest-free.gpkg.zip",
        boundary=((-2.6898, 54.7824), (-1.4599, 54.7824), (-1.4599, 55.8117), (-2.6898, 55.8117), (-2.6898, 54.7824)),
    ),
    Region(
        "nottinghamshire",
        f"{GEOFABRIK_ENGLAND}/nottinghamshire-latest-free.gpkg.zip",
        boundary=((-1.3446, 52.7894), (-0.6663, 52.7894), (-0.6663, 53.5025), (-1.3446, 53.5025), (-1.3446, 52.7894)),
    ),
    Region(
        "oxfordshire",
        f"{GEOFABRIK_ENGLAND}/oxfordshire-latest-free.gpkg.zip",
        boundary=((-1.7195, 51.4594), (-0.8701, 51.4594), (-0.8701, 52.1685), (-1.7195, 52.1685), (-1.7195, 51.4594)),
    ),
    Region(
        "rutland",
        f"{GEOFABRIK_ENGLAND}/rutland-latest-free.gpkg.zip",
        boundary=((-0.8218, 52.5248), (-0.4284, 52.5248), (-0.4284, 52.7598), (-0.8218, 52.7598), (-0.8218, 52.5248)),
    ),
    Region(
        "shropshire",
        f"{GEOFABRIK_ENGLAND}/shropshire-latest-free.gpkg.zip",
        boundary=((-3.2355, 52.3063), (-2.2329, 52.3063), (-2.2329, 52.9984), (-3.2355, 52.9984), (-3.2355, 52.3063)),
    ),
    Region(
        "somerset",
        f"{GEOFABRIK_ENGLAND}/somerset-latest-free.gpkg.zip",
        boundary=((-3.8398, 50.8208), (-2.2444, 50.8208), (-2.2444, 51.5027), (-3.8398, 51.5027), (-3.8398, 50.8208)),
    ),
    Region(
        "south-yorkshire",
        f"{GEOFABRIK_ENGLAND}/south-yorkshire-latest-free.gpkg.zip",
        boundary=((-1.8226, 53.3015), (-0.8653, 53.3015), (-0.8653, 53.6612), (-1.8226, 53.6612), (-1.8226, 53.3015)),
    ),
    Region(
        "staffordshire",
        f"{GEOFABRIK_ENGLAND}/staffordshire-latest-free.gpkg.zip",
        boundary=((-2.4708, 52.4232), (-1.5854, 52.4232), (-1.5854, 53.2262), (-2.4708, 53.2262), (-2.4708, 52.4232)),
    ),
    Region(
        "suffolk",
        f"{GEOFABRIK_ENGLAND}/suffolk-latest-free.gpkg.zip",
        boundary=((0.34, 51.9318), (1.7689, 51.9318), (1.7689, 52.5502), (0.34, 52.5502), (0.34, 51.9318)),
    ),
    Region(
        "surrey",
        f"{GEOFABRIK_ENGLAND}/surrey-latest-free.gpkg.zip",
        boundary=((-0.8489, 51.0715), (0.0582, 51.0715), (0.0582, 51.4716), (-0.8489, 51.4716), (-0.8489, 51.0715)),
    ),
    Region(
        "tyne-and-wear",
        f"{GEOFABRIK_ENGLAND}/tyne-and-wear-latest-free.gpkg.zip",
        boundary=((-1.8527, 54.799), (-1.3457, 54.799), (-1.3457, 55.0794), (-1.8527, 55.0794), (-1.8527, 54.799)),
    ),
    Region(
        "warwickshire",
        f"{GEOFABRIK_ENGLAND}/warwickshire-latest-free.gpkg.zip",
        boundary=((-1.962, 51.9554), (-1.1721, 51.9554), (-1.1721, 52.6872), (-1.962, 52.6872), (-1.962, 51.9554)),
    ),
    Region(
        "west-midlands",
        f"{GEOFABRIK_ENGLAND}/west-midlands-latest-free.gpkg.zip",
        boundary=((-2.2069, 52.3477), (-1.424, 52.3477), (-1.424, 52.6628), (-2.2069, 52.6628), (-2.2069, 52.3477)),
    ),
    Region(
        "west-sussex",
        f"{GEOFABRIK_ENGLAND}/west-sussex-latest-free.gpkg.zip",
        boundary=((-0.9576, 50.7218), (0.0445, 50.7218), (0.0445, 51.1673), (-0.9576, 51.1673), (-0.9576, 50.7218)),
    ),
    Region(
        "west-yorkshire",
        f"{GEOFABRIK_ENGLAND}/west-yorkshire-latest-free.gpkg.zip",
        boundary=((-2.1733, 53.5197), (-1.1988, 53.5197), (-1.1988, 53.9632), (-2.1733, 53.9632), (-2.1733, 53.5197)),
    ),
    Region(
        "wiltshire",
        f"{GEOFABRIK_ENGLAND}/wiltshire-latest-free.gpkg.zip",
        boundary=((-2.3656, 50.945), (-1.4857, 50.945), (-1.4857, 51.7031), (-2.3656, 51.7031), (-2.3656, 50.945)),
    ),
    Region(
        "worcestershire",
        f"{GEOFABRIK_ENGLAND}/worcestershire-latest-free.gpkg.zip",
        boundary=((-2.6632, 51.9666), (-1.7574, 51.9666), (-1.7574, 52.4553), (-2.6632, 52.4553), (-2.6632, 51.9666)),
    ),
)


def get_region(name: str) -> Region:
    for region in REGIONS:
        if region.name == name:
            return region
    raise ValueError(f"Unknown region: {name}")
