import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland

Item {
    id: root
    property var shell: null
    property var manifest: null
    property string omarchyPath: ""
    readonly property var lockService: shell ? shell.serviceFor("omarchy.lock") : null
    property bool sawLock: false
    property bool playing: false
    property real elapsed: 0
    property int portraitMs: 1000
    property string sequence: "portraits"
    property bool bootPending: false
    property bool bootConsumed: false
    property bool bootClaiming: false
    readonly property string runtimeDir: Quickshell.env("XDG_RUNTIME_DIR") || ""
    readonly property string sessionKey: String(Quickshell.env("HYPRLAND_INSTANCE_SIGNATURE")
        || Quickshell.env("XDG_SESSION_ID") || Quickshell.env("WAYLAND_DISPLAY")
        || "desktop").replace(/[^a-zA-Z0-9_.-]/g, "_")
    property string bootStatePath: runtimeDir ? runtimeDir + "/elvis-tcb-boot/" + sessionKey + ".state" : ""
    readonly property int animationMs: sequence === "tcb" ? 2350 : portraitMs * 3 + 350

    function stop() {
        unlockDelay.stop()
        bootDelay.stop()
        animation.stop()
        playing = false
        elapsed = 0
    }

    function play() {
        return playMode("portraits")
    }

    function playMode(mode) {
        // Current Omarchy shells intentionally do not expose the privileged
        // lock service to ordinary third-party plugins. TCB is a startup/manual
        // sequence and does not need that access; portraits still require it
        // because they are specifically triggered by an observed unlock.
        if ((mode !== "tcb" && !lockService) || (lockService && lockService.locked)) return false
        animation.stop()
        sequence = mode
        elapsed = 0
        playing = true
        animation.start()
        return true
    }

    function scheduleBoot() {
        if (bootPending && !bootConsumed && !bootClaiming && (!lockService || !lockService.locked))
            bootDelay.restart()
    }

    function reloadBootRequest() { bootState.reload() }

    function tryBoot() {
        if (!bootPending || bootConsumed || bootClaiming || (lockService && lockService.locked))
            return false
        if (!Quickshell.screens.length) return false
        // Persist consumption BEFORE showing the intro. Repeated hook calls,
        // theme reloads and shell restarts must not replay it this session.
        bootClaiming = true
        bootConsumed = true
        bootState.setText("played\n")
        return true
    }

    FileView {
        id: bootState
        path: root.bootStatePath
        printErrors: false
        watchChanges: true
        onFileChanged: reload()
        onLoaded: {
            if (root.bootClaiming) return
            var state = text().trim()
            root.bootConsumed = state === "played"
            root.bootPending = state === "pending"
            root.scheduleBoot()
        }
        onLoadFailed: root.bootPending = false
        onSaved: {
            if (!root.bootClaiming) return
            root.bootClaiming = false
            root.bootPending = false
            root.playMode("tcb")
        }
        onSaveFailed: {
            root.bootClaiming = false
            root.bootPending = false
            console.warn("Elvis TCB: could not save the session marker; skipping startup intro")
        }
    }

    // Reloading while unlocked starts nothing unless the startup hook left an
    // unconsumed request. Ordinary unlocks never create such a request.
    onLockServiceChanged: {
        stop()
        sawLock = !!lockService && lockService.locked
        scheduleBoot()
    }

    Connections {
        target: root.lockService
        function onLockedChanged() {
            if (root.lockService.locked) {
                root.stop()
                root.sawLock = true
            } else if (root.sawLock) {
                root.sawLock = false
                unlockDelay.restart()
            }
        }
    }

    // Allow the compositor to remove its session-lock surfaces first.
    Timer {
        id: unlockDelay
        interval: 100
        onTriggered: {
            if (root.bootPending || root.bootClaiming) root.tryBoot()
            else root.play()
        }
    }

    Timer { id: bootDelay; interval: 180; onTriggered: root.tryBoot() }
    Connections { target: Quickshell; function onScreensChanged() { root.scheduleBoot() } }

    NumberAnimation {
        id: animation
        target: root
        property: "elapsed"
        from: 0
        to: root.animationMs
        duration: root.animationMs
        onFinished: root.playing = false
    }

    // Create the rendering surfaces only during a sequence.
    // No polling, hidden animation, reserved space, keyboard grab or click grab.
    Loader {
        active: root.playing
        sourceComponent: Variants {
            model: Quickshell.screens
            PanelWindow {
                required property var modelData
                screen: modelData
                color: "transparent"
                anchors { top: true; bottom: true; left: true; right: true }
                exclusionMode: ExclusionMode.Ignore
                WlrLayershell.layer: WlrLayer.Overlay
                WlrLayershell.keyboardFocus: WlrKeyboardFocus.None
                WlrLayershell.namespace: "elvis-unlock"
                mask: Region {}
                Loader {
                    anchors.fill: parent
                    sourceComponent: root.sequence === "tcb" ? bootComponent : portraitsComponent
                    Component {
                        id: portraitsComponent
                        Sequence { elapsed: root.elapsed; portraitMs: root.portraitMs }
                    }
                    Component {
                        id: bootComponent
                        BootSequence { elapsed: root.elapsed }
                    }
                }
            }
        }
    }

    IpcHandler {
        target: "elvis"
        function preview(): string { return root.play() ? "playing" : "unavailable or locked" }
        function tcbPreview(): string { return root.playMode("tcb") ? "playing" : "unavailable or locked" }
        // Only the post-boot hook creates a pending request. This IPC method
        // rereads it; it cannot create or reset a consumed startup request.
        function boot(): string { root.reloadBootRequest(); return "checking" }
        function stop(): string { root.stop(); return "stopped" }
        function status(): string {
            return JSON.stringify({playing: root.playing, hasLockService: !!root.lockService,
                locked: !!root.lockService && root.lockService.locked,
                portraitMs: root.portraitMs, order: [3, 2, 1], sequence: root.sequence,
                bootPending: root.bootPending, bootConsumed: root.bootConsumed,
                version: root.manifest && root.manifest.version ? root.manifest.version : "development"})
        }
    }
}
