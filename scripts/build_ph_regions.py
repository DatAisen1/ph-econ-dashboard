"""
One-off geometry processing script - replaces the earlier 2-zone dissolve
(dissolve_ph_zones.py) now that we have real per-region PSA data for all
18 regions. No dissolving needed this time - each region is already its
own individual polygon in the source data; we're just relabeling each
feature with the PSA-matching name, using the hand-verified mapping in
seeds/ph_region_mapping.csv (built from direct inspection of both
datasets' region lists - see the mentor conversation for the verification).
"""

import csv
import json
import pathlib

SOURCE_PATH = pathlib.Path("/home/claude/philippines-json-maps/2019/geojson/regions/lowres/regions.0.001.json")
MAPPING_PATH = pathlib.Path("/home/claude/ph-econ-dashboard/seeds/ph_region_mapping.csv")
OUTPUT_PATH = pathlib.Path("/home/claude/ph-econ-dashboard/web/public/data/ph_regions.json")


def load_mapping() -> dict[str, dict]:
    mapping = {}
    with open(MAPPING_PATH) as f:
        for row in csv.DictReader(f):
            mapping[row["adm1_pcode"]] = {
                "psa_geolocation_name": row["psa_geolocation_name"],
                "short_label": row["short_label"],
            }
    return mapping


def main():
    source = json.loads(SOURCE_PATH.read_text())
    mapping = load_mapping()

    features = []
    matched_pcodes = set()

    for f in source["features"]:
        pcode = f["properties"]["ADM1_PCODE"]
        if pcode not in mapping:
            raise ValueError(
                f"geojson region {pcode} ({f['properties'].get('ADM1_EN')}) "
                f"has no entry in ph_region_mapping.csv - mapping is incomplete"
            )
        matched_pcodes.add(pcode)
        info = mapping[pcode]
        features.append({
            "type": "Feature",
            "properties": {
                "zone_id": info["short_label"],
                "psa_geolocation_name": info["psa_geolocation_name"],
                "adm1_pcode": pcode,
            },
            "geometry": f["geometry"],
        })

    # Catch the reverse gap too: a mapping entry with no matching geojson
    # feature would silently mean that region never renders - fail loudly
    # instead of shipping an incomplete map.
    unmatched = set(mapping.keys()) - matched_pcodes
    if unmatched:
        raise ValueError(f"Mapping entries with no matching geojson feature: {unmatched}")

    output = {"type": "FeatureCollection", "features": features}
    OUTPUT_PATH.write_text(json.dumps(output))

    print(f"Wrote {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size / 1024:.1f} KB)")
    print(f"Features: {len(features)} (expected 18)")
    assert len(features) == 18, f"expected exactly 18 regions, got {len(features)}"


if __name__ == "__main__":
    main()