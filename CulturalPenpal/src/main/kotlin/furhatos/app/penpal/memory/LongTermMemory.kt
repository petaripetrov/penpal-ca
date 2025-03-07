package furhatos.app.penpal.memory

class LongTermMemory {
    private val userPreferences = mutableMapOf<String, Any>()
    private val learningProgress = mutableMapOf<String, Float>()

    fun updatePreference(key: String, value: Any) {
        userPreferences[key] = value
    }

    fun updateProgress(topic: String, score: Float) {
        learningProgress[topic] = score
    }

    fun getPreference(key: String): Any? {
        return userPreferences[key]
    }

    fun getProgress(topic: String): Float {
        return learningProgress[topic] ?: 0.0f
    }
}