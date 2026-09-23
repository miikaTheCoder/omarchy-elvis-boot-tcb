import QtQuick
import QtQuick.Shapes

Item {
    id: root
    required property var portrait
    property real progress: 1
    property color ink: "#fff0d5"
    readonly property real fit: Math.min(width / portrait.viewBox[2], height / portrait.viewBox[3])

    Item {
        x: (root.width - root.portrait.viewBox[2] * root.fit) / 2
        y: (root.height - root.portrait.viewBox[3] * root.fit) / 2
        scale: root.fit
        transformOrigin: Item.TopLeft
        Item {
            x: -root.portrait.viewBox[0]
            y: -root.portrait.viewBox[1]
            Repeater {
                model: root.portrait.strokes
                Shape {
                    required property var modelData
                    preferredRendererType: Shape.CurveRenderer
                    ShapePath {
                        strokeColor: root.ink
                        strokeWidth: modelData.width * 1.2
                        fillColor: "transparent"
                        capStyle: ShapePath.RoundCap
                        joinStyle: ShapePath.RoundJoin
                        trim.start: 0
                        trim.end: Math.max(0, Math.min(1, (root.progress - modelData.delay) / modelData.duration))
                        PathSvg { path: modelData.d }
                    }
                }
            }
        }
    }
}
