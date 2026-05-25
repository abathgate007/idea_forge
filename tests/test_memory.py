import pytest

from idea_forge.database import initialize_database, open_database
from idea_forge.memory import create_memory, list_memories


def test_memory_record_can_be_created_and_listed() -> None:
    with open_database() as connection:
        initialize_database(connection)

        memory = create_memory(
            connection,
            memory_type="daily summary",
            title="Useful AppSec ideas",
            content="The strongest ideas had a narrow buyer and fast validation step.",
        )
        rows = list_memories(connection)

    assert memory.id == rows[0]["id"]
    assert rows[0]["memory_type"] == "daily summary"
    assert rows[0]["title"] == "Useful AppSec ideas"
    assert "narrow buyer" in rows[0]["content"]
    assert rows[0]["created_at"]


def test_memory_creation_requires_type_title_and_content() -> None:
    with open_database() as connection:
        initialize_database(connection)

        with pytest.raises(ValueError, match="Memory type is required."):
            create_memory(
                connection,
                memory_type=" ",
                title="A title",
                content="Some content",
            )

        with pytest.raises(ValueError, match="Memory title is required."):
            create_memory(
                connection,
                memory_type="daily summary",
                title=" ",
                content="Some content",
            )

        with pytest.raises(ValueError, match="Memory content is required."):
            create_memory(
                connection,
                memory_type="daily summary",
                title="A title",
                content=" ",
            )
