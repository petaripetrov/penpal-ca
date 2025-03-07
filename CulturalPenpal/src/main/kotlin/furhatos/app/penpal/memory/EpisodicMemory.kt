package furhatos.app.penpal.memory
import furhatos.app.penpal.util.*

class EpisodicMemory {
    private val memories = mutableListOf<EpisodicEvent>()

    fun addMemory(event: EpisodicEvent) {
        memories.add(event)
    }

    fun retrieveRelevantMemories(context: String, limit: Int = 5): List<EpisodicEvent> {
        // Implement vector search to find relevant memories
        return memories.sortedByDescending { it.calculateRelevance(context) }.take(limit)
    }
}