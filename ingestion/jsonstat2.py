"""
Decodes a JSON-stat 2.0 dataset (https://json-stat.org/) into flat records.

Why json-stat2 over PXWeb's plain "json" format: the plain format's exact
response envelope isn't consistently documented across PXWeb deployments
(Sweden, Finland, Norway all show slightly different examples online, and
none show PSA's specific shape). json-stat2 is an actual open standard with
a fixed, well-specified schema - safer to implement against a real spec
than to guess at an underdocumented one.

JSON-stat2 shape (the parts we need):
    dataset.dimension.id     -> list of dimension codes, IN THE ORDER used
                                 to flatten the value array (last dimension
                                 varies fastest - row-major / C-order)
    dataset.dimension.size   -> list of ints, size of each dimension, same
                                 order as `id`
    dataset.dimension[code].category.index -> {value_code: position}
    dataset.dimension[code].category.label -> {value_code: human label}
    dataset.value            -> flat array, length = product(size), values
                                 can be null (missing data)
"""


def decode_json_stat2(dataset: dict) -> list[dict]:
    dim_ids = dataset["dimension"]["id"]
    dim_sizes = dataset["dimension"]["size"]
    values = dataset["value"]

    # Invert each dimension's index map (code -> position) into an ordered
    # list (position -> code), so we can decode a flat index back into
    # per-dimension codes.
    position_to_code = []
    position_to_label = []
    for dim_code in dim_ids:
        dim_meta = dataset["dimension"][dim_code]["category"]
        index_map = dim_meta["index"]
        label_map = dim_meta.get("label", {})
        ordered_codes = [None] * len(index_map)
        for code, pos in index_map.items():
            ordered_codes[pos] = code
        position_to_code.append(ordered_codes)
        position_to_label.append([label_map.get(c, c) for c in ordered_codes])

    records = []
    for flat_index, value in enumerate(values):
        # Decode flat_index into per-dimension positions. Row-major with
        # the LAST dimension fastest-varying is the JSON-stat 2.0
        # convention - divmod chain from the last dimension backward.
        remaining = flat_index
        positions = [0] * len(dim_ids)
        for d in range(len(dim_ids) - 1, -1, -1):
            positions[d] = remaining % dim_sizes[d]
            remaining //= dim_sizes[d]

        record = {}
        for d, dim_code in enumerate(dim_ids):
            pos = positions[d]
            record[dim_code] = position_to_code[d][pos]
            record[f"{dim_code}_label"] = position_to_label[d][pos]
        record["value"] = value  # left as-is, including None - never silently dropped
        records.append(record)

    return records