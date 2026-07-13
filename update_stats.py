"""
Auto-updates LeetCode and GFG solve counts in README.md.
Runs via GitHub Actions daily. Patches two badge URLs and the
Mission Targets table row in-place so nothing else changes.
"""

import re
import requests

# ── CONFIG ────────────────────────────────────────────────────────────────────
LEETCODE_USERNAME = "Snehal_Garg"
GFG_USERNAME      = "snehalgeh4e"
README_PATH       = "README.md"
# ─────────────────────────────────────────────────────────────────────────────


def fetch_leetcode_solved(username: str) -> int | None:
    """
    Hits LeetCode's public GraphQL endpoint — no auth needed.
    Returns total problems solved or None on failure.
    """
    url = "https://leetcode.com/graphql"
    query = """
    query getUserProfile($username: String!) {
      matchedUser(username: $username) {
        submitStats {
          acSubmissionNum {
            difficulty
            count
          }
        }
      }
    }
    """
    try:
        resp = requests.post(
            url,
            json={"query": query, "variables": {"username": username}},
            headers={"Content-Type": "application/json", "Referer": "https://leetcode.com"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        stats = data["data"]["matchedUser"]["submitStats"]["acSubmissionNum"]
        # first entry is "All" — the total
        for entry in stats:
            if entry["difficulty"] == "All":
                return entry["count"]
    except Exception as e:
        print(f"[LeetCode] Error: {e}")
    return None


def fetch_gfg_solved(username: str) -> int | None:
    """
    Hits the unofficial GFG profile API.
    Returns total problems solved or None on failure.
    """
    url = f"https://geeks-for-geeks-api.vercel.app/{username}"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        # field is 'totalProblemsSolved' in this API
        return int(data.get("totalProblemsSolved", 0))
    except Exception as e:
        print(f"[GFG] Error: {e}")

    # fallback: try gfgstatscard API
    try:
        url2 = f"https://gfgstatscard.vercel.app/api/{username}"
        resp = requests.get(url2, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return int(data.get("totalProblemsSolved", 0))
    except Exception as e2:
        print(f"[GFG fallback] Error: {e2}")

    return None


def patch_readme(lc: int, gfg: int) -> None:
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    total = lc + gfg

    # ── 1. LeetCode badge ─────────────────────────────────────────────────────
    # Matches: /badge/LeetCode-NNN%20Solved-
    content = re.sub(
        r"(img\.shields\.io/badge/LeetCode-)\d+(%20Solved-)",
        rf"\g<1>{lc}\2",
        content,
    )

    # ── 2. GFG badge ──────────────────────────────────────────────────────────
    # Matches: /badge/GFG-NNN%20Solved-
    content = re.sub(
        r"(img\.shields\.io/badge/GFG-)\d+(%20Solved-)",
        rf"\g<1>{gfg}\2",
        content,
    )

    # ── 3. Mission Targets table row ──────────────────────────────────────────
    # Matches: 🎯 NNN/500
    content = re.sub(
        r"(🎯\s*)\d+(/500)",
        rf"\g<1>{total}\2",
        content,
    )

    # ── 4. About Me bullet ────────────────────────────────────────────────────
    # Matches: Solved: NNN LeetCode problems & NNN+ GFG problems
    content = re.sub(
        r"(Solved:</b>\s*)\d+( LeetCode problems &amp; |\s*LeetCode problems &\s*)\d+(\+? GFG problems)",
        rf"\g<1>{lc}\g<2>{gfg}\3",
        content,
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ README patched → LeetCode: {lc}, GFG: {gfg}, Total: {total}")


if __name__ == "__main__":
    print("Fetching LeetCode stats...")
    lc_count = fetch_leetcode_solved(LEETCODE_USERNAME)
    print(f"  → {lc_count}")

    print("Fetching GFG stats...")
    gfg_count = fetch_gfg_solved(GFG_USERNAME)
    print(f"  → {gfg_count}")

    if lc_count is None:
        print("⚠️  LeetCode fetch failed — keeping existing value")
        # Read current value from README so we don't wipe it
        with open(README_PATH, "r") as f:
            txt = f.read()
        m = re.search(r"badge/LeetCode-(\d+)%20Solved", txt)
        lc_count = int(m.group(1)) if m else 0

    if gfg_count is None:
        print("⚠️  GFG fetch failed — keeping existing value")
        with open(README_PATH, "r") as f:
            txt = f.read()
        m = re.search(r"badge/GFG-(\d+)%20Solved", txt)
        gfg_count = int(m.group(1)) if m else 0

    patch_readme(lc_count, gfg_count)
