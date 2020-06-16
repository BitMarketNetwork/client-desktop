import QtQuick 2.0
import QtQuick.Particles 2.0
import "../js/functions.js" as Funcs

Rectangle {
    id: _base
    width: 360
    height: 540
    color: "black"

    ParticleSystem {
        id: _part
        anchors.fill: parent

        ImageParticle {
            id: _smoke
            system: _part
            anchors.fill: parent
            groups: ["A", "B"]
            source: Funcs.loadImage("glowdot.png")
            colorVariation: 0
            color: "#00111111"
        }
        ImageParticle {
            id: _flame
            anchors.fill: parent
            system: _part
            groups: ["C", "D"]
            source: Funcs.loadImage("glowdot.png")
            colorVariation: 0.1
            color: "#00ff400f"
        }

        Emitter {
            id: _fire
            system: _part
            group: "C"

            y: parent.height
            width: parent.width

            emitRate: 350
            lifeSpan: 3500

            acceleration: PointDirection { y: -17; xVariation: 3 }
            velocity: PointDirection {xVariation: 3}

            size: 24
            sizeVariation: 8
            endSize: 4
        }

        TrailEmitter {
            id: _fsmoke
            group: "B"
            system: _part
            follow: "C"
            width: _base.width
            height: _base.height - 68

            emitRatePerParticle: 1
            lifeSpan: 2000

            velocity: PointDirection {y:-17*6; yVariation: -17; xVariation: 3}
            acceleration: PointDirection {xVariation: 3}

            size: 36
            sizeVariation: 8
            endSize: 16
        }

        TrailEmitter {
            id: _ball
            anchors.fill: parent
            system: _part
            group: "D"
            follow: "E"

            emitRatePerParticle: 120
            lifeSpan: 180
            emitWidth: TrailEmitter.ParticleSize
            emitHeight: TrailEmitter.ParticleSize
            emitShape: EllipseShape{}

            size: 16
            sizeVariation: 4
            endSize: 4
        }

        TrailEmitter {
            id: _fbsmoke
            anchors.fill: parent
            system: _part
            group: "A"
            follow: "E"

            emitRatePerParticle: 128
            lifeSpan: 2400
            emitWidth: TrailEmitter.ParticleSize
            emitHeight: TrailEmitter.ParticleSize
            emitShape: EllipseShape{}

            velocity: PointDirection {yVariation: 16; xVariation: 16}
            acceleration: PointDirection {y: -16}

            size: 24
            sizeVariation: 8
            endSize: 8
        }

        Emitter {
            id: _balls
            system: _part
            group: "E"

            y: parent.height
            width: parent.width

            emitRate: 2
            lifeSpan: 7000

            velocity: PointDirection {y:-17*4*2; xVariation: 6*6}
            acceleration: PointDirection {y: 17*2; xVariation: 6*6}

            size: 8
            sizeVariation: 4
        }

        Turbulence { //A bit of turbulence makes the smoke look better
            anchors.fill: parent
            groups: ["A","B"]
            strength: 32
            system: _part
        }
    }
}

