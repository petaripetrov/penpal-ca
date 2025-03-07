package furhatos.app.penpal

import furhatos.app.penpal.flow.Init
import furhatos.skills.Skill
import furhatos.flow.kotlin.Flow

class PenPalSkill : Skill() {
    override fun start() {
        Flow().run(Init)
    }
}

fun main(args: Array<String>) {
    PenPalSkill().start()
}