# utils/lang_colors.py

LANGUAGE_COLORS = {
    "TypeScript":   0x3178C6,
    "JavaScript":   0xF7DF1E,
    "Python":       0x3572A5,
    "Java":         0xB07219,
    "C++":          0xF34B7D,
    "C#":           0x178600,
    "C":            0x555555,
    "Go":           0x00ADD8,
    "Rust":         0xDEA584,
    "PHP":          0x4F5D95,
    "Ruby":         0x701516,
    "Kotlin":       0xA97BFF,
    "Swift":        0xF05138,
    "HTML":         0xE34C26,
    "CSS":          0x563D7C,
    "Shell":        0x89E051,
    "Dart":         0x00B4AB,
    "Vue":          0x41B883,
    "Svelte":       0xFF3E00,
    "Lua":          0x000080,
    "R":            0x198CE7,
    "Scala":        0xDC322F,
    "Haskell":      0x5E5186,
    "Elixir":       0x6E4A7E,
}

DEFAULT_COLOR = 0x2B2D31  # Discord dark embed


def get_color(languages: dict) -> int:
    if not languages:
        return DEFAULT_COLOR
    dominant = max(languages, key=languages.get)
    return LANGUAGE_COLORS.get(dominant, DEFAULT_COLOR)


def format_languages(languages: dict) -> str:
    if not languages:
        return "`N/A`"
    total = sum(languages.values())
    parts = []
    for lang, bytes_ in sorted(languages.items(), key=lambda x: x[1], reverse=True):
        pct = (bytes_ / total) * 100
        if pct >= 1.0:
            parts.append(f"`{lang} {pct:.0f}%`")
    return " ".join(parts) if parts else "`N/A`"
