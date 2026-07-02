import re

_PROFANITY_KEYWORDS = [
    "hate", "kill", "stupid", "idiot", "moron", "lazy",
    "ugly", "terrible", "awful", "horrible", "damn",
]

_SUSPICIOUS_PATTERNS = [
    r"(?i)\bbuy\s+now\b",
    r"(?i)\bclick\s+here\b",
    r"(?i)\blimited\s+time\b",
    r"(?i)\bact\s+now\b",
    r"(?i)\bdon't\s+miss\b",
    r"(?i)\bexclusive\s+offer\b",
    r"(?i)\bfree\s+\w+\b",
    r"(?i)\bguaranteed\b",
    r"(?i)\brisk[- ]?free\b",
]

_PLATFORM_LIMITS = {
    "twitter": 280,
    "linkedin": 3000,
    "facebook": 63206,
    "instagram": 2200,
    "general": 5000,
}

_TONE_KEYWORDS = {
    "professional": ["please", "thank you", "regards", "we believe", "our team"],
    "casual": ["hey", "cool", "awesome", "guys", "check it out"],
    "humorous": ["funny", "hilarious", "lol", "jk", "just kidding"],
}


def _check_profanity(text: str) -> list[str]:
    found = []
    for word in _PROFANITY_KEYWORDS:
        if re.search(rf"\b{re.escape(word)}\b", text.lower()):
            found.append(f"Potentially inappropriate language: '{word}'")
    return found


def _check_suspicious_patterns(text: str) -> list[str]:
    found = []
    for pattern in _SUSPICIOUS_PATTERNS:
        match = re.search(pattern, text)
        if match:
            found.append(f"Suspicious marketing pattern detected: '{match.group()}'")
    return found


def _check_length(text: str, platform: str) -> list[str]:
    limit = _PLATFORM_LIMITS.get(platform, 5000)
    if len(text) > limit:
        return [f"Exceeds {platform} character limit ({len(text)} > {limit})"]
    if platform == "twitter" and len(text) > 240:
        return [f"Close to Twitter limit ({len(text)}/280). Consider shortening."]
    return []


def _check_hashtags(text: str) -> list[str]:
    hashtags = re.findall(r"#\w+", text)
    issues = []
    if len(hashtags) > 10:
        issues.append(f"Too many hashtags ({len(hashtags)}). Consider max 3-5.")
    if len(hashtags) > 3 and len(text) < 100:
        issues.append("Short post with many hashtags looks like spam.")
    return issues


def _check_urls(text: str) -> list[str]:
    urls = re.findall(r"https?://\S+", text)
    issues = []
    for url in urls:
        if any(ext in url.lower() for ext in [".exe", ".zip", ".scr", ".bat"]):
            issues.append(f"Suspicious file URL detected: {url}")
    if len(urls) > 3:
        issues.append(f"Multiple URLs ({len(urls)}) — may look like link stuffing.")
    return issues


def _check_tone_alignment(text: str, tone: str) -> list[str]:
    if tone == "neutral":
        return []
    expected = _TONE_KEYWORDS.get(tone, [])
    if not expected:
        return []
    found_any = any(kw in text.lower() for kw in expected)
    if not found_any:
        return [f"Text does not match the requested '{tone}' tone."]
    return []


def _check_caps_usage(text: str) -> list[str]:
    words = text.split()
    if not words:
        return []
    all_caps = [w for w in words if len(w) > 2 and w.isupper()]
    if len(all_caps) > len(words) * 0.3:
        return [f"Excessive ALL CAPS ({len(all_caps)}/{len(words)} words)."]
    return []


def _generate_suggestions(issues: list[str]) -> list[str]:
    suggestions = []
    for issue in issues:
        il = issue.lower()
        if "profanity" in il or "inappropriate" in il:
            suggestions.append("Replace flagged words with neutral alternatives.")
        if "marketing" in il or "suspicious pattern" in il:
            suggestions.append("Rephrase to reduce urgency marketing language.")
        if "character limit" in il:
            suggestions.append("Shorten the post or choose a different platform.")
        if "hashtag" in il:
            suggestions.append("Reduce hashtag count to 3-5 max.")
        if "url" in il:
            suggestions.append("Limit links and avoid suspicious file types.")
        if "tone" in il:
            suggestions.append(f"Adjust language to match the desired tone.")
        if "caps" in il:
            suggestions.append("Use Title Case or sentence case instead of ALL CAPS.")
    if not suggestions:
        suggestions.append("No changes needed — content looks good.")
    return suggestions


def _generate_summary(approved: bool, score: int, issues: list[str]) -> str:
    if approved:
        return f"Approved (score: {score}/100). {len(issues)} minor notes."
    if score >= 60:
        return f"Conditional approval (score: {score}/100). Review {len(issues)} items."
    return f"Not approved (score: {score}/100). {len(issues)} issues must be resolved."


def review(
    action_plan: str,
    platform: str = "general",
    tone: str = "neutral",
    strictness: str = "medium",
) -> dict:
    if not action_plan or not action_plan.strip():
        return {
            "approved": False,
            "score": 0,
            "issues": ["Empty action plan — nothing to review."],
            "suggestions": ["Provide the social media post text to review."],
            "summary": "Rejected: empty content.",
        }

    issues: list[str] = []
    weight = {"low": 0.5, "medium": 1.0, "high": 1.5}.get(strictness, 1.0)

    issues.extend(_check_profanity(action_plan))
    issues.extend(_check_suspicious_patterns(action_plan))
    issues.extend(_check_length(action_plan, platform))
    issues.extend(_check_hashtags(action_plan))
    issues.extend(_check_urls(action_plan))
    issues.extend(_check_tone_alignment(action_plan, tone))
    issues.extend(_check_caps_usage(action_plan))

    if strictness == "high":
        if len(action_plan.split()) < 5:
            issues.append("Very short post — may lack meaningful content.")
        if platform == "linkedin" and len(action_plan.split()) < 20:
            issues.append("LinkedIn posts typically perform better with 50+ words.")

    base_score = 100
    penalty = min(len(issues) * int(15 * weight), 85)
    score = max(base_score - penalty, 0)

    if strictness == "low":
        score = min(score + 10, 100)

    approved = score >= 60
    suggestions = _generate_suggestions(issues)
    summary = _generate_summary(approved, score, issues)

    return {
        "approved": approved,
        "score": score,
        "issues": issues,
        "suggestions": suggestions,
        "summary": summary,
    }
