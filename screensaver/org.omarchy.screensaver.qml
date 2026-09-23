//@ pragma AppId org.omarchy.screensaver
import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io

Scope {
    id: root
    property var photos: []
    property int current: 0
    property real blend: 0
    property int intervalMs: 8000
    property bool ready: false
    property bool closing: false
    property var windows: []
    property var visibleScreens: []
    property int mappingIndex: 0
    property bool mapped: false
    property string initialMonitor: ""

    function mapNextMonitor() {
        var monitor = mappingIndex < Quickshell.screens.length
            ? Quickshell.screens[mappingIndex].name : initialMonitor
        if (!monitor) { root.dismiss("no monitor available"); return }
        focusMonitor.command = ["hyprctl", "dispatch",
            "hl.dsp.focus({ monitor = " + JSON.stringify(monitor) + " })"]
        focusMonitor.running = true
        mappingDeadline.restart()
    }

    function dismiss(reason) {
        if (closing) return
        closing = true
        console.log("Elvis screensaver dismissed: " + reason)
        Qt.quit()
    }

    FileView {
        path: Quickshell.env("ELVIS_SCREENSAVER_CONFIG")
            || Quickshell.env("HOME") + "/.config/omarchy/elvis-screensaver/photos.json"
        onLoaded: {
            try {
                var settings = JSON.parse(text())
                if (!Array.isArray(settings.photos) || !settings.photos.length)
                    throw new Error("No photos configured")
                root.photos = settings.photos
                root.intervalMs = Math.max(2000, Number(settings.intervalMs) || 8000)
                root.ready = true
                initialFocus.running = true
                mappingDeadline.start()
            } catch (error) {
                console.error("Elvis screensaver: " + error)
                root.dismiss("invalid photo settings")
            }
        }
        onLoadFailed: root.dismiss("could not read photo settings")
    }

    // Ignore initial pointer placement while the fullscreen windows are mapped.
    Timer { id: inputGrace; interval: 500 }
    Timer { id: mappingDeadline; interval: 5000; onTriggered: root.dismiss("monitor mapping timed out") }
    Process {
        id: initialFocus
        command: ["hyprctl", "monitors", "-j"]
        stdout: StdioCollector {
            onStreamFinished: {
                try {
                    var monitor = JSON.parse(text).find(m => m.focused)
                    root.initialMonitor = monitor ? monitor.name : ""
                } catch (error) { console.warn("Could not read initial monitor: " + error) }
            }
        }
        onExited: {
            if (!root.initialMonitor && Quickshell.screens.length)
                root.initialMonitor = Quickshell.screens[0].name
            root.mapNextMonitor()
        }
    }
    // Like Omarchy's stock launcher, wait for each openwindow event before
    // focusing the next output. Simultaneous Wayland windows otherwise pile
    // onto the currently focused monitor, regardless of QsWindow.screen.
    Process {
        id: focusMonitor
        onExited: (exitCode, exitStatus) => {
            if (exitCode !== 0) { root.dismiss("could not focus monitor"); return }
            if (root.mappingIndex < Quickshell.screens.length) {
                root.visibleScreens = Quickshell.screens.slice(0, root.mappingIndex + 1)
            } else {
                root.mapped = true
                mappingDeadline.stop()
                inputGrace.start()
            }
        }
    }
    Timer {
        running: root.ready && root.photos.length > 1
        interval: root.intervalMs
        repeat: true
        onTriggered: transition.start()
    }
    NumberAnimation {
        id: transition
        target: root
        property: "blend"
        from: 0
        to: 1
        duration: 900
        easing.type: Easing.InOutSine
        onFinished: {
            root.current = (root.current + 1) % root.photos.length
            root.blend = 0
        }
    }

    Variants {
        model: root.visibleScreens
        FloatingWindow {
            id: window
            required property var modelData
            title: "Elvis Screensaver / " + modelData.name
            color: "black"
            // Omarchy's org.omarchy.screensaver rule supplies fullscreen.
            // Qt's client-side fullscreen request can target the wrong output.
            implicitWidth: modelData.width
            implicitHeight: modelData.height
            onClosed: root.dismiss("window closed")
            Component.onCompleted: root.windows = root.windows.concat([window])
            Component.onDestruction: root.windows = root.windows.filter(w => w !== window)

            Item {
                id: content
                anchors.fill: parent
                focus: true
                Keys.onPressed: event => {
                    event.accepted = true
                    root.dismiss("keyboard")
                }
                Slideshow {
                    anchors.fill: parent
                    photos: root.photos
                    current: root.current
                    blend: root.blend
                }
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.AllButtons
                    cursorShape: Qt.BlankCursor
                    property real lastX: -1
                    property real lastY: -1
                    onPressed: root.dismiss("mouse button")
                    onWheel: event => { event.accepted = true; root.dismiss("mouse wheel") }
                    onPositionChanged: mouse => {
                        var moved = lastX >= 0 && Math.hypot(mouse.x - lastX, mouse.y - lastY) > 2
                        if (lastX < 0 || inputGrace.running || !root.mapped) {
                            lastX = mouse.x
                            lastY = mouse.y
                        }
                        if (root.mapped && !inputGrace.running && moved) root.dismiss("mouse movement")
                    }
                }
            }
        }
    }

    Connections {
        target: Hyprland
        function onRawEvent(event) {
            if (!root.mapped && event.name === "openwindow") {
                var parts = event.parse(4)
                if (parts[2] === "org.omarchy.screensaver"
                    && parts[3] === "Elvis Screensaver / " + Quickshell.screens[root.mappingIndex].name) {
                    root.mappingIndex += 1
                    Qt.callLater(root.mapNextMonitor)
                }
            }
            if (root.mapped && !inputGrace.running && event.name === "activewindow") {
                var appId = String(event.data).split(",")[0]
                if (appId && appId !== "org.omarchy.screensaver") root.dismiss("focus changed")
            }
        }
    }

    IpcHandler {
        target: "screensaver"
        function stop(): string { root.dismiss("IPC"); return "stopped" }
        function status(): string {
            return JSON.stringify({ready: root.ready, photos: root.photos.length,
                current: root.current, intervalMs: root.intervalMs, windows: root.windows.length,
                mapped: root.mapped})
        }
    }
}
