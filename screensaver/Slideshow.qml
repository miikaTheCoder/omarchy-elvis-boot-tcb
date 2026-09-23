import QtQuick

Item {
    id: root
    required property var photos
    property int current: 0
    property real blend: 0

    // Decode the three originals once. No blur, crops, filters, or video encoding.
    Repeater {
        model: root.photos
        Image {
            required property int index
            required property var modelData
            anchors.fill: parent
            source: modelData
            fillMode: Image.PreserveAspectFit
            smooth: true
            asynchronous: true
            cache: true
            readonly property bool incoming: index === (root.current + 1) % root.photos.length
            z: incoming ? 1 : 0
            opacity: index === root.current ? 1 : (incoming ? root.blend : 0)
        }
    }
}
