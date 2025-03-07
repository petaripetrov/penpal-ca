package furhatos.app.penpal.flow

import furhatos.app.penpal.PenPalSkill
import furhatos.app.penpal.nlu.*
import furhatos.app.penpal.util.DialogueTurn
import furhatos.flow.kotlin.*
import furhatos.nlu.common.*

val LearningFocus: State = state(Parent) {
    onEntry {
        // Already asked about focus in the previous state
    }

    onResponse<FocusIntent> {
        val focus = it.intent.focus

        // Update user data with selected focus
        val userData = users.current.get("userData")
        userData?.currentFocus = focus
        users.current.put("userData", userData)

        // Store this turn in short-term memory
        PenPalSkill.memorySystem.shortTermMemory.addTurn(
            DialogueTurn(
                userInput = it.text,
                agentResponse = "Great! Let's focus on $focus."
            )
        )

        furhat.say("Great! Let's focus on $focus.")

        // Route to the appropriate practice session based on focus
        when (focus.toLowerCase()) {
            "vocabulary" -> goto(VocabularyPractice)
            "grammar" -> goto(GrammarPractice)
            "conversation" -> goto(ConversationPractice)
            "culture" -> goto(CulturalExploration)
            else -> {
                furhat.say("I'm not sure I understand that focus. Let's try vocabulary practice.")
                goto(VocabularyPractice)
            }
        }
    }

    onResponse {
        furhat.say("I'm not sure I understood your preference. Would you like to focus on vocabulary, grammar, conversation, or cultural aspects?")
        reentry()
    }
}

val VocabularyPractice: State = state(Parent) {
    onEntry {
        val userData = users.current.get("userData")
        val language = userData?.currentLanguage ?: "English"
        val name = userData?.name ?: "there"

        // Log this activity in the memory system
        PenPalSkill.memorySystem.episodicMemory.addMemory(
            timestamp = System.currentTimeMillis(),
            userInput = "",
            agentResponse = "",
            eventType = "PRACTICE_START",
            metadata = mapOf(
                "language" to language,
                "focus" to "vocabulary"
            )
        )

        // Select vocabulary based on user proficiency level
        val proficiencyLevel = userData?.proficiencyLevel ?: "beginner"
        val vocabularySet = PenPalSkill.contentManager.getVocabularySet(language, proficiencyLevel)

        // Store current vocabulary set in user data for this session
        userData?.currentVocabularySet = vocabularySet
        users.current.put("userData", userData)

        furhat.say("Alright $name, let's improve your $language vocabulary! I'll introduce some words and you can practice using them.")

        // Start with the first vocabulary item
        if (vocabularySet.isNotEmpty()) {
            val firstWord = vocabularySet.first()
            furhat.say("Let's start with the word: ${firstWord.term}. It means: ${firstWord.definition}")
            furhat.ask("Can you use this word in a sentence?")
        } else {
            furhat.say("It seems I don't have vocabulary prepared for your level. Let's try something else.")
            goto(LearningFocus)
        }
    }

    onResponse {
        // Store user's practice attempt
        val userData = users.current.get("userData")
        val vocabularySet = userData?.currentVocabularySet

        if (vocabularySet?.isNotEmpty() == true) {
            PenPalSkill.memorySystem.shortTermMemory.addTurn(
                DialogueTurn(
                    userInput = it.text,
                    agentResponse = "Good attempt!",
                    metadata = mapOf(
                        "word" to (vocabularySet.first().term),
                        "usage_attempt" to it.text
                    )
                )
            )

            // Give feedback on usage
            furhat.say("Good attempt! Here's another way you could use it: ${vocabularySet.first().exampleSentence}")

            // Move to next word or wrap up
            if (vocabularySet.size > 1) {
                val nextWord = vocabularySet[1]
                userData?.currentVocabularySet = vocabularySet.drop(1)
                users.current.put("userData", userData)

                furhat.ask("Now let's try the word: ${nextWord.term}. It means: ${nextWord.definition}. Can you use this in a sentence?")
                reentry()
            } else {
                furhat.say("Great job with vocabulary practice! Would you like to continue with another focus area or end the session?")
                goto(PracticeFeedback)
            }
        } else {
            goto(PracticeFeedback)
        }
    }
}

