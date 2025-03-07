package furhatos.app.penpal.memory

import furhatos.app.penpal.util.*

class TripleStore {
    private val subjects = mutableMapOf<String, MutableList<Triple>>()
    private val predicates = mutableMapOf<String, MutableList<Triple>>()
    private val objects = mutableMapOf<String, MutableList<Triple>>()

    fun add(triple: Triple) {
        subjects.getOrPut(triple.subject) { mutableListOf() }.add(triple)
        predicates.getOrPut(triple.predicate) { mutableListOf() }.add(triple)
        objects.getOrPut(triple.`object`) { mutableListOf() }.add(triple)
    }

    fun queryBySubject(subject: String): List<Triple> {
        return subjects[subject] ?: listOf()
    }

    fun queryByPredicate(predicate: String): List<Triple> {
        return predicates[predicate] ?: listOf()
    }

    fun queryByObject(`object`: String): List<Triple> {
        return objects[`object`] ?: listOf()
    }

    fun query(subject: String?, predicate: String?, `object`: String?): List<Triple> {
        val candidates = when {
            subject != null -> queryBySubject(subject)
            predicate != null -> queryByPredicate(predicate)
            `object` != null -> queryByObject(`object`)
            else -> return listOf()
        }

        return candidates.filter { triple ->
            (subject == null || triple.subject == subject) &&
                    (predicate == null || triple.predicate == predicate) &&
                    (`object` == null || triple.`object` == `object`)
        }
    }
}