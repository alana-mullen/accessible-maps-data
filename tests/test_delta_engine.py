from accessible_maps.delta.engine import apply_table_delta
from accessible_maps.delta.models import TableDelta


def test_apply_table_delta():
    base_records = [
        {"fid": 1, "name": "Feature 1", "status": "active"},
        {"fid": 2, "name": "Feature 2", "status": "active"},
        {"fid": 3, "name": "Feature 3", "status": "active"},
    ]

    table_delta = TableDelta(
        table_name="features",
        primary_key="fid",
        inserts=[
            {"fid": 4, "name": "Feature 4", "status": "new"},
        ],
        updates=[
            {"fid": 2, "name": "Feature 2 Modified", "status": "inactive"},
        ],
        deletes=[1],
    )

    reconstructed = apply_table_delta(base_records, table_delta)
    reconstructed_map = {r["fid"]: r for r in reconstructed}

    assert 1 not in reconstructed_map  # deleted
    assert reconstructed_map[2]["name"] == "Feature 2 Modified"  # updated
    assert reconstructed_map[2]["status"] == "inactive"
    assert reconstructed_map[3]["name"] == "Feature 3"  # unchanged
    assert reconstructed_map[4]["name"] == "Feature 4"  # inserted
    assert reconstructed_map[4]["status"] == "new"
