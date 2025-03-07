package furhatos.app.penpal.flow

import furhatos.app.penpal.PenPalSkill
import furhatos.app.penpal.nlu.*
import furhatos.app.penpal.util.DialogueTurn
import furhatos.flow.kotlin.*
import furhatos.nlu.common.*

val Greeting: State = state(Parent) {
    onEntry {
        // Check if this user has used the system before
        val userData = users.current.get("userData")
        val userName = userData?.name

        if (userName != null) {
            // User has been here before - retrieve from episodic memory
            val relevantMemories = PenPalSkill.memorySystem.episodicMemory.retrieveRelevantMemories(userName, limit = 1)

            if (relevantMemories.isNotEmpty()) {
                val lastLanguage = relevantMemories[0].metadata["language"] as? String

                if (lastLanguage != null) {
                    furhat.say("Welcome back, $userName! Last time we practiced $lastLanguage. Would you like to continue with that or try something different today?")

                    // Store this turn in short-term memory
                    PenPalSkill.memorySystem.shortTermMemory.addTurn(
                        DialogueTurn(
                            userInput = "",
                            agentResponse = "Welcome back, $userName! Last time we practiced $lastLanguage. Would you like to continue with that or try something different today?"
                        )
                    )

                    goto(LanguageChoice(lastLanguage))
                } else {
                    furhat.say("Welcome back, $userName! What language would you like to practice today?")
                    goto(LanguageChoice())
                }
            } else {
                furhat.say("Welcome back, $userName! What language would you like to practice today?")
                goto(LanguageChoice())
            }
        } else {
            // New user
            furhat.say("Hello! I'm your cultural pen pal. I can help you learn languages and explore different cultures. What's your name?")

            // Store this turn in short-term memory
            PenPalSkill.memorySystem.shortTermMemory.addTurn(
                DialogueTurn(
                    userInput = "",
                    agentResponse = "Hello! I'm your cultural pen pal. I can help you learn languages and explore different cultures. What's your name?"
                )
            )
        }
    }

    onResponse<NameIntent> {
        val name = it.intent.name

        // Save user's name in user data
        val userData = users.current.get("userData")
        userData?.name = name
        users.current.put("userData", userData)

        // Store this turn in short-term memory
        PenPalSkill.memorySystem.shortTermMemory.addTurn(
            DialogueTurn(
                userInput = it.text,
                agentResponse = "Nice to meet you, $name! What language would you like to learn today?"
            )
        )

        furhat.say("Nice to meet you, $name! What language would you like to learn today?")
        goto(LanguageChoice())
    }
}

fun LanguageChoice(suggestedLanguage: String? = null): State = state(Parent) {
    onEntry {
        if (suggestedLanguage != null) {
            // Wait for user response about continuing with the same language
        } else {
            furhat.ask("I can help you practice Spanish, French, German, Japanese, or Chinese. Which one interests you?")
        }
    }

    onResponse<LanguageIntent> {
        val language = it.intent.language

        // Update user data with selected language
        val userData = users.current.get("userData")
        userData?.currentLanguage = language
        users.current.put("userData", userData)

        // Update long-term memory with language preference
        PenPalSkill.memorySystem.longTermMemory.updatePreference("preferred_language", language)

        // Store this turn in short-term memory
        PenPalSkill.memorySystem.shortTermMemory.addTurn(
            DialogueTurn(
                userInput = it.text,
                agentResponse = "Great! Let's practice $language. What aspect would you like to focus on - vocabulary, grammar, or conversation?"
            )
        )

        furhat.say("Great! Let's practice $language. What aspect would you like to focus on - vocabulary, grammar, or conversation?")
        goto(LearningFocus)
    }

    onResponse<ContinueIntent> {
        if (suggestedLanguage != null) {
            // User wants to continue with the previously practiced language
            val userData = users.current.get("userData")
            userData?.currentLanguage = suggestedLanguage
            users.current.put("userData", userData)

            // Store this turn in short-term memory
            PenPalSkill.memorySystem.shortTermMemory.addTurn(
                DialogueTurn(
                    userInput = it.text,
                    agentResponse = "Great! Let's continue with $suggestedLanguage. What aspect would you like to focus on - vocabulary, grammar, or conversation?"
                )
            )

            furhat.say("Great! Let's continue with $suggestedLanguage. What aspect would you like to focus on - vocabulary, grammar, or conversation?")
            goto(LearningFocus)
        }
    }

    onResponse<DenyIntent> {
        if (suggestedLanguage != null) {
            // User wants to try a different language
            furhat.ask("Which language would you prefer to practice today? I can help with Spanish, French, German, Japanese, or Chinese.")
        }
    }
}