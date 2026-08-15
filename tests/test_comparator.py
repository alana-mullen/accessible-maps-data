from accessible_maps.delta.comparator import compare_records
from accessible_maps.delta.models import TableDelta


def test_compare_records_detects_all_diff_types():
    base_records = [
        {"fid": 1, "name": "Main St Kerb", "kerb": "lowered", "geometry": "POINT(0 0)"},
        {"fid": 2, "name": "High St Kerb", "kerb": "raised", "geometry": "POINT(1 1)"},
        {"fid": 3, "name": "Old Crossing", "crossing": "uncontrolled", "geometry": "POINT(2 2)"},
    ]

    target_records = [
        # fid 1 is unchanged
        {"fid": 1, "name": "Main St Kerb", "kerb": "lowered", "geometry": "POINT(0 0)"},
        # fid 2 has updated attribute
        {"fid": 2, "name": "High St Kerb", "kerb": "flush", "geometry": "POINT(1 1)"},
        # fid 3 is deleted (omitted from target)
        # fid 4 is inserted
        {"fid": 4, "name": "New Footway", "highway": "footway", "geometry": "LINESTRING(0 0, 1 1)"},
    ]

    delta = compare_records(
        "accessibility_features", base_records, target_records, primary_key="fid"
    )

    assert delta.table_name == "accessibility_features"
    assert delta.insert_count == 1
    assert delta.update_count == 1
    assert delta.delete_count == 1
    assert delta.total_target_rows == 3

    assert delta.inserts[0]["fid"] == 4
    assert delta.updates[0]["fid"] == 2
    assert delta.updates[0]["kerb"] == "flush"
    assert delta.deletes == [3]


def test_compare_records_empty_base():
    target = [{"fid": 1, "name": "A"}]
    delta = compare_records("tbl", [], target, primary_key="fid")
    assert delta.insert_count == 1
    assert delta.update_count == 0
    assert delta.delete_count == 0


def test_compare_records_empty_target():
    base = [{"fid": 1, "name": "A"}]
    delta = compare_records("tbl", base, [], primary_key="fid")
    assert delta.insert_count == 0
    assert delta.update_count == 0
    assert delta.delete_count == 1
    assert delta.deletes == [1]


def test_table_delta_json_roundtrip():
    delta = TableDelta(
        table_name="kerbs",
        primary_key="fid",
        inserts=[{"fid": 1, "type": "lowered"}],
        updates=[{"fid": 2, "type": "flush"}],
        deletes=[3, 4],
        total_target_rows=2,
    )

    json_str = delta.to_json()
    reloaded = TableDelta.from_json(json_str)

    assert reloaded.table_name == delta.table_name
    assert reloaded.inserts == delta.inserts
    assert reloaded.updates == delta.updates
    assert reloaded.deletes == delta.deletes
    assert reloaded.total_target_rows == delta.total_target_rows
