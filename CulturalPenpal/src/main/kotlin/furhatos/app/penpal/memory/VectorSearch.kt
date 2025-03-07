package furhatos.app.penpal.memory

import furhatos.app.penpal.nlu.*
import furhatos.flow.kotlin.*
import furhatos.nlu.common.*

class VectorSearch {
    private val model = SentenceEmbeddingModel() // You'll need to implement this with an appropriate NLP library

    fun embed(text: String): FloatArray {
        return model.encode(text)
    }

    fun findSimilar(query: String, documents: List<String>, topK: Int = 5): List<Pair<String, Float>> {
        val queryEmbedding = embed(query)

        return documents.map { doc ->
            val docEmbedding = embed(doc)
            val similarity = cosineSimilarity(queryEmbedding, docEmbedding)
            Pair(doc, similarity)
        }.sortedByDescending { it.second }.take(topK)
    }

    private fun cosineSimilarity(a: FloatArray, b: FloatArray): Float {
        var dotProduct = 0.0f
        var normA = 0.0f
        var normB = 0.0f

        for (i in a.indices) {
            dotProduct += a[i] * b[i]
            normA += a[i] * a[i]
            normB += b[i] * b[i]
        }

        return dotProduct / (Math.sqrt(normA.toDouble()) * Math.sqrt(normB.toDouble())).toFloat()
    }
}