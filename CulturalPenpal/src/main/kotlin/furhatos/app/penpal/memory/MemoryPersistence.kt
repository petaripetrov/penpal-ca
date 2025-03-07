package furhatos.app.penpal.memory
import com.google.gson.Gson
import java.io.File

class MemoryPersistence {
    private val gson = Gson()
    private val basePath = "memory/"

    init {
        File(basePath).mkdirs()
    }

    fun saveEpisodicMemory(userId: String, memory: EpisodicMemory) {
        val file = File("$basePath$userId-episodic.json")
        file.writeText(gson.toJson(memory))
    }

    fun loadEpisodicMemory(userId: String): EpisodicMemory? {
        val file = File("$basePath$userId-episodic.json")
        if (!file.exists()) return null
        return try {
            gson.fromJson(file.readText(), EpisodicMemory::class.java)
        } catch (e: Exception) {
            null
        }
    }

    fun saveSemanticMemory(userId: String, memory: SemanticMemory) {
        val file = File("$basePath$userId-semantic.json")
        file.writeText(gson.toJson(memory))
    }

    fun loadSemanticMemory(userId: String): SemanticMemory? {
        val file = File("$basePath$userId-semantic.json")
        if (!file.exists()) return null
        return try {
            gson.fromJson(file.readText(), SemanticMemory::class.java)
        } catch (e: Exception) {
            null
        }
    }

    fun deleteMemory(userId: String) {
        File("$basePath$userId-episodic.json").delete()
        File("$basePath$userId-semantic.json").delete()
    }

    fun getAllUserIds(): List<String> {
        val directory = File(basePath)
        return directory.listFiles()
            ?.filter { it.isFile && it.name.endsWith("-episodic.json") }
            ?.map { it.name.removeSuffix("-episodic.json") }
            ?: emptyList()
    }
}