package furhatos.app.penpal.flow

import furhatos.app.penpal.PenPalSkill
import furhatos.app.penpal.nlu.*
import furhatos.flow.kotlin.*
import furhatos.nlu.common.*
import furhatos.app.penpal.util.UserData

// Define our parent state for all skills
val Parent: State = state {
    onUserLeave(instant = true) {
        // Save user memory data when they leave
        val userId = users.current.id
        PenPalSkill.memorySystem.persistUserMemory(userId)

        // Reset current user state
        if (users.count > 0) {
            furhat.attend(users.other)
            goto(Idle)
        } else {
            goto(Idle)
        }
    }

    onUserEnter(instant = true) {
        // Load user memory if they have previous interactions
        val userId = users.current.id
        PenPalSkill.memorySystem.loadUserMemory(userId)

        // Initialize user data if not present
        if (users.current.get("userData") == null) {
            users.current.put("userData", UserData())
        }

        furhat.attend(users.current)
    }
}

// Define the idle state
val Idle: State = state(Parent) {
    onEntry {
        // Reset dialog state
        furhat.gesture(Gestures.GazeAway)
        furhat.setNeckTilt(0.0)
        furhat.setLedColor(240, 240, 240)

        // Wait for users
        furhat.attendNobody()
    }

    onUserEnter {
        furhat.attend(users.current)
        goto(Greeting)
    }
}

// Define the init state
val Init: State = state {
    onEntry {
        // Initialize the Furhat robot
        furhat.setVoice(Language.ENGLISH_US, Gender.FEMALE)
        furhat.character = "Isabel"

        // Load language and cultural data
        PenPalSkill.memorySystem.semanticMemory.loadLanguageData()

        // Set LED color
        furhat.setLedColor(0, 125, 255)

        goto(Idle)
    }
}