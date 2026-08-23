"""Unit tests for ROI / Occupancy / Dwell."""

from src.analytics.roi import point_in_polygon, ROIAnalytics
from src.vision.types import Track

def make_track(tid, cx, cy, cname="person", cid=0):
    return Track.from_values(tid, cid, cname, 0.9, cx-10, cy-10, cx+10, cy+10)

def test_point_in_polygon_inside():
    poly = [(0,0),(10,0),(10,10),(0,10)]
    assert point_in_polygon((5,5), poly) is True

def test_point_in_polygon_outside():
    poly = [(0,0),(10,0),(10,10),(0,10)]
    assert point_in_polygon((15,5), poly) is False
    assert point_in_polygon((5,-1), poly) is False

def test_point_on_edge_is_inside():
    poly = [(0,0),(10,0),(10,10),(0,10)]
    assert point_in_polygon((0,5), poly) is True
    assert point_in_polygon((5,0), poly) is True

def test_occupancy_counts():
    poly = [(0,0),(10,0),(10,10),(0,10)]
    roi = ROIAnalytics(polygon=poly, dwell_sec=2.0, fps=10)
    # frame0: 1 inside, 1 outside
    r = roi.update([make_track(1,5,5), make_track(2,15,5)], 0)
    assert r["occupancy"] == 1
    assert r["inside_ids"] == [1]
    assert r["max_occupancy"] == 1
    # frame1: both inside
    r = roi.update([make_track(1,5,5), make_track(2,5,5)], 1)
    assert r["occupancy"] == 2
    assert r["max_occupancy"] == 2
    # frame2: none inside
    r = roi.update([make_track(1,15,5)], 2)
    assert r["occupancy"] == 0
    assert r["max_occupancy"] == 2  # stays max

def test_dwell_threshold():
    poly = [(0,0),(10,0),(10,10),(0,10)]
    # dwell 2 sec at 10fps => 20 frames
    roi = ROIAnalytics(polygon=poly, dwell_sec=2.0, fps=10)
    # track stays inside for 19 frames -> no dwell
    for f in range(19):
        r = roi.update([make_track(1,5,5)], f)
        assert r["total_dwell"] == 0, f"frame {f}"
    # 20th frame should trigger
    r = roi.update([make_track(1,5,5)], 19)
    assert r["total_dwell"] == 1
    assert len(r["dwell_events"]) == 1
    ev = r["dwell_events"][0]
    assert ev.track_id == 1
    assert ev.duration_sec == 2.0
    # further frames should not re-trigger for same stay
    r = roi.update([make_track(1,5,5)], 20)
    assert r["total_dwell"] == 1  # still 1, not duplicate

def test_dwell_resets_on_exit():
    poly = [(0,0),(10,0),(10,10),(0,10)]
    roi = ROIAnalytics(polygon=poly, dwell_sec=1.0, fps=10)  # 10 frames
    for f in range(10):
        roi.update([make_track(1,5,5)], f)
    assert roi.get_events()[0].track_id == 1
    # exit
    roi.update([make_track(1,15,5)], 10)
    # re-enter and stay again
    for f in range(11,21):
        r = roi.update([make_track(1,5,5)], f)
    # second dwell should trigger after another 10 frames (frame 20)
    assert len(roi.get_events()) == 2
    assert roi.get_events()[1].enter_frame == 11

def test_classes_filter():
    poly = [(0,0),(10,0),(10,10),(0,10)]
    roi = ROIAnalytics(polygon=poly, dwell_sec=1.0, fps=10, classes=[0])
    # track cid 1 inside but filtered
    r = roi.update([make_track(1,5,5,cid=1)], 0)
    assert r["occupancy"] == 0
    # cid 0 inside counts
    r = roi.update([make_track(2,5,5,cid=0)], 1)
    assert r["occupancy"] == 1

def test_normalized_polygon():
    # normalized central 0.25-0.75 → 25,25 -75,75 on 100x100
    poly_norm = [(0.25,0.25),(0.75,0.25),(0.75,0.75),(0.25,0.75)]
    roi = ROIAnalytics(polygon=poly_norm, dwell_sec=1.0, fps=10)
    roi.set_frame_size(100,100)
    assert roi.polygon == ((25.0,25.0),(75.0,25.0),(75.0,75.0),(25.0,75.0))
    assert point_in_polygon((50,50), list(roi.polygon)) is True
    assert point_in_polygon((10,10), list(roi.polygon)) is False
    # occupancy with normalized
    r = roi.update([make_track(1,50,50)], 0)
    assert r["occupancy"] == 1

def test_occupancy_by_class():
    poly = [(0,0),(10,0),(10,10),(0,10)]
    roi = ROIAnalytics(polygon=poly, dwell_sec=2.0, fps=10)
    r = roi.update([make_track(1,5,5,cname="person"), make_track(2,5,5,cname="bus")], 0)
    assert r["by_class"] == {"person":1, "bus":1}
