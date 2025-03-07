package furhatos.app.penpal

import furhatos.app.penpal.flow.Init
import furhatos.app.penpal.memory.HybridMemorySystem
import furhatos.app.penpal.memory.EpisodicMemory
import furhatos.app.penpal.memory.SemanticMemory
import furhatos.app.penpal.memory.ShortTermMemory
import furhatos.app.penpal.memory.LongTermMemory
import furhatos.skills.Skill
import furhatos.flow.kotlin.Flow

class PenPalSkill : Skill() {
    override fun start() {
        Flow().run(Init)
    }

    companion object {
        // Initialize the memory system
        val memorySystem = HybridMemorySystem(
            EpisodicMemory(),
            SemanticMemory(),
            ShortTermMemory(),
            LongTermMemory()
        )
    }
}

fun main(args: Array<String>) {
    PenPalSkill().start()
}