val GrammarPractice: State = state(Parent) {
    onEntry {
        val userData = users.current.get("userData")
        val language = userData?.currentLanguage ?: "English"
        val name = userData?.name ?: "there"

        // Log this activity
        PenPalSkill.memorySystem.episodicMemory.addMemory(
            timestamp = System.currentTimeMillis(),
            userInput = "",
            agentResponse = "",
            eventType = "PRACTICE_START",
            metadata = mapOf(
                "language" to language,
                "focus" to "grammar"
            )
        )

        // Select grammar exercises based on proficiency
        val proficiencyLevel = userData?.proficiencyLevel ?: "beginner"
        val grammarExercises = PenPalSkill.contentManager.getGrammarExercises(language, proficiencyLevel)

        userData?.currentGrammarExercises = grammarExercises
        users.current.put("userData", userData)

        furhat.say("Let's work on your $language grammar, $name!")

        if (grammarExercises.isNotEmpty()) {
            val firstExercise = grammarExercises.first()
            furhat.say("We'll practice ${firstExercise.grammarPoint}.")
            furhat.say("Here's an example: ${firstExercise.example}")
            furhat.ask(firstExercise.prompt)
        } else {
            furhat.say("I don't have grammar exercises ready for your level. Let's try something else.")
            goto(LearningFocus)
        }
    }

    onResponse {
        val userData = users.current.get("userData")
        val grammarExercises = userData?.currentGrammarExercises

        if (grammarExercises?.isNotEmpty() == true) {
            val currentExercise = grammarExercises.first()

            // Record this practice attempt
            PenPalSkill.memorySystem.shortTermMemory.addTurn(
                DialogueTurn(
                    userInput = it.text,
                    agentResponse = "Let me give you feedback.",
                    metadata = mapOf(
                        "grammar_point" to currentExercise.grammarPoint,
                        "response" to it.text
                    )
                )
            )

            // Provide feedback (in a real system, this would analyze the response)
            furhat.say("That's a good try! The correct structure would be: ${currentExercise.correctResponse}")

            // Move to next exercise or wrap up
            if (grammarExercises.size > 1) {
                val nextExercise = grammarExercises[1]
                userData?.currentGrammarExercises = grammarExercises.drop(1)
                users.current.put("userData", userData)

                furhat.say("Now let's practice ${nextExercise.grammarPoint}.")
                furhat.say("Here's an example: ${nextExercise.example}")
                furhat.ask(nextExercise.prompt)
                reentry()
            } else {
                furhat.say("You've completed all the grammar exercises! Would you like to try another focus area?")
                goto(PracticeFeedback)
            }
        } else {
            goto(PracticeFeedback)
        }
    }
}

