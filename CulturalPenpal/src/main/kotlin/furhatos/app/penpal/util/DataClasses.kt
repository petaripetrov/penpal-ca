package furhatos.app.penpal.util

import furhatos.app.penpal.PenPalSkill

data class EpisodicEvent(
    val timestamp: Long,
    val userInput: String,
    val agentResponse: String,
    val eventType: EventType,
    val metadata: Map<String, Any> = mapOf()
) {
    fun calculateRelevance(context: String): Float {
        // Implement vector similarity between context and event
        return 0.0f // Replace with actual implementation
    }
}

enum class EventType {
    GRAMMAR_MISTAKE,
    VOCABULARY_LEARNING,
    CULTURAL_INSIGHT,
    ACHIEVEMENT,
    PREFERENCE_CHANGE
}

data class DialogueTurn(
    val userInput: String,
    val agentResponse: String,
    val timestamp: Long = System.currentTimeMillis()
)

data class Triple(
    val subject: String,
    val predicate: String,
    val `object`: String
)

class KnowledgeGraph {
    private val triples = mutableListOf<Triple>()

    fun addTriple(subject: String, predicate: String, `object`: String) {
        triples.add(Triple(subject, predicate, `object`))
    }

    fun query(subject: String?, predicate: String?, `object`: String?): List<Triple> {
        return triples.filter { triple ->
            (subject == null || triple.subject == subject) &&
                    (predicate == null || triple.predicate == predicate) &&
                    (`object` == null || triple.`object` == `object`)
        }
    }
}

private fun loadUserData(userId: String): UserData? {
    // First check if we have cached data for this user
    PenPalSkill.memorySystem.getUserMemory(userId)?.let { return it }

    // Otherwise, try to load from persistent storage
    return try {
        PenPalSkill.memorySystem.loadUserMemory(userId)
    } catch (e: Exception) {
        // If no data exists or there's an error, return null
        null
    }
}

/**
 * Data class to represent user state
 */
data class UserData(
    var name: String? = null,
    var currentLanguage: String? = null,
    var proficiencyLevel: String? = null,
    var interests: List<String> = listOf(),
    var culturalInterests: MutableList<String> = mutableListOf(),
    var sessionStartTime: Long? = null,
    var currentFocus: String? = null,
    var proficiencyScores: Map<String, Int> = mapOf(),
    var difficultyAdjustments: Map<String, Int> = mapOf(),
    var currentVocabularySet: List<VocabularyItem> = listOf(),
    var currentGrammarExercises: List<GrammarExercise> = listOf(),
    var currentConversationTopics: List<ConversationTopic> = listOf(),
    var currentCulturalTopics: List<CulturalTopic> = listOf(),
    var conversationExchangeCount: Int = 0
)

/**
 * Data models for content
 */
data class VocabularyItem(
    val term: String,
    val definition: String,
    val exampleSentence: String,
    val difficulty: String
)

data class GrammarExercise(
    val grammarPoint: String,
    val example: String,
    val prompt: String,
    val correctResponse: String,
    val difficulty: String
)

data class ConversationTopic(
    val topic: String,
    val openingQuestion: String,
    val followUpQuestions: Map<String, List<String>> = mapOf(
        "beginner" to listOf(),
        "intermediate" to listOf(),
        "advanced" to listOf()
    )
) {
    fun getFollowUpQuestion(proficiencyLevel: String, userResponse: String): String {
        val questions = followUpQuestions[proficiencyLevel] ?: followUpQuestions["beginner"] ?: listOf()
        return if (questions.isNotEmpty()) questions.random() else "Can you tell me more about that?"
    }
}

data class CulturalTopic(
    val title: String,
    val category: String,
    val fact: String,
    val additionalInfo: String
)
