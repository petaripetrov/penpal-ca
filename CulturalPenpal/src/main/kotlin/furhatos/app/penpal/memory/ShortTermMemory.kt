package furhatos.app.penpal.memory

class ShortTermMemory {
    private val recentTurns = mutableListOf<DialogueTurn>()
    private val maxTurns = 10

    fun addTurn(turn: DialogueTurn) {
        recentTurns.add(turn)
        if (recentTurns.size > maxTurns) {
            recentTurns.removeAt(0)
        }
    }

    fun getRecentTurns(): List<DialogueTurn> {
        return recentTurns.toList()
    }
}