val ConversationPractice: State = state(Parent) {
    onEntry {
        val userData = users.current.get("userData")
        val language = userData?.currentLanguage ?: "English"
        val name = userData?.name ?: "there"

        // Log activity
        PenPalSkill.memorySystem.episodicMemory.addMemory(
            timestamp = System.currentTimeMillis(),
            userInput = "",
            agentResponse = "",
            eventType = "PRACTICE_START",
            metadata = mapOf(
                "language" to language,
                "focus" to "conversation"
            )
        )

        // Select conversation topics based on interests and proficiency
        val proficiencyLevel = userData?.proficiencyLevel ?: "beginner"
        val interests = userData?.interests ?: listOf("general")
        val conversationTopics = PenPalSkill.contentManager.getConversationTopics(language, proficiencyLevel, interests)

        userData?.currentConversationTopics = conversationTopics
        users.current.put("userData", userData)

        furhat.say("Let's practice having a conversation in $language, $name!")

        if (conversationTopics.isNotEmpty()) {
            val firstTopic = conversationTopics.first()
            furhat.say("Let's talk about ${firstTopic.topic}.")
            furhat.ask(firstTopic.openingQuestion)
        } else {
            furhat.say("I don't have conversation topics prepared. Let's try something else.")
            goto(LearningFocus)
        }
    }

    onResponse {
        val userData = users.current.get("userData")
        val conversationTopics = userData?.currentConversationTopics

        if (conversationTopics?.isNotEmpty() == true) {
            val currentTopic = conversationTopics.first()

            // Store this conversation turn
            PenPalSkill.memorySystem.shortTermMemory.addTurn(
                DialogueTurn(
                    userInput = it.text,
                    agentResponse = "",  // Will be filled after response selection
                    metadata = mapOf("topic" to currentTopic.topic)
                )
            )

            // Select appropriate follow-up question based on user's proficiency
            val proficiencyLevel = userData?.proficiencyLevel ?: "beginner"
            val followUpQuestion = currentTopic.getFollowUpQuestion(proficiencyLevel, it.text)

            // Update last response in memory
            val lastTurn = PenPalSkill.memorySystem.shortTermMemory.getLastTurn()
            lastTurn?.agentResponse = followUpQuestion

            furhat.ask(followUpQuestion)

            // After a few exchanges, move to next topic or wrap up
            val exchangeCount = userData?.conversationExchangeCount ?: 0
            userData?.conversationExchangeCount = exchangeCount + 1

            if (exchangeCount >= 3 && conversationTopics.size > 1) {
                // Reset exchange count and move to next topic
                userData?.conversationExchangeCount = 0
                userData?.currentConversationTopics = conversationTopics.drop(1)
                users.current.put("userData", userData)

                val nextTopic = conversationTopics[1]
                furhat.say("Let's change the subject.")
                furhat.ask("Let's talk about ${nextTopic.topic}. ${nextTopic.openingQuestion}")
            } else if (exchangeCount >= 3 && conversationTopics.size <= 1) {
                // We've completed all conversation topics
                furhat.say("You're doing great with conversation practice! Would you like to try another focus area?")
                goto(PracticeFeedback)
            } else {
                // Continue with current topic
                users.current.put("userData", userData)
                reentry()
            }
        } else {
            goto(PracticeFeedback)
        }
    }
}

