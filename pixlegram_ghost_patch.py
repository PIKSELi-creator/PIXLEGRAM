#!/usr/bin/env python3

from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parent

MESSAGES_CONTROLLER = (
    ROOT
    / "TMessagesProj/src/main/java/org/telegram/messenger/MessagesController.java"
)

PRIVACY_CONFIG = (
    ROOT
    / "TMessagesProj/src/main/java/org/telegram/messenger/PixlegramPrivacyConfig.java"
)

BACKUP_DIR = ROOT / ".pixlegram_backup" / "ghost_mode"


PRIVACY_CONFIG_CONTENT = """\
package org.telegram.messenger;

public final class PixlegramPrivacyConfig {

    private static final String KEY_GHOST_MODE = "pixlegram_ghost_mode";

    private PixlegramPrivacyConfig() {
    }

    public static boolean isGhostModeEnabled(int account) {
        return MessagesController.getMainSettings(account)
                .getBoolean(KEY_GHOST_MODE, false);
    }

    public static void setGhostModeEnabled(int account, boolean enabled) {
        MessagesController.getMainSettings(account)
                .edit()
                .putBoolean(KEY_GHOST_MODE, enabled)
                .apply();
    }
}
"""


OLD_CONDITION = """\
if (!ignoreSetOnline && getConnectionsManager().getPauseTime() == 0 && ApplicationLoader.isScreenOn && !ApplicationLoader.mainInterfacePausedStageQueue) {
"""

NEW_CONDITION = """\
if (!PixlegramPrivacyConfig.isGhostModeEnabled(currentAccount)
                    && !ignoreSetOnline
                    && getConnectionsManager().getPauseTime() == 0
                    && ApplicationLoader.isScreenOn
                    && !ApplicationLoader.mainInterfacePausedStageQueue) {
"""


def fail(message):
    print(f"[ERROR] {message}")
    sys.exit(1)


def main():
    print("=" * 58)
    print("        PIXLEGRAM GHOST MODE PATCHER")
    print("=" * 58)

    # ---------------------------------------------------------
    # 1. Проверка исходников
    # ---------------------------------------------------------

    print("[*] Проверяем исходники...")

    if not MESSAGES_CONTROLLER.exists():
        fail(f"Не найден:\n{MESSAGES_CONTROLLER}")

    if not (ROOT / "TMessagesProj").exists():
        fail("Папка TMessagesProj не найдена.")

    print("[OK] Telegram source найден")

    # ---------------------------------------------------------
    # 2. Читаем MessagesController
    # ---------------------------------------------------------

    try:
        source = MESSAGES_CONTROLLER.read_text(encoding="utf-8")
    except Exception as e:
        fail(f"Не удалось прочитать MessagesController.java: {e}")

    # ---------------------------------------------------------
    # 3. Проверяем состояние патча
    # ---------------------------------------------------------

    if "PixlegramPrivacyConfig.isGhostModeEnabled(currentAccount)" in source:
        print("[!] Ghost Mode уже установлен.")
        print("[OK] Повторный патч не выполняется.")
        return

    occurrences = source.count(OLD_CONDITION)

    print(f"[*] Найдено подходящих участков: {occurrences}")

    if occurrences != 1:
        fail(
            "Ожидался ровно 1 участок updateTimerProc(), "
            f"но найдено: {occurrences}"
        )

    # ---------------------------------------------------------
    # 4. Backup
    # ---------------------------------------------------------

    print("[*] Создаём backup...")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    backup_controller = BACKUP_DIR / "MessagesController.java"

    shutil.copy2(
        MESSAGES_CONTROLLER,
        backup_controller
    )

    print(f"[OK] Backup создан:")
    print(f"     {backup_controller}")

    # ---------------------------------------------------------
    # 5. Создаём PixlegramPrivacyConfig.java
    # ---------------------------------------------------------

    if PRIVACY_CONFIG.exists():
        fail(
            "PixlegramPrivacyConfig.java уже существует, "
            "но патч не обнаружен. Отмена для безопасности."
        )

    PRIVACY_CONFIG.parent.mkdir(parents=True, exist_ok=True)

    PRIVACY_CONFIG.write_text(
        PRIVACY_CONFIG_CONTENT,
        encoding="utf-8"
    )

    print("[OK] Создан PixlegramPrivacyConfig.java")

    # ---------------------------------------------------------
    # 6. Патчим updateTimerProc()
    # ---------------------------------------------------------

    patched_source = source.replace(
        OLD_CONDITION,
        NEW_CONDITION,
        1
    )

    if patched_source == source:
        fail("Замена updateTimerProc() не произошла.")

    MESSAGES_CONTROLLER.write_text(
        patched_source,
        encoding="utf-8"
    )

    print("[OK] updateTimerProc() изменён")

    # ---------------------------------------------------------
    # 7. Проверка результата
    # ---------------------------------------------------------

    print("[*] Проверяем патч...")

    final_source = MESSAGES_CONTROLLER.read_text(
        encoding="utf-8"
    )

    checks = [
        (
            "PixlegramPrivacyConfig.java",
            PRIVACY_CONFIG.exists()
        ),
        (
            "Ghost Mode проверка",
            "PixlegramPrivacyConfig.isGhostModeEnabled(currentAccount)"
            in final_source
        ),
        (
            "старое условие удалено",
            final_source.count(OLD_CONDITION) == 0
        ),
        (
            "новое условие присутствует",
            final_source.count(
                "PixlegramPrivacyConfig.isGhostModeEnabled(currentAccount)"
            ) == 1
        ),
        (
            "ключ Ghost Mode",
            "pixlegram_ghost_mode" in PRIVACY_CONFIG.read_text(
                encoding="utf-8"
            )
        ),
    ]

    failed = False

    for name, result in checks:
        if result:
            print(f"[OK] {name}")
        else:
            print(f"[FAIL] {name}")
            failed = True

    # ---------------------------------------------------------
    # 8. Финальный результат
    # ---------------------------------------------------------

    if failed:
        print()
        print("[ERROR] Проверка патча не пройдена.")
        print("[!] Исходники могли быть изменены.")
        print("[!] Backup находится здесь:")
        print(f"    {BACKUP_DIR}")
        sys.exit(1)

    print()
    print("=" * 58)
    print("              PATCH OK")
    print("=" * 58)
    print()
    print("[OK] Ghost Mode добавлен.")
    print("[OK] Настройка хранится через MainSettings.")
    print("[OK] Значение по умолчанию: OFF")
    print("[OK] Telegram ignoreSetOnline не изменён.")
    print("[OK] Backup создан.")
    print()
    print("Следующий шаг:")
    print("  ./gradlew :TMessagesProj_App:assembleDebug --no-daemon")
    print()


if __name__ == "__main__":
    main()
