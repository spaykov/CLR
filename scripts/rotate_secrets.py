"""Generate fresh values for CLR_API_KEY and CLR_LOGIN_PASSWORD.

Usage:
    python scripts/rotate_secrets.py

Paste whichever value you're rotating into .env, then restart the server.
Both secrets are compared directly against the current .env value on every
request, and sessions are in-memory only, so a restart is all "rotation"
takes: the old value stops working immediately, and every existing browser
session is logged out along with it.
"""

import secrets

# A curated, unambiguous word list (lowercase, no look-alike characters) for
# building a memorable passphrase — same style as CLR_LOGIN_PASSWORD's
# original value. 200 words gives ~7.6 bits/word; four words plus a two-digit
# suffix is ~37 bits, comfortably strong against online guessing once rate
# limiting (5 attempts / 5 minutes on /auth/login) is in place.
_WORDS = sorted({
    "acorn", "amber", "anchor", "antler", "apple", "arrow", "ash", "aspen", "atlas", "aurora",
    "badge", "bamboo", "barley", "basil", "beacon", "beetle", "birch", "bison", "blaze", "bloom",
    "blossom", "boulder", "branch", "breeze", "bridge", "bronze", "brook", "bubble", "cabin", "cactus",
    "camel", "canyon", "cedar", "chalk", "channel", "charm", "cherry", "chestnut", "cinder", "clay",
    "cliff", "clover", "cobalt", "comet", "compass", "coral", "cotton", "cove", "coyote", "crane",
    "crater", "creek", "crest", "cricket", "crimson", "crow", "crystal", "current", "cypress", "daisy",
    "dawn", "delta", "desert", "dew", "diamond", "dune", "eagle", "ember", "emerald", "falcon",
    "feather", "fern", "field", "finch", "fjord", "flame", "flint", "forest", "fossil", "fox",
    "frost", "garden", "garnet", "gecko", "geyser", "glacier", "glade", "gorge", "granite", "gravel",
    "grove", "gull", "harbor", "hawk", "hazel", "heather", "hemlock", "heron", "hickory", "holly",
    "hollow", "honey", "horizon", "hyacinth", "ibis", "iris", "island", "ivory", "ivy", "jade",
    "jasmine", "jay", "jungle", "juniper", "kelp", "kestrel", "lagoon", "lantern", "larch", "lark",
    "laurel", "lichen", "lilac", "lily", "linden", "lizard", "lotus", "lynx", "magnolia", "mallow",
    "mango", "maple", "marble", "marigold", "marsh", "meadow", "mesa", "mist", "moss", "myrtle",
    "nectar", "nettle", "nutmeg", "oak", "oasis", "obsidian", "ocean", "olive", "onyx", "opal",
    "orchard", "orchid", "osprey", "otter", "owl", "palm", "pansy", "papaya", "pebble", "pelican",
    "pepper", "petal", "pigeon", "pine", "plateau", "plum", "poppy", "prairie", "primrose", "quail",
    "quarry", "quartz", "quill", "rain", "raven", "reed", "reef", "ridge", "river", "robin",
    "rose", "ruby", "sable", "saffron", "sage", "sail", "sand", "sapphire", "savanna", "sequoia",
    "shale", "shore", "sienna", "silver", "slate", "sorrel", "sparrow", "spring", "spruce", "storm",
    "sunset", "swallow", "sycamore", "tangerine", "teal", "thicket", "thistle", "thrush", "thyme", "tide",
    "timber", "topaz", "tulip", "tundra", "turquoise", "valley", "vine", "violet", "walnut", "willow",
})


def generate_api_key() -> str:
    """High-entropy token for scripts/curl (X-API-Key header)."""
    return secrets.token_urlsafe(32)


def generate_passphrase(word_count: int = 4) -> str:
    """Memorable passphrase for the browser login screen."""
    words = [secrets.choice(_WORDS) for _ in range(word_count)]
    suffix = f"{secrets.randbelow(100):02d}"
    return "-".join(words) + f"-{suffix}"


if __name__ == "__main__":
    print("New CLR_API_KEY (for scripts/curl):")
    print(f"  {generate_api_key()}")
    print()
    print("New CLR_LOGIN_PASSWORD (for the browser login screen):")
    print(f"  {generate_passphrase()}")
    print()
    print("Paste whichever one you're rotating into .env, then restart the server.")