val CulturalExploration: State = state(Parent) {
    onEntry {
        val userData = users.current.get("userData")
        val language = userData?.currentLanguage ?: "English"
        val name = userData?.name ?: "there"

        // Log activity
        PenPalSkill.memorySystem.episodicMemory.addMemory(
            timestamp = System.currentTimeMillis(),
            userInput = "",
            agentResponse = "",
            eventType = "PRACTICE_START",
            metadata = mapOf(
                "language" to language,
                "focus" to "culture"
            )
        )

        // Get cultural topics
        val culturalTopics = PenPalSkill.contentManager.getCulturalTopics(language)

        userData?.currentCulturalTopics = culturalTopics
        users.current.put("userData", userData)

        furhat.say("Let's explore $language culture, $name!")

        if (culturalTopics.isNotEmpty()) {
            val firstTopic = culturalTopics.first()
            furhat.say("Did you know: ${firstTopic.fact}")
            furhat.ask("What do you think about that? Or would you like to know more?")
        } else {
            furhat.say("I don't have cultural topics prepared. Let's try something else.")
            goto(LearningFocus)
        }
    }

    onResponse<RequestMoreInfoIntent> {
        val userData = users.current.get("userData")
        val culturalTopics = userData?.currentCulturalTopics

        if (culturalTopics?.isNotEmpty() == true) {
            val currentTopic = culturalTopics.first()

            // Store this interaction
            PenPalSkill.memorySystem.shortTermMemory.addTurn(
                DialogueTurn(
                    userInput = it.text,
                    agentResponse = currentTopic.additionalInfo,
                    metadata = mapOf("cultural_topic" to currentTopic.title)
                )
            )

            furhat.say(currentTopic.additionalInfo)
            furhat.ask("Would you like to learn about another cultural aspect?")
        } else {
            goto(PracticeFeedback)
        }
    }

    onResponse<YesIntent> {
        val userData = users.current.get("userData")
        val culturalTopics = userData?.currentCulturalTopics

        if (culturalTopics?.size ?: 0 > 1) {
            val nextTopic = culturalTopics?.get(1)

            userData?.currentCulturalTopics = culturalTopics?.drop(1)
            users.current.put("userData", userData)

            if (nextTopic != null) {
                furhat.say("Great! Here's something else interesting.")
                furhat.say("Did you know: ${nextTopic.fact}")
                furhat.ask("What do you think about that? Or would you like to know more?")
                reentry()
            } else {
                furhat.say("It seems I've shared all the cultural facts I have. Would you like to try another focus area?")
                goto(PracticeFeedback)
            }
        } else {
            furhat.say("It seems I've shared all the cultural facts I have. Would you like to try another focus area?")
            goto(PracticeFeedback)
        }
    }

    onResponse<NoIntent> {
        furhat.say("No problem! Would you like to try another focus area?")
        goto(PracticeFeedback)
    }

    onResponse {
        // For any other response, treat it as a comment on the cultural fact
        PenPalSkill.memorySystem.shortTermMemory.addTurn(
            DialogueTurn(
                userInput = it.text,
                agentResponse = "Thank you for sharing your thoughts.",
                metadata = mapOf("interaction_type" to "cultural_discussion")
            )
        )

        // Store the user's interest in this cultural topic
        val userData = users.current.get("userData")
        val culturalTopics = userData?.currentCulturalTopics

        if (culturalTopics?.isNotEmpty() == true) {
            val currentTopic = culturalTopics.first()

            // Update user's cultural interests based on their response
            userData?.culturalInterests = (userData?.culturalInterests ?: mutableListOf()).apply {
                if (!contains(currentTopic.category)) {
                    add(currentTopic.category)
                }
            }

            users.current.put("userData", userData)

            // Provide more information and move to next topic
            furhat.say("Thank you for sharing your thoughts. ${currentTopic.additionalInfo}")
            furhat.ask("Would you like to learn about another cultural aspect?")
        } else {
            furhat.ask("Would you like to try another focus area?")
            goto(PracticeFeedback)
        }
    }
}

val PracticeFeedback: State = state(Parent) {
    onEntry {
        val userData = users.current.get("userData")
        val focus = userData?.currentFocus ?: "practice"

        // Record practice session completion
        PenPalSkill.memorySystem.episodicMemory.addMemory(
            timestamp = System.currentTimeMillis(),
            userInput = "",
            agentResponse = "",
            eventType = "PRACTICE_COMPLETE",
            metadata = mapOf("focus" to focus)
        )

        furhat.ask("How was your $focus practice? Do you feel like you've learned something new?")
    }

    onResponse<PositiveFeedbackIntent> {
        // Record positive feedback
        PenPalSkill.memorySystem.shortTermMemory.addTurn(
            DialogueTurn(
                userInput = it.text,
                agentResponse = "I'm glad to hear that!",
                metadata = mapOf("feedback" to "positive")
            )
        )

        // Update user proficiency metrics based on positive feedback
        val userData = users.current.get("userData")
        val focus = userData?.currentFocus

        if (focus != null) {
            // Increment proficiency score for this focus area
            userData.proficiencyScores = userData.proficiencyScores.toMutableMap().apply {
                val currentScore = get(focus) ?: 0
                put(focus, currentScore + 1)
            }
            users.current.put("userData", userData)
        }

        furhat.say("I'm glad to hear that! Would you like to continue with another focus area or end this session?")
    }

    onResponse<NegativeFeedbackIntent> {
        // Record negative feedback
        PenPalSkill.memorySystem.shortTermMemory.addTurn(
            DialogueTurn(
                userInput = it.text,
                agentResponse = "I'm sorry to hear that.",
                metadata = mapOf("feedback" to "negative")
            )
        )

        // Update difficulty adjustment for this user
        val userData = users.current.get("userData")
        val focus = userData?.currentFocus

        if (focus != null) {
            // Adjust difficulty level down for this focus area
            userData.difficultyAdjustments = userData.difficultyAdjustments.toMutableMap().apply {
                val currentAdjustment = get(focus) ?: 0
                put(focus, currentAdjustment - 1)
            }
            users.current.put("userData", userData)
        }

        furhat.say("I'm sorry to hear that. I'll try to adjust the difficulty level for next time. Would you like to try another focus area or end this session?")
    }

    onResponse<ContinuePracticeIntent> {
        furhat.say("Great! Let's continue learning.")
        goto(LearningFocus)
    }

    onResponse<EndSessionIntent> {
        furhat.say("Alright, let's wrap up for today.")
        goto(EndSession)
    }

    onResponse {
        // For any other response, ask more specifically
        furhat.ask("Would you like to continue with another focus area or end this session?")
        reentry()
    }
}

