import pytest

from idea_forge.database import initialize_database, open_database
from idea_forge.feedback import record_feedback
from idea_forge.search import IdeaSearchFilters, search_ideas


def reference_id(connection, table_name: str, name: str) -> int:
    return connection.execute(
        f"SELECT id FROM {table_name} WHERE name = ?",
        (name,),
    ).fetchone()["id"]


def insert_idea(
    connection,
    *,
    title: str,
    summary: str,
    portfolio_id: int | None = None,
    idea_agent_id: int | None = None,
    creative_technique_id: int | None = None,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO ideas (
            title,
            summary,
            body,
            portfolio_id,
            idea_agent_id,
            creative_technique_id
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            title,
            summary,
            summary,
            portfolio_id,
            idea_agent_id,
            creative_technique_id,
        ),
    )
    connection.commit()
    return int(cursor.lastrowid)


def test_keyword_search_matches_stored_idea_fields() -> None:
    with open_database() as connection:
        initialize_database(connection)
        insert_idea(
            connection,
            title="AppSec workshop wedge",
            summary="Sell a focused threat modeling workshop.",
        )
        insert_idea(
            connection,
            title="Real estate listing checklist",
            summary="A neighborhood listing prep workflow.",
        )

        results = search_ideas(connection, IdeaSearchFilters(query="threat modeling"))

    assert [row["title"] for row in results] == ["AppSec workshop wedge"]


def test_search_filters_by_portfolio_agent_and_technique() -> None:
    with open_database() as connection:
        initialize_database(connection)
        appsec_portfolio_id = reference_id(connection, "portfolios", "Cybersecurity and AppSec")
        writing_portfolio_id = reference_id(connection, "portfolios", "Writing and content")
        operator_id = reference_id(connection, "idea_agents", "Money-Hungry Operator")
        vc_id = reference_id(connection, "idea_agents", "Seasoned VC")
        tiny_wedge_id = reference_id(connection, "creative_techniques", "Tiny Wedge")
        inversion_id = reference_id(connection, "creative_techniques", "Inversion")
        insert_idea(
            connection,
            title="Matching idea",
            summary="Matches every selected metadata filter.",
            portfolio_id=appsec_portfolio_id,
            idea_agent_id=operator_id,
            creative_technique_id=tiny_wedge_id,
        )
        insert_idea(
            connection,
            title="Wrong metadata idea",
            summary="Should be filtered out.",
            portfolio_id=writing_portfolio_id,
            idea_agent_id=vc_id,
            creative_technique_id=inversion_id,
        )

        results = search_ideas(
            connection,
            IdeaSearchFilters(
                portfolio_id=appsec_portfolio_id,
                idea_agent_id=operator_id,
                creative_technique_id=tiny_wedge_id,
            ),
        )

    assert [row["title"] for row in results] == ["Matching idea"]


def test_search_filters_by_feedback_action() -> None:
    with open_database() as connection:
        initialize_database(connection)
        starred_id = insert_idea(
            connection,
            title="Starred idea",
            summary="A useful stored idea.",
        )
        insert_idea(
            connection,
            title="Unstarred idea",
            summary="Another stored idea.",
        )
        record_feedback(connection, idea_id=starred_id, action="star")

        results = search_ideas(
            connection,
            IdeaSearchFilters(feedback_action="star"),
        )

    assert [row["title"] for row in results] == ["Starred idea"]


def test_search_rejects_invalid_feedback_action_filter() -> None:
    with open_database() as connection:
        initialize_database(connection)

        with pytest.raises(
            ValueError,
            match="Unsupported feedback action filter: save_forever",
        ):
            search_ideas(
                connection,
                IdeaSearchFilters(feedback_action="save_forever"),
            )
