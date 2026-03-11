# utils/lang_colors.py

LANGUAGE_COLORS = {
    "TypeScript":   0x3178C6,  # Biru TypeScript
    "JavaScript":   0xF7DF1E,  # Kuning JavaScript
    "Python":       0x3572A5,  # Biru Python
    "Java":         0xB07219,  # Coklat Java
    "C++":          0xF34B7D,  # Pink C++
    "C#":           0x178600,  # Hijau C#
    "C":            0x555555,  # Abu C
    "Go":           0x00ADD8,  # Cyan Go
    "Rust":         0xDEA584,  # Oranye Rust
    "PHP":          0x4F5D95,  # Ungu PHP
    "Ruby":         0x701516,  # Merah Ruby
    "Kotlin":       0xA97BFF,  # Ungu Kotlin
    "Swift":        0xF05138,  # Oranye Swift
    "HTML":         0xE34C26,  # Oranye HTML
    "CSS":          0x563D7C,  # Ungu CSS
    "Shell":        0x89E051,  # Hijau Shell
    "Dart":         0x00B4AB,  # Teal Dart
    "Vue":          0x41B883,  # Hijau Vue
    "Svelte":       0xFF3E00,  # Merah Svelte
    "Lua":          0x000080,  # Navy Lua
    "R":            0x198CE7,  # Biru R
    "Scala":        0xDC322F,  # Merah Scala
    "Haskell":      0x5E5186,  # Ungu Haskell
    "Elixir":       0x6E4A7E,  # Ungu Elixir
    "Unknown":      0x95A5A6,  # Abu default
}

def get_embed_color(languages: dict) -> int:
    """
    Menentukan warna embed berdasarkan bahasa dengan persentase tertinggi.
    
    Args:
        languages (dict): Dictionary dari GitHub API berisi {bahasa: jumlah_byte}
    
    Returns:
        int: Warna embed dalam format hex integer
    """
    if not languages:
        return LANGUAGE_COLORS["Unknown"]

    dominant_lang = max(languages, key=languages.get)
    return LANGUAGE_COLORS.get(dominant_lang, LANGUAGE_COLORS["Unknown"])


def get_language_percentages(languages: dict) -> str:
    """
    Mengubah data bahasa menjadi string persentase yang mudah dibaca.
    
    Args:
        languages (dict): Dictionary dari GitHub API berisi {bahasa: jumlah_byte}
    
    Returns:
        str: String berformat '🔵 TypeScript 85.3% | 🟡 JavaScript 14.7%'
    """
    if not languages:
        return "Tidak diketahui"

    total = sum(languages.values())
    parts = []
    for lang, byte_count in sorted(languages.items(), key=lambda x: x[1], reverse=True):
        pct = (byte_count / total) * 100
        parts.append(f"**{lang}** {pct:.1f}%")

    return " | ".join(parts)