val EndSession: State = state(Parent) {
    onEntry {
        val userData = users.current.get("userData")
        val name = userData?.name ?: "there"

        // Create an episodic memory of this session
        val language = userData?.currentLanguage
        val focus = userData?.currentFocus

        if (language != null && focus != null) {
            PenPalSkill.memorySystem.episodicMemory.addMemory(
                timestamp = System.currentTimeMillis(),
                userInput = "",
                agentResponse = "",
                eventType = "SESSION_END",
                metadata = mapOf(
                    "language" to language,
                    "focus" to focus,
                    "duration" to (System.currentTimeMillis() - (userData.sessionStartTime ?: 0))
                )
            )
        }

        // Store session data in long-term memory
        PenPalSkill.memorySystem.longTermMemory.updateSessionData(userData)

        // Calculate progress statistics
        val progressStats = calculateUserProgress(userData)

        // Save user memory data
        val userId = users.current.id
        PenPalSkill.memorySystem.persistUserMemory(userId)

        // Give personalized feedback based on session
        when (focus?.toLowerCase()) {
            "vocabulary" -> {
                furhat.say("You've worked on ${progressStats.wordsLearned} new vocabulary words today, $name.")
                if (progressStats.wordsLearned > 5) {
                    furhat.say("That's excellent progress!")
                } else {
                    furhat.say("Keep practicing and you'll build your vocabulary quickly.")
                }
            }
            "grammar" -> {
                furhat.say("You've completed ${progressStats.exercisesCompleted} grammar exercises today, $name.")
                if (progressStats.correctResponses > progressStats.exercisesCompleted * 0.7) {
                    furhat.say("Your grammar is really improving!")
                } else {
                    furhat.say("With more practice, these grammar points will become natural for you.")
                }
            }
            "conversation" -> {
                furhat.say("We had a nice conversation in ${language ?: "your target language"} today, $name.")
                furhat.say("Regular speaking practice is key to language fluency.")
            }
            "culture" -> {
                furhat.say("I hope you enjoyed learning about ${language ?: "target language"} culture today, $name.")
                furhat.say("Understanding culture is an important part of mastering a language.")
            }
            else -> {
                furhat.say("Thanks for practicing with me today, $name!")
            }
        }

        // Suggest focus for next time based on user data
        val suggestedFocus = getSuggestedFocus(userData)
        if (suggestedFocus != null && suggestedFocus != focus) {
            furhat.say("Next time, we might want to focus on $suggestedFocus to balance your language skills.")
        }

        // Final goodbye
        furhat.say("I've saved your progress, and we can continue next time. Have a great day!")

        // Reset session state
        goto(Idle)
    }
}

/**
 * Helper function to calculate user progress statistics
 */
private fun calculateUserProgress(userData: UserData?): ProgressStats {
    if (userData == null) return ProgressStats()

    // Calculate statistics based on session data in short-term memory
    val sessionTurns = PenPalSkill.memorySystem.shortTermMemory.getAllTurns()

    val wordsLearned = sessionTurns.count { it.metadata?.get("word") != null }
    val exercisesCompleted = sessionTurns.count { it.metadata?.get("grammar_point") != null }

    // Approximate correct responses by counting turns that received positive feedback
    val correctResponses = sessionTurns.count {
        val response = it.agentResponse.toLowerCase()
        response.contains("good") || response.contains("correct") || response.contains("excellent")
    }

    // Calculate conversation turns
    val conversationTurns = sessionTurns.count { it.metadata?.get("topic") != null }

    return ProgressStats(
        wordsLearned = wordsLearned,
        exercisesCompleted = exercisesCompleted,
        correctResponses = correctResponses,
        conversationTurns = conversationTurns
    )
}

