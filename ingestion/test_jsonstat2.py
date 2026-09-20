from jsonstat2 import decode_json_stat2

# Synthetic 2-dimension dataset: Geolocation (2 values) x Year (2 values).
# Flat value array is row-major with the LAST dimension (Year) fastest-
# varying, so the order is: (PHL,2018), (PHL,2019), (NCR,2018), (NCR,2019).
FIXTURE = {
    "dimension": {
        "id": ["Geolocation", "Year"],
        "size": [2, 2],
        "Geolocation": {
            "category": {
                "index": {"0": 0, "1": 1},
                "label": {"0": "PHILIPPINES", "1": "National Capital Region (NCR)"},
            }
        },
        "Year": {
            "category": {
                "index": {"0": 0, "1": 1},
                "label": {"0": "2018", "1": "2019"},
            }
        },
    },
    "value": [100.5, 102.3, None, 105.1],  # PHL/2019 is deliberately missing
}


def test_decode_produces_correct_row_count_and_order():
    records = decode_json_stat2(FIXTURE)
    assert len(records) == 4


def test_decode_maps_codes_and_labels_correctly():
    records = decode_json_stat2(FIXTURE)
    first = records[0]
    assert first["Geolocation"] == "0"
    assert first["Geolocation_label"] == "PHILIPPINES"
    assert first["Year"] == "0"
    assert first["Year_label"] == "2018"
    assert first["value"] == 100.5


def test_decode_preserves_null_value_without_dropping_row():
    """
    The exact scenario that would break a naive parser: a null in the
    middle of the flat array must still produce a row (position
    NCR/2018), not shift every subsequent value's alignment.
    """
    records = decode_json_stat2(FIXTURE)
    ncr_2018 = records[2]
    assert ncr_2018["Geolocation_label"] == "National Capital Region (NCR)"
    assert ncr_2018["Year_label"] == "2018"
    assert ncr_2018["value"] is None

    # and the row AFTER the null must still be correctly aligned, not
    # shifted - this is what would break if null handling were wrong
    ncr_2019 = records[3]
    assert ncr_2019["Year_label"] == "2019"
    assert ncr_2019["value"] == 105.1


if __name__ == "__main__":
    test_decode_produces_correct_row_count_and_order()
    test_decode_maps_codes_and_labels_correctly()
    test_decode_preserves_null_value_without_dropping_row()
    print("PASSED: 3/3 json-stat2 decoder tests")