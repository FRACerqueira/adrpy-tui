import pytest

from adrpy_tui.core.decisions import (
    ACCEPTED, INVALID, MIGRATED, PROPOSED, REJECTED, SUPERSEDED, labels, state,
)


def _decision(**header):
    return {"filename": "ADR001V01-x.md", "header": {"is_valid": True, "is_migrated": False, **header}}


@pytest.mark.parametrize("decision, expected", [
    (_decision(status_create="Proposed"), PROPOSED),
    (_decision(status_create="Proposed", status_update="Accepted"), ACCEPTED),
    (_decision(status_create="Proposed", status_update="Rejected"), REJECTED),
    (_decision(status_create="Proposed", status_update="Accepted", status_change="Superseded"), SUPERSEDED),
    (_decision(is_migrated=True), MIGRATED),
    (_decision(is_migrated=True, status_update="Accepted"), ACCEPTED),
    (_decision(is_valid=False, status_create="Proposed"), INVALID),
    ({"filename": "x.md", "header": None}, INVALID),
])
def test_state(decision, expected):
    assert state(decision) == expected


def test_folder_of_is_relative_to_the_decisions_folder(tmp_path):
    from adrpy_tui.core.decisions import folder_of

    root = tmp_path / "doc" / "adr"
    assert folder_of(root / "ADR001V01-x.md", root) == "."
    assert folder_of(root / "backend" / "data" / "ADR002V01-y.md", root) == "backend/data"
    assert folder_of(tmp_path / "elsewhere" / "ADR003V01-z.md", root) == "elsewhere"


def test_labels_come_from_the_repository_s_config():
    config = {"statusnew": "Proposto", "statusacc": "Aceito", "statusrej": "Rejeitado", "statussup": "Substituído",
              "headermigrated": "Migrado"}
    assert labels(config) == {PROPOSED: "Proposto", ACCEPTED: "Aceito", REJECTED: "Rejeitado",
                              SUPERSEDED: "Substituído", MIGRATED: "Migrado"}


def test_a_missing_label_falls_back_to_the_canonical_state():
    assert labels({})[PROPOSED] == PROPOSED


def test_explore_reports_canonical_states_whatever_the_labels(repo, client):
    """The finding behind ADR0001V01 rule 5, kept as a permanent test: a
    repository labelled in Portuguese still gets canonical states."""
    assert client.run("config", ("--path", str(repo), "--statusnew", "Proposto", "--statusacc", "Aceito")).success
    created = client.run("new", ("--path", str(repo), "--title", "Teste")).data["created"]
    assert client.run("approve", ("--file", created)).success
    [decision] = client.run("explore", ("--path", str(repo))).data["decisions"]
    assert state(decision) == ACCEPTED