/**
 * Helper function to suggest next focus area based on user data
 */
private fun getSuggestedFocus(userData: UserData?): String? {
    if (userData == null) return null

    // Get proficiency scores for different focus areas
    val scores = userData.proficiencyScores
    if (scores.isEmpty()) return null

    // Find the area with lowest proficiency score
    val weakestArea = scores.entries.minByOrNull { it.value }?.key

    // If user hasn't practiced an area yet, suggest that
    val focusOptions = listOf("vocabulary", "grammar", "conversation", "culture")
    val unpracticedAreas = focusOptions.filter { !scores.containsKey(it) }

    return if (unpracticedAreas.isNotEmpty()) {
        unpracticedAreas.random()
    } else {
        weakestArea
    }
}

/**
 * Data class to track user progress statistics
 */
data class ProgressStats(
    val wordsLearned: Int = 0,
    val exercisesCompleted: Int = 0,
    val correctResponses: Int = 0,
    val conversationTurns: Int = 0
)

/**
 * Idle state to wait for new users
 */
val Idle: State = state {
    onEntry {
        furhat.attend(users.random)
        if (users.count > 0) {
            furhat.ask("Would you like to practice a language with me?")
        }
    }

    onResponse<YesIntent> {
        goto(LanguageSelection)
    }

    onResponse<NoIntent> {
        furhat.say("No problem. Let me know if you change your mind.")
        reentry()
    }

    onUserEnter {
        furhat.attend(it)
        val userData = loadUserData(it.id)
        it.put("userData", userData)

        if (userData != null && userData.name != null) {
            // Returning user
            furhat.say("Welcome back, ${userData.name}! Would you like to continue practicing ${userData.currentLanguage}?")
        } else {
            // New user
            furhat.ask("Hello! I'm your language learning assistant. Would you like to practice a language with me?")
        }
    }

    onUserLeave {
        if (users.count > 0) {
            furhat.attend(users.random)
        } else {
            furhat.attendNobody()
        }
    }
}

/**
 * Language selection state
 */
val LanguageSelection: State = state(Parent) {
    onEntry {
        val userData = users.current.get("userData")

        if (userData?.currentLanguage != null) {
            // User already has a language preference
            furhat.ask("Would you like to continue with ${userData.currentLanguage}, or try a different language?")
        } else {
            // New language selection
            furhat.ask("Which language would you like to practice? I can help with English, Spanish, French, German, and Japanese.")
        }
    }

    onResponse<LanguageSelectionIntent> {
        val language = it.intent.language
        val userData = users.current.get("userData") ?: UserData()

        // Update user data with selected language
        userData.currentLanguage = language
        userData.sessionStartTime = System.currentTimeMillis()
        users.current.put("userData", userData)

        // Store this turn in short-term memory
        PenPalSkill.memorySystem.shortTermMemory.addTurn(
            DialogueTurn(
                userInput = it.text,
                agentResponse = "Great choice! Let's practice $language.",
                metadata = mapOf("language" to language)
            )
        )

        furhat.say("Great choice! Let's practice $language.")

        // If new user, get their name
        if (userData.name == null) {
            goto(UserIntroduction)
        } else {
            // For returning users, check proficiency
            if (userData.proficiencyLevel == null) {
                goto(ProficiencyCheck)
            } else {
                goto(LearningFocusIntroduction)
            }
        }
    }

    onResponse<ContinueWithCurrentLanguageIntent> {
        val userData = users.current.get("userData")
        val language = userData?.currentLanguage

        if (language != null) {
            furhat.say("Great! Let's continue with $language.")

            // Update session start time
            userData.sessionStartTime = System.currentTimeMillis()
            users.current.put("userData", userData)

            goto(LearningFocusIntroduction)
        } else {
            furhat.say("I'm not sure which language you've been learning. Let's start fresh.")
            furhat.ask("Which language would you like to practice?")
            reentry()
        }
    }

    onResponse {
        furhat.say("I didn't catch that. I can help you practice English, Spanish, French, German, or Japanese.")
        furhat.ask("Which would you like to try?")
        reentry()
    }
}

