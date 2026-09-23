import QtQuick
import QtQuick.Effects
import "Portraits.js" as Art

Item {
    id: root
    property real elapsed: 0
    property int portraitMs: 1000
    property color ink: "#fff0d5"
    property bool dimDesktop: true
    readonly property int totalMs: portraitMs * 3 + 350
    readonly property real ending: Math.max(0, Math.min(1, (totalMs - elapsed) / 350))

    Rectangle {
        anchors.fill: parent
        color: "#080a0e"
        opacity: root.dimDesktop ? 0.76 * Math.min(1, root.elapsed / 100) * root.ending : 0
    }

    Repeater {
        model: Art.portraits
        Item {
            id: frame
            required property var modelData
            required property int index
            readonly property real localTime: root.elapsed - index * root.portraitMs
            readonly property real entrance: Math.max(0, Math.min(1, localTime / 70))
            readonly property real departure: index < 2
                ? Math.max(0, Math.min(1, (root.portraitMs + 110 - localTime) / 140))
                : root.ending
            width: parent.width
            height: parent.height
            visible: localTime >= 0 && departure > 0
            opacity: entrance * departure

            Portrait {
                id: portrait
                anchors.centerIn: parent
                width: Math.min(parent.width * 0.8, parent.height * 0.68)
                height: parent.height * 0.84
                portrait: frame.modelData
                progress: Math.max(0, frame.localTime / root.portraitMs)
                ink: root.ink
                layer.enabled: true
                layer.effect: MultiEffect {
                    shadowEnabled: true
                    shadowColor: root.ink
                    shadowBlur: 0.65
                    shadowOpacity: 0.32
                    shadowHorizontalOffset: 0
                    shadowVerticalOffset: 0
                }
            }
        }
    }
}
