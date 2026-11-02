"""Texts residents receive. Honest by design: nothing promises help before a team is assigned."""

ACKNOWLEDGED = (
    "Natanggap po namin ang mensahe ninyo. HINDI pa ito kumpirmasyon na may parating na "
    "tulong; ia-update namin kayo. (Received. This is NOT yet confirmation that help is coming.)"
)
WELCOME = (
    "Saklolo po ito. I-text ang sitwasyon: nasaan kayo (barangay, landmark), ilan kayo, at "
    "kung may bata, senior, o may sakit. Kung nasa agarang panganib, tumawag din sa 911. "
    "(This is Saklolo. Tell us where you are, how many you are, and who needs care. "
    "In immediate danger, also call 911.)"
)
LOCATION_RECEIVED = (
    "Salamat po, natanggap namin ang lokasyon ninyo. (Thank you, we have your location.)"
)


def team_assigned(team: str) -> str:
    return (
        f"May rescue team na po papunta sa inyo ({team}). Manatili po sa ligtas na lugar. "
        f"(A rescue team is on the way: {team}. Please stay somewhere safe.)"
    )
