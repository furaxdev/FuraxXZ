import json
import zipfile

import pytest
from furaxxz import lab


@pytest.fixture
def source_tree(tmp_path):
    src = tmp_path / "source"
    (src / "system" / "fonts").mkdir(parents=True)
    (src / "system" / "fonts" / "Roboto.ttf").write_bytes(b"original-font-bytes")
    (src / "system" / "build.prop").write_text("ro.build.version=1\n")
    return src


@pytest.fixture
def lab_root(tmp_path):
    return tmp_path / "lab"


def test_init_session_snapshots_and_hashes(source_tree, lab_root):
    session = lab.init_session(lab_root, source_tree, "s1")

    assert session.original_tree.is_dir()
    assert (session.original_tree / "system" / "fonts" / "Roboto.ttf").read_bytes() == b"original-font-bytes"
    assert session.original_checksums.is_file()
    assert session.modified_tree.is_dir()
    assert (session.modified_tree / "system" / "fonts" / "Roboto.ttf").read_bytes() == b"original-font-bytes"
    assert session.load_operations() == []


def test_init_session_missing_source_raises(lab_root, tmp_path):
    with pytest.raises(lab.LabError):
        lab.init_session(lab_root, tmp_path / "does-not-exist", "s1")


def test_init_session_refuses_to_overwrite_existing(source_tree, lab_root):
    lab.init_session(lab_root, source_tree, "s1")
    with pytest.raises(lab.LabError):
        lab.init_session(lab_root, source_tree, "s1")


def test_apply_replace_updates_file_and_records_operation(source_tree, lab_root, tmp_path):
    session = lab.init_session(lab_root, source_tree, "s1")
    new_font = tmp_path / "new-font.ttf"
    new_font.write_bytes(b"replacement-font-bytes")

    result = lab.apply_operation(session, "replace", "system/fonts/Roboto.ttf", new_font)

    assert result.sha256_before is not None
    assert result.sha256_after is not None
    assert result.sha256_before != result.sha256_after
    modified_font = session.modified_tree / "system" / "fonts" / "Roboto.ttf"
    assert modified_font.read_bytes() == b"replacement-font-bytes"
    # original snapshot must be untouched
    original_font = session.original_tree / "system" / "fonts" / "Roboto.ttf"
    assert original_font.read_bytes() == b"original-font-bytes"

    ops = session.load_operations()
    assert len(ops) == 1
    assert ops[0]["type"] == "replace"
    assert ops[0]["relPath"] == "system/fonts/Roboto.ttf"


def test_apply_add_creates_new_file(source_tree, lab_root, tmp_path):
    session = lab.init_session(lab_root, source_tree, "s1")
    new_file = tmp_path / "extra.txt"
    new_file.write_text("hello")

    lab.apply_operation(session, "add", "system/extra.txt", new_file)

    assert (session.modified_tree / "system" / "extra.txt").read_text() == "hello"


def test_apply_add_existing_file_raises(source_tree, lab_root, tmp_path):
    session = lab.init_session(lab_root, source_tree, "s1")
    new_file = tmp_path / "extra.txt"
    new_file.write_text("hello")
    with pytest.raises(lab.LabError):
        lab.apply_operation(session, "add", "system/build.prop", new_file)


def test_apply_remove_deletes_file(source_tree, lab_root):
    session = lab.init_session(lab_root, source_tree, "s1")
    lab.apply_operation(session, "remove", "system/build.prop")
    assert not (session.modified_tree / "system" / "build.prop").exists()


def test_apply_remove_missing_file_raises(source_tree, lab_root):
    session = lab.init_session(lab_root, source_tree, "s1")
    with pytest.raises(lab.LabError):
        lab.apply_operation(session, "remove", "system/does-not-exist.txt")


def test_apply_replace_missing_target_raises(source_tree, lab_root, tmp_path):
    session = lab.init_session(lab_root, source_tree, "s1")
    new_file = tmp_path / "x.ttf"
    new_file.write_bytes(b"x")
    with pytest.raises(lab.LabError):
        lab.apply_operation(session, "replace", "system/does-not-exist.ttf", new_file)


def test_apply_rejects_path_traversal(source_tree, lab_root, tmp_path):
    session = lab.init_session(lab_root, source_tree, "s1")
    evil = tmp_path / "evil.ttf"
    evil.write_bytes(b"evil")
    with pytest.raises(lab.LabError):
        lab.apply_operation(session, "add", "../../../etc/evil.ttf", evil)


