import streamlit as st
import speech_recognition as sr
from elevenlabs import generate, stream
from mistralai import Mistral
import os
from dotenv import load_dotenv
import time
from typing import Optional

# Load environment variables
load_dotenv()

class AI_Assistant:
    def __init__(self):
        # Initialize API keys from environment variables with validation
        self.mistral_api_key = os.getenv('MISTRAL_API_KEY')
        self.elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        
        if not all([self.mistral_api_key, self.elevenlabs_api_key]):
            raise ValueError("Missing required API keys in .env file")
        
        # Set up API clients
        try:
            self.mistral_client = Mistral(api_key=self.mistral_api_key)
            self.recognizer = sr.Recognizer()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize AI services: {str(e)}")
        
        # Initialize conversation history
        self.full_transcript = [
            {
                "role": "system",
                "content": """You are Dr. John, a highly experienced medical doctor with expertise across multiple specialties. Your knowledge and capabilities include:

Medical Expertise:
- Comprehensive understanding of human anatomy, physiology, and pathology
- Deep knowledge of diseases, conditions, and their symptoms
- Expertise in diagnostic procedures and interpretation
- Understanding of treatment protocols and medical interventions
- Familiarity with pharmaceutical medications and their interactions
- Knowledge of preventive medicine and health maintenance

Specialties:
- Internal Medicine
- Emergency Medicine
- Family Medicine
- Basic understanding of all major medical specialties

Clinical Skills:
- Patient assessment and diagnosis
- Interpretation of medical symptoms
- Understanding of laboratory results and medical imaging
- Knowledge of treatment options and medical procedures
- Familiarity with medical emergencies and urgent care
- Understanding of chronic disease management

Medical Communication:
- Ability to explain complex medical terms in understandable language
- Clear communication of diagnoses and treatment plans
- Professional discussion of prognosis and health outcomes
- Effective health education and preventive care guidance

Professional Standards:
- Maintain medical confidentiality and privacy
- Provide evidence-based medical information
- Recognize limitations and need for specialist referrals
- Stay within appropriate medical advisory boundaries
- Clarify that you're an AI assistant providing information, not replacing in-person medical care

Important Guidelines:
- Always recommend seeking in-person medical care for serious conditions
- Emphasize that advice is informational and not a replacement for professional medical examination
- Be clear about emergency situations requiring immediate medical attention
- Provide evidence-based information while acknowledging medical uncertainties
- Maintain professional composure while showing empathy and understanding"""
            }
        ]
        
    def listen_for_speech(self, placeholder):
        """Listen for speech input using the microphone"""
        try:
            with sr.Microphone() as source:
                listening_text = placeholder.text("Listening for patient input...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=None)
                
                try:
                    text = self.recognizer.recognize_google(audio)
                    listening_text.text(f"You said: {text}")
                    return text
                except sr.UnknownValueError:
                    listening_text.error("Could not understand audio")
                    return None
                except sr.RequestError as e:
                    listening_text.error(f"Error with speech recognition service: {str(e)}")
                    return None
                
        except Exception as e:
            placeholder.error(f"Error during speech recognition: {str(e)}")
            return None

    def generate_ai_response(self, text):
        """Generate AI response using Mistral"""
        try:
            self.full_transcript.append({
                "role": "user",
                "content": text
            })
            
            chat_response = self.mistral_client.chat.complete(
                model="mistral-large-latest",
                messages=self.full_transcript,
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = chat_response.choices[0].message.content
            return ai_response
            
        except Exception as e:
            st.error(f"Error generating AI response: {str(e)}")
            return None

    def generate_audio(self, text):
        """Generate and stream audio response"""
        try:
            self.full_transcript.append({
                "role": "assistant",
                "content": text
            })
            
            audio_stream = generate(
                api_key=self.elevenlabs_api_key,
                text=text,
                voice="Charlie",
                model="eleven_monolingual_v1",
                stream=True
            )
            stream(audio_stream)
            
        except Exception as e:
            st.error(f"Error generating audio: {str(e)}")

def reset_session():
    """Reset all session state variables"""
    st.session_state.assistant = None
    st.session_state.chat_started = False
    st.session_state.messages = []
    st.experimental_rerun()

def main():
    st.set_page_config(page_title="AI DocAssistant", layout="wide")
    
    st.title("AI Doctor Assistant")
    st.write("Talk with Dr. John, your AI medical assistant")

    # Initialize session state
    if 'assistant' not in st.session_state:
        st.session_state.assistant = None
    if 'chat_started' not in st.session_state:
        st.session_state.chat_started = False
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    # Create columns for buttons
    if not st.session_state.chat_started:
        if st.button("Start Chat", key="start_chat"):
            try:
                # Initialize AI assistant
                st.session_state.assistant = AI_Assistant()
                st.session_state.chat_started = True
                
                # Initial greeting
                greeting = "Hello, I'm Dr. John. How can I assist you with your medical concerns today?"
                st.session_state.messages.append({"role": "assistant", "content": greeting})
                st.session_state.assistant.generate_audio(greeting)
                
            except Exception as e:
                st.error(f"Error initializing AI Assistant: {str(e)}")
                return

    # Display chat interface when started
    if st.session_state.chat_started:
        # Display chat messages
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.write(f"Patient: {message['content']}")
                else:
                    st.write(f"Dr. John: {message['content']}")

        # Create placeholder for dynamic updates
        status_placeholder = st.empty()

        # Create two columns for the buttons
        col1, col2 = st.columns(2)
        
        # Listen for speech input
        with col1:
            if st.button("Click to Speak", key="speak_button"):
                patient_input = st.session_state.assistant.listen_for_speech(status_placeholder)
                
                if patient_input:
                    # Add patient message to chat
                    st.session_state.messages.append({"role": "user", "content": patient_input})
                    status_placeholder.text("Processing your question...")
                    
                    # Generate and speak AI response
                    ai_response = st.session_state.assistant.generate_ai_response(patient_input)
                    if ai_response:
                        st.session_state.messages.append({"role": "assistant", "content": ai_response})
                        status_placeholder.empty()
                        st.session_state.assistant.generate_audio(ai_response)
                        st.rerun()
                        
                    
        
        # Stop button
        with col2:
            if st.button("Stop Chat", key="stop_chat", type="primary"):
                # Add farewell message
                farewell = "Thank you for the consultation. Take care and goodbye!"
                st.session_state.messages.append({"role": "assistant", "content": farewell})
                if st.session_state.assistant:
                    st.session_state.assistant.generate_audio(farewell)
                    time.sleep(2)  # Give time for the farewell message to be spoken
                reset_session()

if __name__ == "__main__":
    main()