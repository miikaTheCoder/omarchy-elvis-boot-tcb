import QtQuick
import Quickshell
import "plugin/nextg.elvis-unlock" as Elvis

ShellRoot {
    id: root
    property int stage: 0
    property int failures: 0
    QtObject { id: lock; property bool locked: false }
    QtObject { id: mockShell; function serviceFor(id) { return lock } }
    Elvis.Service { id: service; shell: mockShell; portraitMs: 40; bootStatePath: "" }
    Elvis.Service { id: tcbOnlyService; shell: null; portraitMs: 40; bootStatePath: "" }
    function check(condition, description) {
        console.log((condition ? "PASS " : "FAIL ") + description)
        if (!condition) failures++
    }
    Timer {
        interval: 40
        repeat: true
        running: true
        onTriggered: {
            root.stage++
            if (root.stage === 1) {
                root.check(!service.playing, "No animation on plugin load")
                root.check(tcbOnlyService.playMode("tcb"), "TCB works without privileged lock-service access")
                tcbOnlyService.stop()
                root.check(!tcbOnlyService.play(), "Unlock portraits still require lock-service access")
                lock.locked = true
                root.check(!service.play(), "Manual preview refused while locked")
                lock.locked = false
                lock.locked = true
            } else if (root.stage === 5) {
                root.check(!service.playing, "Relock cancels a pending unlock animation")
                lock.locked = false
            } else if (root.stage === 9) {
                root.check(service.playing, "An observed unlock starts the sequence")
                lock.locked = true
                root.check(!service.playing, "Relock immediately removes the overlay")
                lock.locked = false
            } else if (root.stage === 26) {
                root.check(!service.playing, "Sequence ends and releases its windows")
                service.shell = null
                service.shell = mockShell
                root.check(!service.playing, "Rebinding an unlocked service does not replay")
                console.log("RESULT " + root.failures + " failures")
                Qt.quit()
            }
        }
    }
}