def test_apply_rejects_absolute_path(source_tree, lab_root, tmp_path):
    session = lab.init_session(lab_root, source_tree, "s1")
    evil = tmp_path / "evil.ttf"
    evil.write_bytes(b"evil")
    with pytest.raises(lab.LabError):
        lab.apply_operation(session, "add", "/etc/evil.ttf", evil)


def test_apply_on_nonexistent_session_raises(lab_root):
    session = lab.LabSession(session_id="ghost", lab_root=lab_root)
    with pytest.raises(lab.LabError):
        lab.apply_operation(session, "remove", "system/build.prop")


def test_build_produces_zip_and_report(source_tree, lab_root, tmp_path):
    session = lab.init_session(lab_root, source_tree, "s1")
    new_font = tmp_path / "new-font.ttf"
    new_font.write_bytes(b"replacement-font-bytes")
    lab.apply_operation(session, "replace", "system/fonts/Roboto.ttf", new_font)

    report = lab.build_session(session)

    assert report["status"] == "EXPERIMENTAL"
    assert report["flashable"] is False
    assert report["fileCount"] == 2
    assert len(report["operations"]) == 1

    archive_path = session.rebuilt_dir / "s1.zip"
    assert archive_path.is_file()
    with zipfile.ZipFile(archive_path) as zf:
        names = set(zf.namelist())
        assert "system/fonts/Roboto.ttf" in names
        assert zf.read("system/fonts/Roboto.ttf") == b"replacement-font-bytes"

    report_path = session.report_dir / "report.json"
    assert report_path.is_file()
    assert json.loads(report_path.read_text())["flashable"] is False


def test_build_missing_session_raises(lab_root):
    session = lab.LabSession(session_id="ghost", lab_root=lab_root)
    with pytest.raises(lab.LabError):
        lab.build_session(session)


def test_verify_passes_for_untouched_session(source_tree, lab_root, tmp_path):
    session = lab.init_session(lab_root, source_tree, "s1")
    new_font = tmp_path / "new-font.ttf"
    new_font.write_bytes(b"replacement-font-bytes")
    lab.apply_operation(session, "replace", "system/fonts/Roboto.ttf", new_font)

    result = lab.verify_session(session, tmp_path / "work")

    assert result.ok
    assert result.original_intact
    assert result.reproducible
    assert result.original_mismatches == []
    assert result.reproduction_mismatches == []


def test_verify_detects_tampered_original(source_tree, lab_root, tmp_path):
    session = lab.init_session(lab_root, source_tree, "s1")
    # Tamper with the supposedly-immutable original snapshot.
    (session.original_tree / "system" / "build.prop").write_text("tampered!\n")

    result = lab.verify_session(session, tmp_path / "work")

    assert not result.original_intact
    assert "system/build.prop" in result.original_mismatches
    assert not result.ok


def test_verify_detects_unreproducible_modification(source_tree, lab_root, tmp_path):
    session = lab.init_session(lab_root, source_tree, "s1")
    new_font = tmp_path / "new-font.ttf"
    new_font.write_bytes(b"replacement-font-bytes")
    lab.apply_operation(session, "replace", "system/fonts/Roboto.ttf", new_font)

    # Hand-edit the modified tree without recording an operation for it —
    # operations.json no longer describes what's actually in modified/.
    (session.modified_tree / "system" / "build.prop").write_text("undocumented change\n")

    result = lab.verify_session(session, tmp_path / "work")

    assert result.original_intact
    assert not result.reproducible
    assert "system/build.prop" in result.reproduction_mismatches
    assert not result.ok


def test_verify_missing_session_raises(lab_root, tmp_path):
    session = lab.LabSession(session_id="ghost", lab_root=lab_root)
    with pytest.raises(lab.LabError):
        lab.verify_session(session, tmp_path / "work")


def test_full_pipeline_multiple_operations(source_tree, lab_root, tmp_path):
    session = lab.init_session(lab_root, source_tree, "pipeline")

    new_font = tmp_path / "new-font.ttf"
    new_font.write_bytes(b"new-font")
    extra = tmp_path / "extra.txt"
    extra.write_text("extra")

    lab.apply_operation(session, "replace", "system/fonts/Roboto.ttf", new_font)
    lab.apply_operation(session, "add", "system/extra.txt", extra)
    lab.apply_operation(session, "remove", "system/build.prop")

    assert len(session.load_operations()) == 3

    verify = lab.verify_session(session, tmp_path / "work")
    assert verify.ok

    report = lab.build_session(session)
    assert report["fileCount"] == 2  # Roboto.ttf (replaced) + extra.txt; build.prop removed
    assert len(report["operations"]) == 3
