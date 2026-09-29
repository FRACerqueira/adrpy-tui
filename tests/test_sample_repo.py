"""scripts/make_sample_repo.py: what it builds, and that --reset never
deletes a folder it did not build."""

import importlib.util
import pathlib
from pathlib import Path

import pytest

from adrpy_tui.core.decisions import ACCEPTED, PROPOSED, REJECTED, SUPERSEDED, state

_SPEC = importlib.util.spec_from_file_location(
    "make_sample_repo", Path(__file__).parent.parent / "scripts" / "make_sample_repo.py"
)
make_sample_repo = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(make_sample_repo)

# Built once for the whole module (each build is dozens of adrpy calls), so
# its tests run on one worker under pytest-xdist.
pytestmark = pytest.mark.xdist_group("sample_repo")
EXTRA = 9  # three of each state the extras take in turn


@pytest.fixture(scope="module")
def samples(tmp_path_factory):
    root = tmp_path_factory.mktemp("samples")
    make_sample_repo.build(root, language="pt-br", extra=EXTRA)
    return root


def _extras(decisions):
    return [decision for decision in decisions if decision["title"].startswith("decisao-de-exemplo")]


def test_the_sample_repository_has_a_decision_in_every_state(samples, client):
    decisions = client.run("explore", ("--path", str(samples / "sample"))).data["decisions"]
    states = [state(decision) for decision in decisions]
    assert {PROPOSED, ACCEPTED, REJECTED, SUPERSEDED} <= set(states)
    names = {decision["filename"] for decision in decisions}
    # Revisions are on from the first decision, so every name carries R01:
    # the revision `revise` wrote is R02, the version `version` wrote V02.
    assert any("R02" in name for name in names) and any("V02" in name for name in names)
    assert client.run("check", ("--path", str(samples / "sample"))).success
    assert any("backend" in pathlib.Path(decision["path"]).parent.name for decision in decisions)


def test_the_sample_repository_uses_the_chosen_language_s_labels(samples, client):
    config = client.run("config", ("--path", str(samples / "sample"))).data["config"]
    assert config["statusnew"] == "Proposto"


def test_the_sample_repository_has_decision_log_entries(samples):
    entries = [p for p in (samples / "sample" / "doc" / "decision-log").glob("*.md") if p.name != "INDEX.md"]
    assert len(entries) == 3


def test_the_legacy_repository_has_files_without_a_header(samples):
    folder = samples / "legacy" / "doc" / "adr"
    assert sorted(p.name for p in folder.glob("*.md")) == sorted(make_sample_repo.LEGACY_FILES)
    assert (samples / "legacy" / ".adrpy.json").is_file()


def test_the_broken_repository_is_refused_by_check(samples, client):
    result = client.run("check", ("--path", str(samples / "broken")))
    assert (result.success, result.code) == (False, "repository-inconsistent")
    assert "duplicate-number" in {error["code"] for error in result.data["errors"]}


def test_the_empty_folder_has_no_config(samples):
    assert (samples / "empty").is_dir() and not any((samples / "empty").iterdir())


def test_extra_adds_decisions_in_turn_proposed_accepted_and_rejected(samples, client):
    decisions = client.run("explore", ("--path", str(samples / "sample"))).data["decisions"]
    extras = sorted(_extras(decisions), key=lambda decision: decision["filename"])
    assert len(extras) == EXTRA
    assert [state(decision) for decision in extras] == [PROPOSED, ACCEPTED, REJECTED] * (EXTRA // 3)


def test_extra_cannot_be_negative(tmp_path):
    with pytest.raises(make_sample_repo.SampleError, match="--extra"):
        make_sample_repo.build(tmp_path, extra=-1)
    assert not any(tmp_path.iterdir())


def test_a_folder_that_is_not_empty_is_refused_without_reset(tmp_path):
    (tmp_path / "something.txt").write_text("mine", encoding="utf-8")
    with pytest.raises(make_sample_repo.SampleError, match="not empty"):
        make_sample_repo.build(tmp_path)
    assert (tmp_path / "something.txt").read_text(encoding="utf-8") == "mine"


def test_reset_refuses_a_folder_the_script_did_not_build(tmp_path):
    (tmp_path / "doc").mkdir()
    (tmp_path / "doc" / "real-work.md").write_text("mine", encoding="utf-8")
    with pytest.raises(make_sample_repo.SampleError, match="nothing was deleted"):
        make_sample_repo.build(tmp_path, reset=True)
    assert (tmp_path / "doc" / "real-work.md").read_text(encoding="utf-8") == "mine"


def test_reset_deletes_what_a_manual_test_left_and_builds_again(tmp_path, monkeypatch):
    """What reset deletes and that it builds again; what a build writes is
    the module fixture's tests' concern, so the builders are stubbed here."""
    built = []

    def stub(name):
        def builder(client, repo, *args):
            repo.mkdir(parents=True, exist_ok=True)
            (repo / "built.txt").write_text(name, encoding="utf-8")
            built.append(name)
        return builder

    monkeypatch.setattr(make_sample_repo, "build_sample", stub("sample"))
    monkeypatch.setattr(make_sample_repo, "build_legacy", stub("legacy"))
    monkeypatch.setattr(make_sample_repo, "build_broken", stub("broken"))
    monkeypatch.setattr(make_sample_repo, "add_extra", lambda client, repo, count: built.append(f"extra {count}"))

    make_sample_repo.build(tmp_path, client=object())
    (tmp_path / "sample" / "changed-by-hand.md").write_text("x", encoding="utf-8")
    (tmp_path / "leftover.txt").write_text("x", encoding="utf-8")

    make_sample_repo.build(tmp_path, reset=True, extra=4, client=object())
    assert not (tmp_path / "leftover.txt").exists()
    assert not (tmp_path / "sample" / "changed-by-hand.md").exists()
    assert (tmp_path / make_sample_repo.MARKER).is_file()
    assert built == ["sample", "extra 0", "legacy", "broken", "sample", "extra 4", "legacy", "broken"]
