import QtQuick
import Quickshell
import Quickshell.Io
import "plugin/nextg.elvis-unlock" as Elvis

ShellRoot {
    id: root
    property real elapsed: 0
    property bool tcb: false
    property int exportWidth: 1920
    property int exportHeight: 1080
    Component {
        id: portraitScene
        Elvis.Sequence { elapsed: root.elapsed; dimDesktop: false }
    }
    Component {
        id: bootScene
        Elvis.BootSequence { elapsed: root.elapsed; dimDesktop: false }
    }
    FloatingWindow {
        id: window
        title: "Elvis · The Prime Years — preview"
        implicitWidth: 1100
        implicitHeight: 720
        color: "#080a0e"
        Rectangle {
            id: canvas
            anchors.fill: parent
            color: "#080a0e"
            Loader {
                anchors.fill: parent
                sourceComponent: root.tcb ? bootScene : portraitScene
            }
        }
        // Native export layout, independent of window tiling and resizing.
        Rectangle {
            id: exportCanvas
            x: window.width + 64
            width: root.exportWidth
            height: root.exportHeight
            color: "#080a0e"
            Loader {
                anchors.fill: parent
                sourceComponent: root.tcb ? bootScene : portraitScene
            }
        }
        MouseArea { anchors.fill: parent; onClicked: animation.restart() }
    }
    NumberAnimation {
        id: animation
        target: root
        property: "elapsed"
        from: 0
        to: root.tcb ? 2350 : 3350
        duration: root.tcb ? 2350 : 3350
    }
    IpcHandler {
        target: "preview"
        function play(): void { animation.restart() }
        function mode(name: string): void { animation.stop(); root.tcb = name === "tcb"; root.elapsed = 0 }
        function frame(time: real): void { animation.stop(); root.elapsed = time }
        function capture(path: string): void {
            canvas.grabToImage(function(result) { result.saveToFile(path) })
        }
        function exportSize(width: int, height: int): string {
            if (width < 320 || height < 240 || width > 7680 || height > 4320) return "invalid size"
            root.exportWidth = width
            root.exportHeight = height
            return "ok"
        }
        function exportFrame(time: real, path: string): void {
            animation.stop()
            root.elapsed = time
            Qt.callLater(function() {
                exportCanvas.grabToImage(function(result) { result.saveToFile(path) },
                    Qt.size(root.exportWidth, root.exportHeight))
            })
        }
        function quit(): void { Qt.quit() }
    }
    Component.onCompleted: animation.start()
}