/**
 * User introduction state for new users
 */
val UserIntroduction: State = state(Parent) {
    onEntry {
        furhat.ask("Before we start, could you tell me your name?")
    }

    onResponse<NameIntent> {
        val name = it.intent.name
        val userData = users.current.get("userData") ?: UserData()

        // Update user data with name
        userData.name = name
        users.current.put("userData", userData)

        // Store this turn in short-term memory
        PenPalSkill.memorySystem.shortTermMemory.addTurn(
            DialogueTurn(
                userInput = it.text,
                agentResponse = "Nice to meet you, $name!",
                metadata = mapOf("user_name" to name)
            )
        )

        furhat.say("Nice to meet you, $name!")
        goto(ProficiencyCheck)
    }

    onResponse {
        // Try to extract a name from any response
        val possibleName = it.text.split(" ").firstOrNull { word ->
            word.length > 1 && word[0].isUpperCase()
        } ?: it.text.trim()

        val userData = users.current.get("userData") ?: UserData()
        userData.name = possibleName
        users.current.put("userData", userData)

        furhat.say("Nice to meet you! I'll call you $possibleName.")
        goto(ProficiencyCheck)
    }
}

/**
 * Proficiency check for language level - completed implementation
 */
val ProficiencyCheck: State = state(Parent) {
    onEntry {
        val userData = users.current.get("userData")
        val language = userData?.currentLanguage ?: "the language"

        furhat.ask("How would you rate your $language proficiency? Beginner, intermediate, or advanced?")
    }

    onResponse<ProficiencyIntent> {
        val proficiencyLevel = it.intent.level.toLowerCase()
        val userData = users.current.get("userData")

        // Update user data with proficiency level
        userData?.proficiencyLevel = proficiencyLevel
        users.current.put("userData", userData)

        // Store this turn in short-term memory
        PenPalSkill.memorySystem.shortTermMemory.addTurn(
            DialogueTurn(
                userInput = it.text,
                agentResponse = "I'll tailor the content to a $proficiencyLevel level.",
                metadata = mapOf("proficiency_level" to proficiencyLevel)
            )
        )

        furhat.say("I'll tailor the content to a $proficiencyLevel level.")
        goto(InterestCheck)
    }

    onResponse {
        // Try to determine proficiency level from any response
        val response = it.text.toLowerCase()
        val proficiencyLevel = when {
            response.contains("begin") || response.contains("basic") || response.contains("new") ||
                    response.contains("start") || response.contains("novice") -> "beginner"

            response.contains("intermedia") || response.contains("middle") ||
                    response.contains("some") || response.contains("okay") -> "intermediate"

            response.contains("advanc") || response.contains("fluent") ||
                    response.contains("proficient") || response.contains("expert") -> "advanced"

            else -> "beginner"  // Default to beginner if unclear
        }

        val userData = users.current.get("userData")
        userData?.proficiencyLevel = proficiencyLevel
        users.current.put("userData", userData)

        furhat.say("I'll tailor the content to a $proficiencyLevel level.")
        goto(InterestCheck)
    }
}

/**
 * Interest check to personalize content
 */
