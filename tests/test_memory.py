from memory import MemoryBuffer, compare_buffers


def test_memory_edits_undo_redo_and_find():
    buffer = MemoryBuffer(b"abcdef")
    buffer.edit(1, b"XY")
    assert bytes(buffer) == b"aXYdef"
    assert buffer.find(b"XY") == 1
    buffer.undo()
    assert bytes(buffer) == b"abcdef"
    buffer.redo()
    assert bytes(buffer) == b"aXYdef"


def test_compare_buffers_reports_missing_bytes():
    assert compare_buffers(b"ab", b"acx") == [(1, 98, 99), (2, None, 120)]
