from pathlib import Path
import re
import shutil
from datetime import datetime

ROOT = Path.home() / "TELEGRAM-SOURCE"
LOGO = ROOT / "pixlegram_logo.png"

RES = ROOT / "TMessagesProj" / "src" / "main" / "res"
BACKUP = ROOT / ".pixlegram_backup" / "branding_v1"

APP_NAME = "PIXLEGRAM"

if not ROOT.exists():
    raise SystemExit("[ERROR] TELEGRAM-SOURCE not found")

if not LOGO.exists():
    raise SystemExit(f"[ERROR] Logo not found: {LOGO}")

if not RES.exists():
    raise SystemExit(f"[ERROR] Android resources not found: {RES}")

BACKUP.mkdir(parents=True, exist_ok=True)


def backup_file(path):
    rel = path.relative_to(ROOT)
    dst = BACKUP / rel
    dst.parent.mkdir(parents=True, exist_ok=True)

    if not dst.exists():
        shutil.copy2(path, dst)


def replace_app_strings():
    changed = []

    for path in RES.glob("values*/strings.xml"):
        text = path.read_text(encoding="utf-8")
        original = text

        text = re.sub(
            r'(<string\s+name="AppName"[^>]*>).*?(</string>)',
            rf'\1{APP_NAME}\2',
            text,
            flags=re.DOTALL
        )

        text = re.sub(
            r'(<string\s+name="AppNameBeta"[^>]*>).*?(</string>)',
            rf'\1{APP_NAME}\2',
            text,
            flags=re.DOTALL
        )

        if text != original:
            backup_file(path)
            path.write_text(text, encoding="utf-8")
            changed.append(str(path.relative_to(ROOT)))

    return changed


def install_logo():
    destination = RES / "drawable-nodpi" / "pixlegram_logo.png"
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists():
        backup_file(destination)

    shutil.copy2(LOGO, destination)

    return destination


def patch_manifests():
    changed = []

    manifests = list((ROOT / "TMessagesProj").rglob("AndroidManifest.xml"))
    manifests += list((ROOT / "TMessagesProj_App").rglob("AndroidManifest.xml"))

    seen = set()

    for path in manifests:
        if path in seen:
            continue
        seen.add(path)

        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue

        # Меняем только реальные application manifests,
        # где уже используется имя приложения.
        if 'android:label="@string/AppName"' not in text:
            if 'android:label="@string/AppNameBeta"' not in text:
                continue

        original = text

        # Название
        text = text.replace(
            'android:label="@string/AppNameBeta"',
            'android:label="@string/AppName"'
        )

        # Существующая иконка
        text = re.sub(
            r'android:icon="[^"]+"',
            'android:icon="@drawable/pixlegram_logo"',
            text
        )

        # Round icon
        text = re.sub(
            r'android:roundIcon="[^"]+"',
            'android:roundIcon="@drawable/pixlegram_logo"',
            text
        )

        if 'android:icon=' not in text:
            text = re.sub(
                r'(<application\b)',
                r'\1\n        android:icon="@drawable/pixlegram_logo"',
                text,
                count=1
            )

        if 'android:roundIcon=' not in text:
            text = re.sub(
                r'(<application\b[^>]*?)>',
                r'\1\n        android:roundIcon="@drawable/pixlegram_logo">',
                text,
                count=1,
                flags=re.DOTALL
            )

        if text != original:
            backup_file(path)
            path.write_text(text, encoding="utf-8")
            changed.append(str(path.relative_to(ROOT)))

    return changed


def validate():
    logo = RES / "drawable-nodpi" / "pixlegram_logo.png"

    if not logo.exists():
        raise SystemExit("[ERROR] PIXLEGRAM logo was not installed")

    errors = []

    for path in RES.glob("values*/strings.xml"):
        text = path.read_text(encoding="utf-8")

        for match in re.finditer(
            r'<string\s+name="(AppName|AppNameBeta)"[^>]*>(.*?)</string>',
            text,
            flags=re.DOTALL
        ):
            name = match.group(1)
            value = re.sub(r"<.*?>", "", match.group(2)).strip()

            if value != APP_NAME:
                errors.append(
                    f"{path.relative_to(ROOT)}: {name} = {value}"
                )

    if errors:
        print("\n[ERROR] Branding validation failed:")
        for e in errors:
            print("  " + e)
        raise SystemExit(1)

    print("[OK] PIXLEGRAM branding validated")


print("=" * 55)
print("PIXLEGRAM 1.0 — BRANDING")
print("=" * 55)

print("\n[1/4] Checking logo...")
print(f"[OK] {LOGO}")
print(f"[OK] {LOGO.stat().st_size // 1024} KB")

print("\n[2/4] Installing logo...")
logo = install_logo()
print(f"[OK] {logo.relative_to(ROOT)}")

print("\n[3/4] Changing application name...")
strings = replace_app_strings()

if strings:
    for item in strings:
        print(f"[CHANGED] {item}")
else:
    print("[INFO] AppName already PIXLEGRAM")

print("\n[4/4] Changing launcher icon...")
manifests = patch_manifests()

if manifests:
    for item in manifests:
        print(f"[CHANGED] {item}")
else:
    print("[INFO] No matching application manifest changes needed")

print("\nValidating...")
validate()

print("\n" + "=" * 55)
print("PIXLEGRAM 1.0 BRANDING READY")
print("=" * 55)
print("\nName: PIXLEGRAM")
print("Logo: drawable-nodpi/pixlegram_logo.png")
print(f"Backup: {BACKUP.relative_to(ROOT)}")
print("\n[OK] Old app branding replaced")
print("[OK] Telegram core was not globally renamed")
print("[OK] Backup created before modifications")

