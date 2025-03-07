package furhatos.app.penpal.nlu

import furhatos.util.*
import furhatos.nlu.*

class LanguageIntent : Intent() {
    var language: String = ""

    override fun getExamples(lang: Language): List<String> {
        return listOf(
            "I want to practice @language",
            "Let's learn @language",
            "@language please",
            "I'm interested in @language"
        )
    }
}

class FocusIntent : Intent() {
    var focus: String = ""

    override fun getExamples(lang: Language): List<String> {
        return listOf(
            "Let's focus on @focus",
            "I want to practice @focus",
            "@focus please",
            "Can we do some @focus"
        )
    }
}