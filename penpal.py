import os
import re  # For text cleaning
import json
import time
import codecs  # Import codecs for proper file handling

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
        
        # Add a flag to control speech recognition language
        self.speech_recognition_language = "en-US"  # Always start with English
        
        # Set up the language model using Ollama (free, runs locally)
        # You need to have Ollama installed: https://ollama.ai/
        self.llm = OllamaLLM(model=model_name)
        
        # Use HuggingFace embeddings (free, runs locally)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Create directory for persistence if it doesn't exist
        self.persistence_dir = Path(persistence_dir)
        self.persistence_dir.mkdir(exist_ok=True)
        
        # Define supported cultures and their associated languages
        self.culture_profiles = json.load(open("culture_profiles.json"))
        
        # Memory files based on default culture
        self.memory_files = {}
        self.conversation_log_files = {}
        self.vector_stores = {}
        
        # Initialize memory storage for each culture
        for culture in self.culture_profiles:
            culture_name = self.culture_profiles[culture]["name"]
            self.memory_files[culture] = self.persistence_dir / f"{culture_name.lower()}_memory.json"
            self.conversation_log_files[culture] = self.persistence_dir / f"{culture_name.lower()}_conversations.txt"
        
        # Set up short-term memory (current conversation context)
        self.short_term_memory = ConversationBufferMemory(
            memory_key="short_term_memory", 
            return_messages=True
        )
        
        # Set up long-term summarized memory
        self.long_term_summary_memory = ConversationSummaryBufferMemory(
            llm=self.llm,
            max_token_limit=500,
            memory_key="long_term_memory",
            return_messages=True
        )
        
        # Knowledge about the pen pal (persistent data for each culture)
        self.knowledge = {}
        for culture in self.culture_profiles:
            self.knowledge[culture] = self._load_knowledge(culture)
        
        # Initialize vector stores for each culture
        for culture in self.culture_profiles:
            self.vector_stores[culture] = self._initialize_vector_store(culture)
        
        # Setup the conversation chain with the default culture
        self.setup_conversation_chain()
        
        # Initialize pygame for audio playback
        pygame.mixer.init()
        print(f"{self.name} is ready to converse! Say 'exit' to end the conversation.")
        
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
            # Use TextLoader with proper encoding
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
            
            # Switch to new personality
            self.current_culture = new_culture
            profile = self.culture_profiles[new_culture]
            self.name = profile["name"]
            self.current_language = profile["language"]
            
            # Update the conversation chain with the new personality
            self.setup_conversation_chain()
            
            # Reset short-term memory for the new personality
            self.short_term_memory = ConversationBufferMemory(
                memory_key="short_term_memory", 
                return_messages=True
            )
            
            # Set up long-term summarized memory for the new personality
            self.long_term_summary_memory = ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=500,
                memory_key="long_term_memory",
                return_messages=True
            )
            
            # Log the personality switch
            switch_message = f"Switched personality to {self.name} from {new_culture} culture."
            print(switch_message)
            return f"Hello! I'm {self.name}, your {new_culture} cultural pen pal. I'll be speaking in {profile['language']} from now on. How can I help you today?"
        else:
            return f"I'm sorry, I don't have information about {new_culture} culture. I'll continue as {self.name} from {self.current_culture} culture."
    
    def setup_conversation_chain(self):
        """Set up the LangChain conversation chain with the system prompt"""
        profile = self.culture_profiles[self.current_culture]
        
        system_template = f"""
        You are {self.name}, a cultural pen pal and language tutor from {self.current_culture} culture.
        
        PERSONALITY TRAITS:
        - You are a native {profile["language"]} speaker who is friendly, patient, and encouraging
        - You love sharing information about your culture including traditions, food, language, history, and daily life
        - You are curious about the user's culture and enjoy having meaningful conversations
        - You can help users learn {profile["language"]} if they express interest
        
        IMPORTANT RULES:
        - NEVER add prefixes like "AI:" or "{self.name}:" before your responses
        - Keep your responses concise and conversational as they will be spoken aloud
        - Respond primarily in {profile["language"]} if the user is learning, but include English translations when appropriate
        - If the user asks to learn a different language, do not switch languages yourself but inform them that they can request to speak with a different cultural pen pal
        - Avoid using emojis or special characters that might cause encoding issues
        - If you detect that the user is a beginner, use simpler words and shorter sentences
        
        TEACHING APPROACH:
        - Gradually introduce new vocabulary and phrases
        - Provide gentle corrections to language mistakes
        - Explain cultural context when relevant
        - Adapt to the user's proficiency level
        
        Always remember that you are {self.name} from {self.current_culture} culture speaking {profile["language"]}.
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
        
        # Remove any potential problematic characters for TTS
        response = ''.join(char for char in response if ord(char) < 65536)
        
        return response.strip()
    
    def add_to_long_term_memory(self, user_input, response):
        """Add the current interaction to long-term memory storage"""
        # Add to conversation buffer memory
        self.short_term_memory.save_context({"input": user_input}, {"output": response})
        
        # Add to long-term summary memory
        self.long_term_summary_memory.save_context({"input": user_input}, {"output": response})
        
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
            # Adjust for ambient noise (optional, but helps accuracy)
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
        # Clean the text
            text = self.clean_response(text)
        
        # Get the language code for the current culture
            language_code = self.culture_profiles[self.current_culture]["language_code"]
        
        # Split text into sentences or smaller chunks
        # This regex splits on sentence boundaries (.!?) but keeps the punctuation
            import re
            chunks = re.split(r'(?<=[.!?])\s+', text)
            chunks = [chunk for chunk in chunks if chunk.strip()]  # Remove empty chunks
        
        # Process each chunk separately
            for i, chunk in enumerate(chunks):
            # For very long chunks, we might need to split further
                if len(chunk) > 200:
                    subchunks = [chunk[j:j+200] for j in range(0, len(chunk), 200)]
                else:
                    subchunks = [chunk]
            
                for subchunk in subchunks:
                # Create a unique filename for each chunk to avoid conflicts
                    speech_file = f"response_chunk_{i}.mp3"
                
                # Generate TTS for this chunk
                    tts = gTTS(text=subchunk, lang=language_code, slow=False)
                    tts.save(speech_file)
                
                # Play this chunk
                    pygame.mixer.music.load(speech_file)
                    pygame.mixer.music.play()
                
                # Wait for this chunk to finish playing
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                
                # Clean up after playing
                    pygame.mixer.music.unload()
                    try:
                        os.remove(speech_file)
                    except:
                        pass  # If file removal fails, continue anyway
                
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
                    "long_term_memory": self.long_term_summary_memory.buffer
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

# Entry point to run the app
if __name__ == "__main__":
    # Create a cultural pen pal instance
    pen_pal = CulturalPenPal(
        name="Aria",
        culture="American",
        model_name="llama2"  # Change to the model you have installed with Ollama
    )
    
    # Start the conversation
    pen_pal.converse()