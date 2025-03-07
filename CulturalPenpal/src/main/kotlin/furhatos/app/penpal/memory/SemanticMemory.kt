package furhatos.app.penpal.memory

import furhatos.app.penpal.util.*

class SemanticMemory {
    private val knowledgeGraph = KnowledgeGraph()

    fun addFact(subject: String, predicate: String, objectValue: String) {
        knowledgeGraph.addTriple(subject, predicate, objectValue)
    }

    fun queryFacts(subject: String?, predicate: String?, objectValue: String?): List<Triple> {
        return knowledgeGraph.query(subject, predicate, objectValue)
    }
}