"""Texts residents receive. Honest by design: nothing promises help before a team is assigned."""

ACKNOWLEDGED = (
    "Natanggap po namin ang mensahe ninyo. HINDI pa ito kumpirmasyon na may parating na "
    "tulong; ia-update namin kayo. (Received. This is NOT yet confirmation that help is coming.)"
)
LOCATION_RECEIVED = (
    "Salamat po, natanggap namin ang lokasyon ninyo. (Thank you, we have your location.)"
)


def team_assigned(team: str) -> str:
    return (
        f"May rescue team na po papunta sa inyo ({team}). Manatili po sa ligtas na lugar. "
        f"(A rescue team is on the way: {team}. Please stay somewhere safe.)"
    )
