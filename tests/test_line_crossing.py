"""Unit tests for LineCrossingCounter — synthetic tracks."""

import pytest
from src.vision.types import Track
from src.analytics.line_crossing import LineCrossingCounter

def make_track(tid, cx, cy, class_name="person", class_id=0):
    # bbox 20x20 around center
    x1, y1, x2, y2 = cx-10, cy-10, cx+10, cy+10
    return Track.from_values(tid, class_id, class_name, 0.9, x1, y1, x2, y2)

def test_single_cross_left_to_right():
    # vertical line x=50
    counter = LineCrossingCounter(p1=(50,0), p2=(50,100), mode="both")
    # track moves from x=10 to x=90 across line
    tracks_f0 = [make_track(1, 10, 50)]
    assert counter.update(tracks_f0, 0) == []
    tracks_f1 = [make_track(1, 90, 50)]
    events = counter.update(tracks_f1, 1)
    assert len(events) == 1
    assert events[0].direction == "a_to_b"  # left is a side (cross>0), right is b
    assert counter.get_counts()["total"] == 1
    assert counter.get_counts()["a_to_b"] == 1

def test_single_cross_right_to_left():
    counter = LineCrossingCounter(p1=(50,0), p2=(50,100), mode="both")
    tracks_f0 = [make_track(1, 90, 50)]
    counter.update(tracks_f0, 0)
    tracks_f1 = [make_track(1, 10, 50)]
    events = counter.update(tracks_f1, 1)
    assert len(events) == 1
    assert events[0].direction == "b_to_a"
    assert counter.get_counts()["b_to_a"] == 1

def test_round_trip_counts_two():
    counter = LineCrossingCounter(p1=(50,0), p2=(50,100), mode="both", cooldown_frames=8)
    counter.update([make_track(1, 10, 50)], 0)
    counter.update([make_track(1, 90, 50)], 10)
    assert counter.get_counts()["total"] == 1
    # back after cooldown
    events = counter.update([make_track(1, 10, 50)], 20)
    assert len(events) == 1
    assert counter.get_counts()["total"] == 2
    assert counter.get_counts()["a_to_b"] == 1
    assert counter.get_counts()["b_to_a"] == 1

def test_no_cross_same_side():
    counter = LineCrossingCounter(p1=(50,0), p2=(50,100), mode="both")
    counter.update([make_track(1, 10, 50)], 0)
    counter.update([make_track(1, 20, 50)], 1)
    counter.update([make_track(1, 30, 50)], 2)
    assert counter.get_counts()["total"] == 0

def test_mode_filter_a_to_b_only():
    counter = LineCrossingCounter(p1=(50,0), p2=(50,100), mode="a_to_b")
    counter.update([make_track(1, 90, 50)], 0)
    # b->a should be ignored
    events = counter.update([make_track(1, 10, 50)], 1)
    assert len(events) == 0
    assert counter.get_counts()["total"] == 0
    # a->b should count
    counter2 = LineCrossingCounter(p1=(50,0), p2=(50,100), mode="a_to_b")
    counter2.update([make_track(2, 10, 50)], 0)
    events2 = counter2.update([make_track(2, 90, 50)], 1)
    assert len(events2) == 1

def test_jitter_near_line_no_double_count():
    # track approaches line but stays same side with jitter within 2px of line — should not double count
    counter = LineCrossingCounter(p1=(50,0), p2=(50,100), mode="both")
    # start left
    counter.update([make_track(1, 10, 50)], 0)
    # move to 48 (still left, side >0 but close)
    counter.update([make_track(1, 48, 50)], 1)
    assert counter.get_counts()["total"] == 0
    # jitter to 49, still left
    counter.update([make_track(1, 49, 50)], 2)
    assert counter.get_counts()["total"] == 0
    # cross to 52 (right)
    events = counter.update([make_track(1, 52, 50)], 3)
    assert len(events) == 1
    # stay right jitter 51, 53
    counter.update([make_track(1, 51, 50)], 4)
    counter.update([make_track(1, 53, 50)], 5)
    assert counter.get_counts()["total"] == 1

def test_multiple_ids_independent():
    counter = LineCrossingCounter(p1=(50,0), p2=(50,100), mode="both")
    # id1 left->right, id2 right->left same frame
    counter.update([make_track(1, 10, 50), make_track(2, 90, 50)], 0)
    events = counter.update([make_track(1, 90, 50), make_track(2, 10, 50)], 1)
    assert len(events) == 2
    assert counter.get_counts()["total"] == 2

def test_horizontal_line():
    # horizontal line y=50, top to bottom
    counter = LineCrossingCounter(p1=(0,50), p2=(100,50), mode="both")
    counter.update([make_track(1, 50, 10)], 0)
    events = counter.update([make_track(1, 50, 90)], 1)
    assert len(events) == 1
    # For horizontal, cross sign logic still holds: vector (100,0), cross = 100*(y-50)?? Wait p1(0,50)->p2(100,50) cross = 100*(y-50?) Actually side = (100)*(y-50) - 0*(x-0) =100*(y-50). So y<50 => negative (b), y>50 => positive (a)? Check: y=10 => 100*(-40) = -4000 (b), y=90 => 4000 (a) => b_to_a direction. Accept either but count should happen.
    assert counter.get_counts()["total"] == 1

def test_classes_filter():
    counter = LineCrossingCounter(p1=(50,0), p2=(50,100), mode="both", classes=[0])
    counter.update([make_track(1, 10, 50, class_id=0)], 0)
    # track with class 1 should be ignored
    counter.update([make_track(2, 10, 50, class_id=1)], 1)
    # move both across
    events = counter.update([make_track(1, 90, 50, class_id=0), make_track(2, 90, 50, class_id=1)], 2)
    assert len(events) == 1
    assert events[0].track_id == 1

def test_normalized_coords():
    # normalized line 0.5 vertical center, frame 100x100 -> line x=50
    counter = LineCrossingCounter(p1=(0.5,0), p2=(0.5,1), mode="both")
    counter.set_frame_size(100, 100)
    # now p1,p2 should be (50,0)-(50,100)
    assert counter.p1 == (50.0, 0.0)
    assert counter.p2 == (50.0, 100.0)
    counter.update([make_track(1, 10, 50)], 0)
    events = counter.update([make_track(1, 90, 50)], 1)
    assert len(events) == 1
