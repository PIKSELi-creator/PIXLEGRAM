from pathlib import Path
import shutil
import json
import re

ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / ".pixlegram_backup"
REPORT = ROOT / "pixlegram" / "config" / "source_scan.json"

JAVA_ROOTS = [
    ROOT / "TMessagesProj",
    ROOT / "TMessagesProj_App",
]

def check_source():
    required = [
        ROOT / "TMessagesProj",
        ROOT / "TMessagesProj_App",
        ROOT / "gradlew",
    ]

    print("[*] Проверяем исходники...")

    for path in required:
        if not path.exists():
            print(f"[ERROR] Не найдено: {path}")
            return False

    print("[OK] Telegram source найден")
    return True


def backup_file(path):
    if not path.exists():
        return

    relative = path.relative_to(ROOT)
    target = BACKUP / relative
    target.parent.mkdir(parents=True, exist_ok=True)

    if not target.exists():
        shutil.copy2(path, target)


def create_backup():
    print("[*] Проверяем backup...")

    BACKUP.mkdir(exist_ok=True)

    for file in [
        ROOT / "TMessagesProj/src/main/res/values/strings.xml",
        ROOT / "TMessagesProj_App/build.gradle",
        ROOT / "gradle.properties",
    ]:
        backup_file(file)

    print(f"[OK] Backup: {BACKUP}")


def scan_source():
    print("[*] Сканируем Telegram source...")
    print()

    results = {
        "gifts": [],
        "privacy": [],
        "online": [],
        "messages": [],
        "profile": [],
        "api": [],
    }

    patterns = {
        "gifts": [
            r"\bGift\b",
            r"\bGifts\b",
            r"gift",
            r"stars",
        ],
        "privacy": [
            r"privacy",
            r"Privacy",
            r"PrivacySettings",
        ],
        "online": [
            r"online",
            r"status",
            r"UserStatus",
        ],
        "messages": [
            r"MessageObject",
            r"messages",
            r"Message",
        ],
        "profile": [
            r"Profile",
            r"UserInfo",
            r"ProfileActivity",
        ],
        "api": [
            r"APP_ID",
            r"APP_HASH",
            r"BuildVars",
        ],
    }

    extensions = {".java", ".kt", ".gradle", ".xml"}

    for root in JAVA_ROOTS:
        if not root.exists():
            continue

        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in extensions:
                continue

            try:
                text = path.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )
            except Exception:
                continue

            relative = str(path.relative_to(ROOT))

            for category, category_patterns in patterns.items():
                matches = []

                for pattern in category_patterns:
                    if re.search(pattern, text):
                        matches.append(pattern)

                if matches:
                    results[category].append({
                        "file": relative,
                        "matches": matches
                    })

    REPORT.parent.mkdir(parents=True, exist_ok=True)

    REPORT.write_text(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    for category, files in results.items():
        print(f"[+] {category}: {len(files)} файлов")

    print()
    print(f"[OK] Отчёт сохранён:")
    print(REPORT)


def main():
    print("=" * 55)
    print("           PIXLEGRAM 1.0.0 SOURCE SCAN")
    print("=" * 55)
    print()

    if not check_source():
        raise SystemExit(1)

    create_backup()
    scan_source()

    print()
    print("=" * 55)
    print("[OK] Сканирование завершено")
    print("[*] Исходники пока не изменялись")
    print("[*] Следующий этап — интеграция PIXLEGRAM Gifts")
    print("=" * 55)


if __name__ == "__main__":
    main()
