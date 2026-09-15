from app.models.user import Role, User
from app.services.mention_parser import find_ado_ids, find_mention_tokens, resolve_mentions


def _user(user_id: int, employee_name: str) -> User:
    return User(
        id=user_id,
        employee_name=employee_name,
        employee_mail_id=f"user{user_id}@example.com",
        employee_id=f"E{user_id}",
        password_hash="hashed",
        role=Role.TEAM_MEMBER,
        is_active=True,
    )


# ---------- find_mention_tokens ----------


def test_find_mention_tokens_extracts_letter_tokens():
    assert find_mention_tokens("Can @Sarah confirm this lines up with @Priya?") == [
        "Sarah",
        "Priya",
    ]


def test_find_mention_tokens_ignores_digit_tokens():
    assert find_mention_tokens("Related to @1234") == []


def test_find_mention_tokens_deduplicates_case_insensitively():
    assert find_mention_tokens("@Sarah can you loop in @sarah again?") == ["Sarah"]


def test_find_mention_tokens_ignores_email_addresses():
    assert find_mention_tokens("Reach me at user@example.com for details") == []


def test_find_mention_tokens_scans_multiple_texts():
    assert find_mention_tokens("Title mentions @John", None, "Body mentions @Priya") == [
        "John",
        "Priya",
    ]


def test_find_mention_tokens_handles_none_and_empty_text():
    assert find_mention_tokens(None, "", "no mentions here") == []


# ---------- find_ado_ids ----------


def test_find_ado_ids_extracts_digit_tokens():
    assert find_ado_ids("Can @Sarah confirm this lines up with @1234?") == [1234]


def test_find_ado_ids_ignores_letter_tokens():
    assert find_ado_ids("@Sarah please check") == []


def test_find_ado_ids_deduplicates_repeated_ids():
    assert find_ado_ids("See @1234 and again @1234") == [1234]


def test_find_ado_ids_preserves_first_seen_order_across_multiple_ids():
    assert find_ado_ids("Related to @42 and also @7") == [42, 7]


def test_find_ado_ids_scans_multiple_texts():
    assert find_ado_ids("Title @1", None, "Body @2") == [1, 2]


# ---------- resolve_mentions ----------


def test_resolve_mentions_matches_first_name_case_insensitively():
    sarah = _user(7, "Sarah Iyer")
    resolved = resolve_mentions(["sarah"], [sarah])
    assert resolved == [sarah]


def test_resolve_mentions_ignores_unmatched_candidates():
    sarah = _user(7, "Sarah Iyer")
    assert resolve_mentions(["Priya"], [sarah]) == []


def test_resolve_mentions_is_scoped_to_the_given_attendee_list():
    sarah = _user(7, "Sarah Iyer")
    outsider = _user(8, "Priya Nair")
    # outsider is a valid name but not passed in as an attendee candidate
    assert resolve_mentions(["Priya"], [sarah]) == []
    assert resolve_mentions(["Priya"], [sarah, outsider]) == [outsider]


def test_resolve_mentions_deduplicates_the_same_user_across_tokens():
    sarah = _user(7, "Sarah Iyer")
    resolved = resolve_mentions(["Sarah", "Iyer"], [sarah])
    assert resolved == [sarah]


def test_resolve_mentions_preserves_candidate_order():
    sarah = _user(7, "Sarah Iyer")
    john = _user(3, "John Owner")
    resolved = resolve_mentions(["John", "Sarah"], [sarah, john])
    assert [user.id for user in resolved] == [john.id, sarah.id]