val InterestCheck: State = state(Parent) {
    onEntry {
        val userData = users.current.get("userData")
        val name = userData?.name ?: "there"

        furhat.ask("$name, what topics are you interested in? For example: travel, food, music, business, technology, or sports?")
    }

    onResponse<InterestsIntent> {
        val interestList = it.intent.interests
        val userData = users.current.get("userData")

        // Update user data with interests
        userData?.interests = interestList
        users.current.put("userData", userData)

        // Store this turn in short-term memory
        PenPalSkill.memorySystem.shortTermMemory.addTurn(
            DialogueTurn(
                userInput = it.text,
                agentResponse = "Great! I'll include content about ${interestList.joinToString(", ")}.",
                metadata = mapOf("interests" to interestList.joinToString(","))
            )
        )

        furhat.say("Great! I'll include content about ${interestList.joinToString(", ")}.")
        goto(LearningFocusIntroduction)
    }

    onResponse {
        // Extract potential interests from any response
        val response = it.text.toLowerCase()
        val possibleInterests = listOf(
            "travel", "food", "music", "business", "technology", "sports",
            "movies", "books", "art", "science", "history", "culture",
            "fashion", "health", "nature", "politics", "education"
        )

        val detectedInterests = possibleInterests.filter { interest ->
            response.contains(interest)
        }

        val interests = if (detectedInterests.isEmpty()) {
            listOf("general")  // Default to general topics if no specific interests detected
        } else {
            detectedInterests
        }

        val userData = users.current.get("userData")
        userData?.interests = interests
        users.current.put("userData", userData)

        furhat.say("Thanks! I'll focus on content related to ${interests.joinToString(", ")}.")
        goto(LearningFocusIntroduction)
    }
}

/**
 * Introduction to learning focus options
 */
val LearningFocusIntroduction: State = state(Parent) {
    onEntry {
        val userData = users.current.get("userData")
        val name = userData?.name ?: "there"
        val language = userData?.currentLanguage ?: "the language"

        // Log session start
        PenPalSkill.memorySystem.episodicMemory.addMemory(
            timestamp = System.currentTimeMillis(),
            userInput = "",
            agentResponse = "",
            eventType = "SESSION_START",
            metadata = mapOf(
                "language" to language,
                "proficiency" to (userData?.proficiencyLevel ?: "beginner")
            )
        )

        // Provide personalized recommendation based on past data
        val suggestedFocus = getSuggestedFocus(userData)
        val recommendation = if (suggestedFocus != null) {
            "Based on your previous sessions, I'd recommend focusing on $suggestedFocus today, but the choice is yours."
        } else {
            "What would you like to focus on today?"
        }

        furhat.say("Now, $name, we can focus on different aspects of $language learning.")
        furhat.ask("$recommendation Would you like to practice vocabulary, grammar, conversation skills, or learn about culture?")
    }

    onResponse<FocusIntent> {
        val focus = it.intent.focus
        val userData = users.current.get("userData")

        // Update user data with selected focus
        userData?.currentFocus = focus
        users.current.put("userData", userData)

        // Store this turn in short-term memory
        PenPalSkill.memorySystem.shortTermMemory.addTurn(
            DialogueTurn(
                userInput = it.text,
                agentResponse = "Great! Let's focus on $focus.",
                metadata = mapOf("focus" to focus)
            )
        )

        goto(LearningFocus)
    }

    onResponse {
        // Try to determine focus from any response
        val response = it.text.toLowerCase()
        val focus = when {
            response.contains("vocab") || response.contains("word") -> "vocabulary"
            response.contains("grammar") || response.contains("structure") ||
                    response.contains("rules") || response.contains("syntax") -> "grammar"
            response.contains("convers") || response.contains("speak") ||
                    response.contains("talk") || response.contains("chat") -> "conversation"
            response.contains("culture") || response.contains("custom") ||
                    response.contains("tradition") || response.contains("histor") -> "culture"
            else -> {
                // If we can't determine, ask more specifically
                furhat.say("I'm not sure which area you'd like to focus on.")
                furhat.ask("Please choose one: vocabulary, grammar, conversation, or culture?")
                reentry()
                return@onResponse
            }
        }

        val userData = users.current.get("userData")
        userData?.currentFocus = focus
        users.current.put("userData", userData)

        furhat.say("Great! Let's focus on $focus.")
        goto(LearningFocus)
    }
}

/**
 * Helper function to load user data from persistent storage
 */
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