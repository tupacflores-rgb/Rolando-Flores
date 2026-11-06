"""Tests de la Entrega 1: memoria persistida (P4)."""

from app.memory import ConversationMemory


class FakeRepo:
    def __init__(self):
        self.saved = []

    def save_memory(self, note_id, kind, payload, created_at):
        self.saved.append((note_id, kind, payload, created_at))

    def restore_memory(self):
        return []


def test_memory_persists_when_repository_present():
    repo = FakeRepo()
    memory = ConversationMemory(repository=repo)
    assert memory.persistent is True
    memory.append("VIVO-1", "nota", {"text": "ok"})
    assert len(repo.saved) == 1
    assert repo.saved[0][0] == "VIVO-1"
    assert repo.saved[0][1] == "nota"


def test_memory_in_ram_without_repository():
    memory = ConversationMemory()
    assert memory.persistent is False
    memory.append("VIVO-1", "nota", {"text": "ok"})
    assert len(memory.get("VIVO-1")) == 1


def test_memory_restore_on_init():
    class RepoWithData(FakeRepo):
        def restore_memory(self):
            return [
                {"note_id": "VIVO-2", "kind": "borrador", "payload": {"filas": []}, "created_at": __import__("datetime").datetime.now(__import__("datetime").UTC)}
            ]

    memory = ConversationMemory(repository=RepoWithData())
    assert len(memory.get("VIVO-2")) == 1
