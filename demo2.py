# app.py

import streamlit as st
import os
import tempfile
import json
import time
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)

st.set_page_config(
    page_title="Audio Transcription App",
    page_icon="🎙️",
    layout="wide"
)

st.title("🎙️ Audio Transcription App")
st.write("Upload an audio file to transcribe it using Deepgram's API.")

# API key input (could be stored more securely in production)
api_key = st.text_input("Enter your Deepgram API Key:", 
                        type="password", 
                        help="Your Deepgram API key. Get one at https://console.deepgram.com")

uploaded_file = st.file_uploader("Choose an audio file", 
                                type=["wav", "mp3", "m4a", "ogg", "flac", "aac", "mp4"],
                                help="Select an audio file from your device to transcribe")

# Add option for showing confidence values
show_confidence = st.checkbox("Show confidence values", value=False,
                             help="Display the numerical confidence score for each word")

# Function to transcribe audio using Deepgram SDK
def transcribe_audio(file_path, api_key):
    try:
        # Create a Deepgram client using the API key
        deepgram = DeepgramClient(api_key)
        
        # Read the audio file as binary data
        with open(file_path, "rb") as file:
            buffer_data = file.read()
        
        payload: FileSource = {
            "buffer": buffer_data,
        }
        
        # Configure Deepgram options for audio analysis
        options = PrerecordedOptions(
            model="nova-3",
            smart_format=True,
            diarize=True
        )
        
        # Call the transcribe_file method with the payload and options
        response = deepgram.listen.rest.v("1").transcribe_file(payload, options)
        
        # Return the response
        return response
        
    except Exception as e:
        raise Exception(f"Deepgram transcription error: {e}")

def display_transcription(response, show_confidence=False):
    try:
        # Get the full transcription result
        results = response.results
        
        st.markdown("### Transcription Result:")
        
        # Process paragraphs and sentences
        word_count = 0
        for p in results.channels[0].alternatives[0].paragraphs.paragraphs:
            for s in p.sentences:
                # Start a new sentence container
                html = '<div style="margin-bottom: 10px;"><span style="font-weight: bold;">Sentence: </span>'
                
                # Process each word in the sentence
                words_in_sentence = s.text.split(' ')
                for i, w in enumerate(words_in_sentence):
                    if word_count < len(results.channels[0].alternatives[0].words):
                        word_obj = results.channels[0].alternatives[0].words[word_count]
                        confidence = word_obj.confidence
                        
                        # Calculate color based on confidence
                        r = int(255 * (1 - confidence))
                        g = int(255 * confidence)
                        b = 0
                        
                        # Display word with or without confidence score
                        if show_confidence:
                            display_text = f"{w} ({confidence:.2f})"
                        else:
                            display_text = w
                            
                        html += f'<span style="background-color: rgb({r}, {g}, {b}); padding: 3px 5px; margin: 2px; border-radius: 3px; color: {"white" if confidence < 0.5 else "black"};">{display_text}</span> '
                        
                        word_count += 1
                    else:
                        # If we run out of word objects with confidence scores
                        html += f'<span>{w}</span> '
                
                html += '</div>'
                st.markdown(html, unsafe_allow_html=True)
        
        # Add download options for transcript
        plain_text = " ".join([w.word for w in results.channels[0].alternatives[0].words])
        st.download_button(
            label="Download Transcript (Text)",
            data=plain_text,
            file_name="transcript.txt",
            mime="text/plain"
        )
        
        # Download with confidence scores
        detailed_text = "\n".join([f"{w.word} ({w.confidence:.2f})" for w in results.channels[0].alternatives[0].words])
        st.download_button(
            label="Download Detailed Transcript (with confidence scores)",
            data=detailed_text,
            file_name="detailed_transcript.txt",
            mime="text/plain"
        )
        
    except Exception as e:
        st.error(f"Error parsing transcription result: {e}")
        st.json(response.to_dict())

# Transcribe button
if uploaded_file is not None and api_key:
    if st.button("Transcribe Audio"):
        with st.spinner("Transcribing your audio... This may take a moment."):
            # Create a temporary file to store the uploaded audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            try:
                # Call the transcribe function
                response = transcribe_audio(tmp_file_path, api_key)
                
                # Display the colored transcription with user preference for confidence values
                display_transcription(response, show_confidence)
                
                # Optionally display the raw JSON response in an expandable section
                with st.expander("View Raw API Response"):
                    st.json(response.to_dict())
                    
            except Exception as e:
                st.error(f"An error occurred during transcription: {e}")
            
            finally:
                # Clean up the temporary file
                os.unlink(tmp_file_path)

elif not api_key and uploaded_file is not None:
    st.warning("Please enter your Deepgram API key to proceed.")
elif api_key and uploaded_file is None:
    st.info("Please upload an audio file to transcribe.")
else:
    st.info("Enter your API key and upload an audio file to get started.")

# Add some helpful information at the bottom
st.markdown("---")
st.markdown("""
### About this app
This application uses the Deepgram API to transcribe your audio files. The transcription is color-coded 
based on the confidence level:
- **Green**: High confidence
- **Yellow/Orange**: Medium confidence
- **Red**: Low confidence

Your files are processed securely and are not stored permanently.
""")

# Add a sidebar with additional information
with st.sidebar:
    st.header("How to use")
    st.markdown("""
    1. Enter your Deepgram API key
    2. Upload an audio file
    3. Toggle the "Show confidence values" checkbox if you want to see numerical scores
    4. Click 'Transcribe Audio'
    5. View the color-coded transcription
    6. Download the transcript if needed
    
    You can repeat this process with different audio files.
    """)
    
    st.header("Supported File Types")
    st.markdown("WAV, MP3, M4A, OGG, FLAC, AAC, MP4")