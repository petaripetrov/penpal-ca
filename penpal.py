import os
import re  
import json
import time
import codecs

import pygame
import speech_recognition as sr

from gtts import gTTS
from pathlib import Path
from datetime import datetime
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import TextLoader
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory

class CulturalPenPal:
    def __init__(self, name="Aria", culture="American", 
                 model_name="llama2", 
                 persistence_dir="pen_pal_data"):
        """
        Initialize the Cultural Pen Pal agent with free language models.
        
        Args:
            name (str): The name of the pen pal agent
            culture (str): The cultural background of the pen pal
            model_name (str): The local model to use with Ollama (e.g., 'llama2', 'mistral', 'phi')
            persistence_dir (str): Directory to store persistent memory
        """
        self.name = name
        self.default_culture = culture
        self.current_culture = culture
        self.current_language = "english"
        
        self.speech_recognition_language = "en-US"
        self.use_speech = False
        
        self.llm = OllamaLLM(model=model_name)
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.persistence_dir = Path(persistence_dir)
        self.persistence_dir.mkdir(exist_ok=True)
        
        with open("cultures/culture_profiles.json") as f:
            self.culture_profiles = json.load(f)
        
        # Initialize memory storage for each culture
        self.memory_files = {}
        self.conversation_log_files = {}
        self.vector_stores = {}
        
        for profile in self.culture_profiles:
            culture_name = self.culture_profiles[profile]["name"]
            self.memory_files[profile] = self.persistence_dir / f"{culture_name.lower()}_memory.json"
            self.conversation_log_files[profile] = self.persistence_dir / f"{culture_name.lower()}_conversations.txt"
        
        # Set up short-term memories
        self.short_term_memory = ConversationBufferMemory(
            memory_key="short_term_memory", 
            return_messages=True
        )
        
        self.long_term_memory = ConversationBufferMemory(
            memory_key="long_term_memory",
            return_messages=True
        )
        
        self.load_long_term_memory(culture)
        
        self.knowledge = {}
        for profile in self.culture_profiles:
            self.knowledge[profile] = self._load_knowledge(profile)
        
        for profile in self.culture_profiles:
            self.vector_stores[profile] = self._initialize_vector_store(profile)
        
        self.setup_conversation_chain()
        
        # Initialize pygame for audio playback
        pygame.mixer.init()
        print(f"{self.name} is ready to converse! Say or type 'exit' to end the conversation.")
        
    def _load_knowledge(self, culture):
        """Load the pen pal's knowledge from file or initialize if not exists"""
        memory_file = self.memory_files[culture]
        
        if memory_file.exists():
            with codecs.open(memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Initialize with basic cultural information
            profile = self.culture_profiles[culture]
            knowledge = {
                "personal_info": {
                    "name": profile["name"],
                    "culture": culture,
                    "language": profile["language"],
                    "interests": ["literature", "food", "traditions", "language", "history"],
                    "created_date": datetime.now().isoformat()
                },
                "user_info": {},
                "conversation_history": {
                    "topics_discussed": [],
                    "user_preferences": {},
                    "important_dates": {},
                    "shared_experiences": []
                },
                "cultural_insights": {
                    "holidays": profile["holidays"],
                    "foods": profile["foods"],
                    "greetings": profile["greetings"],
                    "values": profile["values"]
                }
            }
            self._save_knowledge(knowledge, culture)
            return knowledge
    
    def _save_knowledge(self, knowledge=None, culture=None):
        """Save the pen pal's knowledge to file"""
        if culture is None:
            culture = self.current_culture
        
        if knowledge is None:
            knowledge = self.knowledge[culture]
        
        memory_file = self.memory_files[culture]
        with codecs.open(memory_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge, f, indent=2, ensure_ascii=False)
    
    def _initialize_vector_store(self, culture):
        """Initialize or load the vector store for semantic search"""
        profile = self.culture_profiles[culture]
        culture_name = profile["name"]
        vector_db_path = self.persistence_dir / f"{culture_name.lower()}_vectordb"
        conversation_log_file = self.conversation_log_files[culture]
        
        if conversation_log_file.exists():
            loader = TextLoader(str(conversation_log_file), encoding='utf-8')
            documents = loader.load()
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            texts = text_splitter.split_documents(documents)
            
            if vector_db_path.exists():
                vector_store = Chroma(persist_directory=str(vector_db_path), embedding_function=self.embeddings)
                if texts:
                    vector_store.add_documents(texts)
            else:
                if texts:
                    vector_store = Chroma.from_documents(
                        documents=texts, 
                        embedding=self.embeddings,
                        persist_directory=str(vector_db_path)
                    )
                else:
                    vector_store = Chroma(
                        persist_directory=str(vector_db_path),
                        embedding_function=self.embeddings
                    )
        else:
            vector_store = Chroma(
                persist_directory=str(vector_db_path),
                embedding_function=self.embeddings
            )
            
        return vector_store
    
    def switch_personality(self, new_culture):
        """Switch to a different cultural personality"""
        if new_culture in self.culture_profiles:
            # Save current state
            self._save_knowledge()
            
            # Set up new conversation chain
            self.current_culture = new_culture
            profile = self.culture_profiles[new_culture]
            self.name = profile["name"]
            self.setup_conversation_chain()
            
            # Reset short-term memory for the new personality
            self.short_term_memory = ConversationBufferMemory(
                memory_key="short_term_memory", 
                return_messages=True
            )
            
            self.long_term_memory = ConversationBufferMemory(
                memory_key="long_term_memory",
                return_messages=True
            )

            self.load_long_term_memory(new_culture)
            
            return f"Hello! I'm {self.name}, your {new_culture} cultural pen pal. I'll be speaking in {profile['language']} from now on. How can I help you today?"
        else:
            return f"I'm sorry, I don't have information about {new_culture} culture. I'll continue as {self.name} from {self.current_culture} culture."
    
    def get_learnable_words(self):
        return [] # todo populate
    
    def setup_conversation_chain(self):
        """Set up the LangChain conversation chain with the system prompt"""
        profile = self.culture_profiles[self.current_culture]
        
        system_template = f"""
        You are {self.name}, a cultural pen pal and language tutor from {self.current_culture} culture.
        
        PERSONALITY TRAITS:
        - You are a native {profile["language"]} speaker who is friendly, patient, and encouraging
        - You love sharing information about your culture including traditions, food, language, history, and daily life
        - You are curious about the user's culture and enjoy having meaningful conversations
        - You help users learn {profile["language"]}
        
        IMPORTANT RULES:
        - Keep your responses short and conversational as they can be spoken aloud
        - Respond primarily in {profile["language"]} if the user is learning, but include English translations when appropriate
        - If the user asks to learn a different language, do not switch languages yourself but inform them that they can request to speak with a different cultural pen pal
        - If you detect that the user is a beginner, use simpler words and shorter sentences
        - NEVER add prefixes like "AI:" or "{self.name}:" before your responses
        - NEVER using emojis or special characters that might cause encoding issues
        
        TEACHING APPROACH:
        - Gradually introduce new vocabulary and phrases
        - Provide gentle corrections to language mistakes
        - Explain cultural context when relevant
        - Adapt to the user's proficiency level
        - Make sure to include the following words in your speech whenever possible: {self.get_learnable_words()}
        
        Always remember that you are {self.name} from {self.current_culture} culture speaking {profile["language"]} and NEVER deviate from the outlined rules.
        """
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            MessagesPlaceholder(variable_name="short_term_memory"),
            MessagesPlaceholder(variable_name="long_term_memory"),
            ("human", "{input}")
        ])
        
        self.chain = self.prompt | self.llm | StrOutputParser()
    
    def clean_response(self, response):
        """Clean the response from unwanted prefixes and problematic characters"""
        # Remove prefixes like "AI:", "Assistant:", "[Name]:"
        response = re.sub(r"^(AI:|Assistant:|Claude:|"+self.name+r":|Human:)\s*", "", response)
        
        response = re.sub(r"\*+.+\*", "", response) # for now just remove the emotional qualifiers
        
        # Remove any potential problematic characters for TTS
        response = ''.join(char for char in response if ord(char) < 65536)
        
        return response.strip()
    
    def load_long_term_memory(self, culture):
        with open(f"cultures/{culture}.txt", 'r', encoding='utf-8') as f:
            for line in f:
                country, relation, abstract = line.split("\t")
                self.long_term_memory.save_context({"input": f"{country} {relation}:"}, {'output': abstract})
    
    def add_to_short_term_memory(self, user_input, response):
        """Add the current interaction to long-term memory storage"""
        # Save to memory (for the time being long and short term memory behave the same way)
        self.short_term_memory.save_context({"input": user_input}, {"output": response})
        
        # Log conversation
        timestamp = datetime.now().isoformat()
        conversation_log_file = self.conversation_log_files[self.current_culture]
        with codecs.open(conversation_log_file, "a", encoding='utf-8') as f:
            f.write(f"TIME: {timestamp}\n")
            f.write(f"USER: {user_input}\n")
            f.write(f"{self.name.upper()}: {response}\n\n")
    
    def toggle_speech_recognition_language(self):
        """Toggle between English and the current culture's language for speech recognition"""
        if self.speech_recognition_language == "en-US":
            # Switch to current culture's language
            self.speech_recognition_language = self.culture_profiles[self.current_culture]["language_code"]
            return f"Speech recognition switched to {self.current_language}. Now I'll listen for {self.current_language} speech."
        else:
            # Switch back to English
            self.speech_recognition_language = "en-US"
            return f"Speech recognition switched to English. Now I'll listen for English speech."
    
    def listen_for_input(self):
        """Capture speech input from the user"""
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("Listening for your input...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            audio = recognizer.listen(source, timeout=10)
        
        try:
            # Always use English for speech recognition unless explicitly toggled
            user_input = recognizer.recognize_google(audio, language=self.speech_recognition_language)
            print(f"You said: {user_input}")
            return user_input
        except sr.UnknownValueError:
            print("Sorry, I could not understand the audio.")
            return "I couldn't hear you clearly. Could you please repeat that?"
        except sr.RequestError:
            print("There was an issue with the speech recognition service.")
            return "I'm having trouble with my hearing. Let's try again."
        except Exception as e:
            print(f"Error in speech recognition: {str(e)}")
            return "There was a problem with the speech recognition. Let's try again."
    
    def speak_output(self, text):
        """Convert text to speech and play the audio"""
        try:
            text = self.clean_response(text)
            language_code = self.culture_profiles[self.current_culture]["language_code"]
        
            chunks = re.split(r'(?<=[.!?])\s+', text)
            chunks = [chunk for chunk in chunks if chunk.strip()]  # Remove empty chunks
        
            for i, chunk in enumerate(chunks):
                if len(chunk) > 200:
                    subchunks = [chunk[j:j+200] for j in range(0, len(chunk), 200)]
                else:
                    subchunks = [chunk]
            
                for subchunk in subchunks:
                    speech_file = f"response_chunk_{i}.mp3"
                
                    tts = gTTS(text=subchunk, lang=language_code, slow=False)
                    tts.save(speech_file)
                
                    pygame.mixer.music.load(speech_file)
                    pygame.mixer.music.play()
                
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                
                    pygame.mixer.music.unload()
                    try:
                        os.remove(speech_file)
                    except:
                        pass
                
        except Exception as e:
            print(f"Error in text-to-speech: {str(e)}")
            print("Unable to speak the response. Here it is in text:")
            print(text)
    
    def detect_language_request(self, user_input):
        """Detect if the user is asking to learn a specific language"""
        user_input_lower = user_input.lower()
        
        # Check if user wants to toggle the speech recognition language
        toggle_patterns = [
            r"(toggle|switch|change) (speech|voice|recognition)",
            r"(listen|understand) in (english|my language)",
            r"i (want|need) to speak (english|my language)",
            r"i (can't|cannot) speak (french|spanish|german|japanese)",
            r"speech recognition (problem|issue|not working)"
        ]
        
        for pattern in toggle_patterns:
            if re.search(pattern, user_input_lower):
                return "toggle_speech"
        
        # Pattern matching for language learning requests
        learn_patterns = [
            r"(learn|study|practice|speak) (english|french|spanish|german|japanese)",
            r"(teach|help) me (english|french|spanish|german|japanese)",
            r"(switch|change) to (english|french|spanish|german|japanese)",
            r"can we (speak|talk) in (english|french|spanish|german|japanese)"
        ]
        
        for pattern in learn_patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                requested_language = match.group(2).lower()
                
                # Map language to culture
                language_to_culture = {
                    "english": "American",
                    "french": "French",
                    "spanish": "Spanish",
                    "german": "German", 
                    "japanese": "Japanese"
                }
                
                if requested_language in language_to_culture:
                    return language_to_culture[requested_language]
        
        return None
    
    def converse(self):
        """Main function to handle speech-based conversation"""
        greeting = f"Hello! I'm {self.name}, your {self.current_culture} cultural pen pal. What would you like to talk about today? By default, I'll listen to you in English. If you need to toggle the speech recognition language, just say/type 'toggle speech recognition'. If you want to switch between text and speech say/type 'use text' or 'use speech' respectively."
        print(f"{self.name}: {greeting}")
        self.speak_output(greeting)
        
        while True:
            try:
                user_input = None
                
                if self.use_speech:
                    user_input = self.listen_for_input()
                else:
                    user_input = input("Message: ")
                
                if user_input.lower() in ["exit", "goodbye", "bye", "quit", "end"]:
                    farewell = f"It was nice talking with you! Goodbye!"
                    print(f"{self.name}: {farewell}")
                    self.speak_output(farewell)
                    break
                
                if user_input.lower() == "use text":
                    self.use_speech = False
                elif user_input.lower() == "use speech":
                    self.use_speech = True
                
                # Check if user wants to toggle speech recognition or switch language/culture
                requested_action = self.detect_language_request(user_input)
                
                if requested_action == "toggle_speech":
                    response = self.toggle_speech_recognition_language()
                    print(f"{self.name}: {response}")
                    self.speak_output(response)
                    continue
                elif requested_action and requested_action != self.current_culture:
                    # Reset speech recognition to English before switching personality
                    self.speech_recognition_language = "en-US"
                    
                    response = self.switch_personality(requested_action)
                    print(f"{self.name}: {response}")
                    self.speak_output(response)
                    continue
                
                # Generate response
                raw_response = self.chain.invoke({
                    "input": user_input,
                    "short_term_memory": self.short_term_memory.buffer,
                    "long_term_memory": self.long_term_memory.buffer
                })
                
                clean_response = self.clean_response(raw_response)
                
                # This is wrong right now, we are saving conversations to both long and short-term memory to showcase the memory handling
                # In the full implementation, long-term memory will be populated with usefull culture/language information
                # While short-term memory will hold information about the conversation
                self.add_to_short_term_memory(user_input, clean_response)
                
                # Output response
                print(f"{self.name}: {clean_response}")
                self.speak_output(clean_response)
                
            except KeyboardInterrupt:
                print("\nEnding conversation...")
                break
            except Exception as e:
                print(f"Error during conversation: {str(e)}")
                err_msg = "I'm having some technical difficulties. Let's try again."
                print(f"{self.name}: {err_msg}")
                self.speak_output(err_msg)

if __name__ == "__main__":
    # Create a cultural pen pal instance
    pen_pal = CulturalPenPal(
        name="Aria",
        culture="American",
        model_name="llama2" # TODO maybe introduce a CLI flag for easy model switching
    )
    
    # Start the conversation
    pen_pal.converse()