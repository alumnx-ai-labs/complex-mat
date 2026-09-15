import re

from app.models.user import User

# A token is a mention candidate when '@' is immediately followed by a letter,
# and an Azure DevOps reference candidate when immediately followed by a
# digit — this is the single disambiguation rule the BRD specifies (FR-028,
# FR-029). The negative lookbehind keeps an email address like
# "user@example.com" from being parsed as "@example".
MENTION_PATTERN = re.compile(r"(?<![\w@.])@([A-Za-z][A-Za-z0-9_]*)")
ADO_PATTERN = re.compile(r"(?<![\w@.])@(\d+)")


def find_mention_tokens(*texts: str | None) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for text in texts:
        if not text:
            continue
        for match in MENTION_PATTERN.finditer(text):
            name = match.group(1)
            key = name.lower()
            if key not in seen:
                seen.add(key)
                tokens.append(name)
    return tokens


def find_ado_ids(*texts: str | None) -> list[int]:
    ids: list[int] = []
    seen: set[int] = set()
    for text in texts:
        if not text:
            continue
        for match in ADO_PATTERN.finditer(text):
            ado_id = int(match.group(1))
            if ado_id not in seen:
                seen.add(ado_id)
                ids.append(ado_id)
    return ids


def resolve_mentions(candidates: list[str], attendees: list[User]) -> list[User]:
    """Resolves "@<letters>" tokens against a Meeting's Attendees by name.

    A candidate matches an Attendee if it equals any whitespace-separated
    word of their Employee Name (e.g. "@Sarah" -> "Sarah Iyer"), case
    insensitively.
    """
    resolved: list[User] = []
    seen_ids: set[int] = set()
    for name in candidates:
        lowered = name.lower()
        for attendee in attendees:
            words = attendee.employee_name.lower().split()
            if lowered in words and attendee.id not in seen_ids:
                seen_ids.add(attendee.id)
                resolved.append(attendee)
                break
    return resolved
