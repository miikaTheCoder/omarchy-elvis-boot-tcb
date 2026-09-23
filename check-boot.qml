import QtQuick
import Quickshell
import Quickshell.Io
import "plugin/nextg.elvis-unlock" as Elvis

ShellRoot {
    id: root
    readonly property string fixturePath: Quickshell.env("ELVIS_TEST_BOOT_STATE") || ""
    property int stage: 0
    property int failures: 0
    QtObject { id: lock; property bool locked: true }
    QtObject { id: mockShell; function serviceFor(id) { return lock } }
    Loader {
        id: serviceLoader
        sourceComponent: Elvis.Service {
            shell: mockShell
            portraitMs: 1000
            bootStatePath: root.fixturePath
        }
    }
    FileView {
        id: fixture
        path: root.fixturePath
        printErrors: false
        onSaved: { if (serviceLoader.item) serviceLoader.item.reloadBootRequest() }
    }
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
            var service = serviceLoader.item
            if (root.stage === 1) {
                if (!root.fixturePath.startsWith("/tmp/")) throw new Error("Test needs a /tmp/ fixture")
                root.check(!service.playing && !service.bootPending, "No TCB without a startup request")
                fixture.setText("pending\n")
            } else if (root.stage === 8) {
                root.check(service.bootPending && !service.playing, "Startup request waits while locked")
                serviceLoader.active = false
            } else if (root.stage === 9) {
                serviceLoader.active = true
            } else if (root.stage === 16) {
                root.check(service.bootPending && !service.playing, "Pending startup survives a service restart")
                lock.locked = false
            } else if (root.stage === 24) {
                root.check(service.playing && service.sequence === "tcb", "First unlock after locked startup plays TCB")
                root.check(service.bootConsumed && !service.bootPending, "Startup request consumed before playback")
                root.check(!service.tryBoot(), "Duplicate startup trigger cannot replay TCB")
                lock.locked = true
                root.check(!service.playing, "Relocking cancels TCB")
                lock.locked = false
            } else if (root.stage === 32) {
                root.check(service.playing && service.sequence === "portraits", "Subsequent unlock plays only Elvis portraits")
                service.stop()
                serviceLoader.active = false
            } else if (root.stage === 33) {
                serviceLoader.active = true
            } else if (root.stage === 41) {
                root.check(service.bootConsumed && !service.playing, "Consumed marker survives a service restart")
                service.reloadBootRequest()
            } else if (root.stage === 49) {
                root.check(!service.playing, "Repeated post-boot notification stays quiet")
                console.log("RESULT " + root.failures + " failures")
                Qt.quit()
            }
        }
    }
}
