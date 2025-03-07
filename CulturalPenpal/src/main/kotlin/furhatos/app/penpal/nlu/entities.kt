package furhatos.app.penpal.nlu

import furhatos.nlu.ListEntity

val LanguageEntity = ListEntity(
    entityType = "language",
    values = listOf("Spanish", "French", "German", "Italian", "Japanese", "Chinese")
)

val FocusEntity = ListEntity(
    entityType = "focus",
    values = listOf("vocabulary", "grammar", "conversation", "culture")
)