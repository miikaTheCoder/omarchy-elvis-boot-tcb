import QtQuick
import QtQuick.Effects

Item {
    id: root
    property real elapsed: 0
    property bool dimDesktop: true
    readonly property int totalMs: 2350
    readonly property real ending: Math.max(0, Math.min(1, (totalMs - elapsed) / 500))
    readonly property real entrance: Math.max(0, Math.min(1, elapsed / 80))
    // One soft highlight, not a repeating strobe.
    readonly property real glint: Math.max(0, 1 - Math.abs(elapsed - 790) / 160)

    Rectangle {
        anchors.fill: parent
        color: "#07080b"
        opacity: root.dimDesktop ? 0.88 * root.entrance * root.ending : 0
    }
    TcbMark {
        // Brief halo behind the mark; the visible emblem is rendered directly.
        anchors.centerIn: parent
        width: Math.min(parent.width * 0.7, parent.height * 0.5)
        height: parent.height * 0.76
        elapsed: root.elapsed
        visible: root.glint > 0
        opacity: root.glint * 0.32 * root.ending
        layer.enabled: true
        layer.effect: MultiEffect {
            shadowEnabled: true
            shadowColor: "#edc36d"
            shadowBlur: 0.5
            shadowOpacity: 0.55
            shadowHorizontalOffset: 0
            shadowVerticalOffset: 0
        }
    }
    TcbMark {
        anchors.centerIn: parent
        width: Math.min(parent.width * 0.7, parent.height * 0.5)
        height: parent.height * 0.76
        elapsed: root.elapsed
        opacity: root.entrance * root.ending
    }
}
