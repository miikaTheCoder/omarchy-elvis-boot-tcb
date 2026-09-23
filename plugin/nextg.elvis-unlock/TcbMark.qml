import QtQuick
import QtQuick.Shapes
import "TcbArt.js" as Art

Item {
    id: root
    property real elapsed: 1600
    readonly property real fit: Math.min(width / 420, height / 750)
    readonly property real boltDraw: Math.max(0, Math.min(1, elapsed / 420))
    readonly property real letterDraw: Math.max(0, Math.min(1, (elapsed - 170) / 540))
    readonly property real solid: Math.max(0, Math.min(1, (elapsed - 460) / 360))

    Item {
        x: (root.width - 420 * root.fit) / 2
        y: (root.height - 750 * root.fit) / 2
        scale: root.fit
        transformOrigin: Item.TopLeft

        // The bolt arrives first as a hot gold outline.
        Shape {
            preferredRendererType: Shape.CurveRenderer
            ShapePath {
                strokeColor: "#ffeab3"
                strokeWidth: 2.1
                fillColor: "transparent"
                joinStyle: ShapePath.MiterJoin
                trim.end: root.boltDraw
                PathSvg { path: Art.bolt }
            }
        }
        Repeater {
            model: Art.letters
            Shape {
                required property string modelData
                preferredRendererType: Shape.CurveRenderer
                ShapePath {
                    strokeColor: "#f2d18d"
                    strokeWidth: 1.6
                    fillColor: "transparent"
                    trim.end: root.letterDraw
                    PathSvg { path: modelData }
                }
            }
        }

        Item {
            opacity: root.solid
            Repeater {
                model: [Art.bolt].concat(Art.letters)
                Shape {
                    required property string modelData
                    preferredRendererType: Shape.CurveRenderer
                    ShapePath {
                        strokeWidth: 0.7
                        strokeColor: "#e7c37b"
                        fillRule: ShapePath.OddEvenFill
                        fillGradient: LinearGradient {
                            x1: 90; y1: 15; x2: 350; y2: 580
                            GradientStop { position: 0; color: "#775522" }
                            GradientStop { position: 0.16; color: "#e8cc87" }
                            GradientStop { position: 0.29; color: "#fff0be" }
                            GradientStop { position: 0.38; color: "#a67b36" }
                            GradientStop { position: 0.59; color: "#e5c17a" }
                            GradientStop { position: 0.74; color: "#75521f" }
                            GradientStop { position: 1; color: "#d8b56e" }
                        }
                        PathSvg { path: modelData }
                    }
                }
            }
            Repeater {
                model: Art.bevels
                Shape {
                    required property var modelData
                    opacity: modelData.light ? 0.55 : 0.4
                    preferredRendererType: Shape.CurveRenderer
                    ShapePath {
                        strokeWidth: -1
                        fillColor: modelData.light ? "#fff1bd" : "#3c2914"
                        PathSvg { path: modelData.d }
                    }
                }
            }
            Repeater {
                model: Art.highlights
                Shape {
                    required property string modelData
                    opacity: 0.65
                    preferredRendererType: Shape.CurveRenderer
                    ShapePath {
                        strokeWidth: 1.3
                        strokeColor: "#fff3c7"
                        fillColor: "transparent"
                        PathSvg { path: modelData }
                    }
                }
            }
        }
    }
}
