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
