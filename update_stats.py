"""
Auto-updates LeetCode and GFG solve counts in README.md.
Runs via GitHub Actions daily.
"""

import re
import requests

LEETCODE_USERNAME = "Snehal_Garg"
GFG_USERNAME      = "snehalgeh4e"
README_PATH       = "README.md"


def fetch_leetcode_solved(username: str) -> int | None:
    """Uses LeetCode's official public GraphQL API — no auth needed."""
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
            headers={
                "Content-Type": "application/json",
                "Referer": "https://leetcode.com",
                "User-Agent": "Mozilla/5.0"
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        stats = data["data"]["matchedUser"]["submitStats"]["acSubmissionNum"]
        for entry in stats:
            if entry["difficulty"] == "All":
                return entry["count"]
    except Exception as e:
        print(f"[LeetCode GraphQL] Error: {e}")
    return None


def fetch_gfg_solved(username: str) -> int | None:
    """
    Tries multiple GFG APIs in order, sums difficulty counts as fallback.
    """

    # ── API 1: geeks-for-geeks-stats ──────────────────────────────────────────
    try:
        url = f"https://geeks-for-geeks-stats-api.vercel.app/?raw=Y&userName={username}"
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        print(f"[GFG API 1] raw response: {data}")
        # This API returns keys: School, Basic, Easy, Medium, Hard
        total = sum([
            int(data.get("School", 0) or 0),
            int(data.get("Basic",  0) or 0),
            int(data.get("Easy",   0) or 0),
            int(data.get("Medium", 0) or 0),
            int(data.get("Hard",   0) or 0),
        ])
        if total > 0:
            print(f"[GFG API 1] total = {total}")
            return total
    except Exception as e:
        print(f"[GFG API 1] Error: {e}")

    # ── API 2: gfgstatscard ───────────────────────────────────────────────────
    try:
        url2 = f"https://gfgstatscard.vercel.app/api/{username}"
        resp = requests.get(url2, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        print(f"[GFG API 2] raw response: {data}")
        val = data.get("totalProblemsSolved") or data.get("total") or 0
        if int(val) > 0:
            return int(val)
    except Exception as e:
        print(f"[GFG API 2] Error: {e}")

    # ── API 3: geeks-for-geeks-api ────────────────────────────────────────────
    try:
        url3 = f"https://geeks-for-geeks-api.vercel.app/{username}"
        resp = requests.get(url3, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        print(f"[GFG API 3] raw response: {data}")
        val = data.get("totalProblemsSolved") or data.get("total") or 0
        if int(val) > 0:
            return int(val)
        # Try summing if totalProblemsSolved not present
        total = sum([
            int(data.get("School", 0) or 0),
            int(data.get("Basic",  0) or 0),
            int(data.get("Easy",   0) or 0),
            int(data.get("Medium", 0) or 0),
            int(data.get("Hard",   0) or 0),
        ])
        if total > 0:
            return total
    except Exception as e:
        print(f"[GFG API 3] Error: {e}")

    # ── API 4: scrape profile page ────────────────────────────────────────────
    try:
        url4 = f"https://auth.geeksforgeeks.org/user/{username}/practice/"
        resp = requests.get(url4, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        text = resp.text
        # Look for "Problems Solved" count in page HTML
        match = re.search(r'"totalProblemsSolved"\s*:\s*(\d+)', text)
        if match:
            return int(match.group(1))
        # Alternate pattern
        match2 = re.search(r'(\d+)\s*</span>\s*<[^>]+>Problems Solved', text)
        if match2:
            return int(match2.group(1))
    except Exception as e:
        print(f"[GFG scrape] Error: {e}")

    return None


def read_current_value(pattern: str) -> int:
    """Reads current badge number from README as fallback."""
    try:
        with open(README_PATH, "r") as f:
            txt = f.read()
        m = re.search(pattern, txt)
        return int(m.group(1)) if m else 0
    except Exception:
        return 0


def patch_readme(lc: int, gfg: int) -> None:
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    total = lc + gfg

    # 1. LeetCode badge
    content = re.sub(
        r"(img\.shields\.io/badge/LeetCode-)\d+(%20Solved-)",
        rf"\g<1>{lc}\2",
        content,
    )
    # 2. GFG badge
    content = re.sub(
        r"(img\.shields\.io/badge/GFG-)\d+(%20Solved-)",
        rf"\g<1>{gfg}\2",
        content,
    )
    # 3. Mission Targets table
    content = re.sub(
        r"(🎯\s*)\d+(/500)",
        rf"\g<1>{total}\2",
        content,
    )
    # 4. About Me bullet — handles both & and &amp;
    content = re.sub(
        r"(Solved:</b>\s*)\d+(\s*LeetCode problems\s*(?:&amp;|&)\s*)\d+(\+?\s*GFG problems)",
        rf"\g<1>{lc}\g<2>{gfg}\3",
        content,
    )

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ README patched → LeetCode: {lc}, GFG: {gfg}, Total: {total}")


if __name__ == "__main__":
    print("=" * 50)
    print("Fetching LeetCode stats...")
    lc_count = fetch_leetcode_solved(LEETCODE_USERNAME)
    print(f"  LeetCode result: {lc_count}")

    print("Fetching GFG stats...")
    gfg_count = fetch_gfg_solved(GFG_USERNAME)
    print(f"  GFG result: {gfg_count}")

    if lc_count is None:
        print("⚠️  LeetCode fetch failed — keeping existing value")
        lc_count = read_current_value(r"badge/LeetCode-(\d+)%20Solved")

    if gfg_count is None:
        print("⚠️  GFG fetch failed — keeping existing value")
        gfg_count = read_current_value(r"badge/GFG-(\d+)%20Solved")

    print(f"Final values → LeetCode: {lc_count}, GFG: {gfg_count}")
    patch_readme(lc_count, gfg_count)
