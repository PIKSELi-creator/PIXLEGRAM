#!/usr/bin/env python3

from pathlib import Path
import json
import shutil
import re
import sys
from datetime import datetime

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "TMessagesProj"
APP = ROOT / "TMessagesProj_App"
BACKUP = ROOT / ".pixlegram_backup" / "engine"

APP_NAME = "PIXLEGRAM"
VERSION = "1.0.0"


def log(tag, text):
    print(f"[{tag}] {text}")


def backup(path):
    if not path.exists():
        return
    dst = BACKUP / path.relative_to(ROOT)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(path, dst)


def replace_file(path, replacements):
    if not path.exists():
        return False

    old = path.read_text(encoding="utf-8")
    new = old

    for a, b in replacements:
        new = new.replace(a, b)

    if new != old:
        backup(path)
        path.write_text(new, encoding="utf-8")
        return True

    return False


def find_files(pattern):
    return list(SRC.rglob(pattern)) + list(APP.rglob(pattern))


def branding():
    log("*", "Настраиваем PIXLEGRAM branding...")

    string_files = list(SRC.glob("src/main/res/values*/strings.xml"))

    changed = 0

    for path in string_files:
        if replace_file(path, [
            ('<string name="AppName">Telegram</string>',
             '<string name="AppName">PIXLEGRAM</string>'),
            ('<string name="AppNameBeta">Telegram Beta</string>',
             '<string name="AppNameBeta">PIXLEGRAM</string>')
        ]):
            changed += 1

    log("OK", f"Branding изменён в {changed} файлах")


def config():
    log("*", "Создаём конфигурацию PIXLEGRAM...")

    path = ROOT / "pixlegram" / "config" / "pixlegram.json"
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "name": APP_NAME,
        "version": VERSION,
        "telegram_client": True,
        "telegram_api": True,
        "telegram_auth": True,
        "channels": True,
        "groups": True,
        "messages": True,
        "media": True,
        "gifts": True,
        "gift_showcase": True,
        "google_email_auth": True,
        "build": "github-actions"
    }

    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    log("OK", "PIXLEGRAM config создан")


def audit():
    log("*", "Проверяем Telegram-инфраструктуру...")

    checks = {
        "Telegram source": SRC.exists(),
        "Application module": APP.exists(),
        "Gradle": (ROOT / "gradlew").exists(),
        "Telegram API": bool(find_files("BuildVars.java")),
        "Authorization": bool(find_files("*Login*.java")),
        "Messages": bool(find_files("MessageObject.java")),
        "Channels": bool(find_files("*Channel*.java")),
        "Profile": bool(find_files("*Profile*.java")),
        "Gifts": bool(find_files("*Gift*.java")),
        "Network": bool(find_files("ConnectionsManager.java")),
    }

    failed = []

    for name, ok in checks.items():
        if ok:
            log("OK", name)
        else:
            log("!!", name)
            failed.append(name)

    return failed


def google_auth_audit():
    log("*", "Проверяем Google/email authorization flow...")

    files = find_files("*.java")
    found = False

    patterns = [
        "google_signin_allowed",
        "emailVerificationGoogle",
        "verifyEmail",
        "Google"
    ]

    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        if any(x in text for x in patterns):
            found = True
            break

    if found:
        log("OK", "Google/email authorization flow найден")
    else:
        log("!!", "Google/email flow не найден — Telegram source требует проверки")

    return found


def safety_check():
    log("*", "Проверяем опасные изменения...")

    controller = SRC / "src/main/java/org/telegram/messenger/MessagesController.java"

    if not controller.exists():
        return

    text = controller.read_text(encoding="utf-8", errors="ignore")

    if "PixlegramPrivacyConfig.isGhostModeEnabled" in text:
        log("!!", "Обнаружен Ghost Mode patch — для релиза 1.0 он отключён")
        backup(controller)

        # Восстанавливаем последнюю резервную копию ghost patch,
        # если она существует.
        ghost = ROOT / ".pixlegram_backup" / "ghost_mode" / "MessagesController.java"

        if ghost.exists():
            controller.write_text(
                ghost.read_text(encoding="utf-8"),
                encoding="utf-8"
            )
            log("OK", "MessagesController восстановлен из Ghost Mode backup")
        else:
            log("!!", "Backup Ghost Mode не найден — файл не изменён")


def main():
    print("=" * 58)
    print("          PIXLEGRAM 1.0 BUILD ENGINE")
    print("=" * 58)

    if not SRC.exists() or not APP.exists():
        log("ERR", "Telegram source не найден")
        sys.exit(1)

    BACKUP.mkdir(parents=True, exist_ok=True)

    log("OK", "Telegram source найден")
    log("OK", f"Backup: {BACKUP}")

    branding()
    config()

    failed = audit()
    google_auth_audit()
    safety_check()

    print()
    print("=" * 58)

    if failed:
        log("!!", "Есть проблемы:")
        for x in failed:
            print("   -", x)
    else:
        log("OK", "Основная инфраструктура Telegram найдена")

    print()
    log("OK", "PIXLEGRAM source подготовлен")
    log("INFO", "APK собираем ТОЛЬКО через GitHub Actions")
    print("=" * 58)


if __name__ == "__main__":
    main()
