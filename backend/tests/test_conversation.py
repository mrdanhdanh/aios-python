"""Conversation memory tests."""

import pytest

from aios_core.memory import ConversationMemory


@pytest.fixture
def mem(tmp_path):
    return ConversationMemory(db_path=str(tmp_path / "conv.db"))


def test_create_and_add_message(mem):
    cid = mem.create_conversation("s1")
    mid = mem.add_message(cid, "user", "hello")
    assert mid
    messages = mem.get_messages(cid)
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "hello"


def test_role_invalid_raises(mem):
    cid = mem.create_conversation("s1")
    with pytest.raises(ValueError, match="role"):
        mem.add_message(cid, "assistan", "x")  # typo


def test_unknown_conversation_raises(mem):
    with pytest.raises(ValueError, match="unknown conversation"):
        mem.add_message("nope", "user", "x")


def test_limit_returns_newest_ascending(mem):
    cid = mem.create_conversation("s1")
    for i in range(5):
        mem.add_message(cid, "user", f"msg-{i}")
    limited = mem.get_messages(cid, limit=2)
    assert [m["content"] for m in limited] == ["msg-3", "msg-4"]  # newest 2, ascending
    # limit > count → all
    assert len(mem.get_messages(cid, limit=100)) == 5


def test_ordering_preserved(mem):
    cid = mem.create_conversation("s1")
    mem.add_message(cid, "user", "first")
    mem.add_message(cid, "assistant", "second")
    messages = mem.get_messages(cid)
    assert [m["content"] for m in messages] == ["first", "second"]


def test_list_conversations(mem):
    c1 = mem.create_conversation("s1")
    c2 = mem.create_conversation("s1")
    mem.create_conversation("s2")
    assert set(mem.list_conversations("s1")) == {c1, c2}


def test_db_auto_created(tmp_path):
    mem = ConversationMemory(db_path=str(tmp_path / "nested" / "conv.db"))
    cid = mem.create_conversation("s")
    assert mem.get_messages(cid) == []


def test_ids_unique(mem):
    cid = mem.create_conversation("s")
    ids = {mem.add_message(cid, "user", f"m{i}") for i in range(10)}
    assert len(ids) == 10
