import speech_recognition as sr
import pyaudio
import wave
import time
import os

def test_microphone_list():
    """List all available microphones"""
    p = pyaudio.PyAudio()
    info = '\nAvailable Microphones:\n'
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        if dev_info['maxInputChannels'] > 0:  # if the device has input channels, it's a microphone
            info += f"Index {i}: {dev_info['name']}\n"
    p.terminate()
    return info

def record_and_play_test(duration=5):
    """Record audio and play it back to test microphone"""
    chunk = 1024
    format = pyaudio.paInt16
    channels = 1
    rate = 44100
    
    p = pyaudio.PyAudio()
    
    print(f"\nRecording for {duration} seconds...")
    
    stream = p.open(format=format,
                    channels=channels,
                    rate=rate,
                    input=True,
                    frames_per_buffer=chunk)
    
    frames = []
    
    for i in range(0, int(rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)
        # Print a dot every second to show progress
        if i % int(rate / chunk) == 0:
            print(".", end="", flush=True)
    
    print("\nFinished recording!")
    
    stream.stop_stream()
    stream.close()
    
    # Save the recorded audio
    test_file = "microphone_test.wav"
    wf = wave.open(test_file, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(format))
    wf.setframerate(rate)
    wf.writeframes(b''.join(frames))
    wf.close()
    
    # Play back the recorded audio
    print("\nPlaying back the recording...")
    
    wf = wave.open(test_file, 'rb')
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)
    
    data = wf.readframes(chunk)
    while data:
        stream.write(data)
        data = wf.readframes(chunk)
    
    stream.stop_stream()
    stream.close()
    p.terminate()
    
    # Clean up the test file
    wf.close()
    os.remove(test_file)

def test_speech_recognition():
    """Test speech recognition"""
    recognizer = sr.Recognizer()
    
    print("\nTesting speech recognition...")
    print("Please speak something when prompted.")
    
    try:
        with sr.Microphone() as source:
            print("\nAdjusting for ambient noise... Please be quiet.")
            recognizer.adjust_for_ambient_noise(source, duration=2)
            print("\nOK, now speak something...")
            
            try:
                audio = recognizer.listen(source, timeout=5)
                print("\nProcessing speech...")
                
                try:
                    text = recognizer.recognize_google(audio)
                    print(f"\nYou said: {text}")
                    return True
                except sr.UnknownValueError:
                    print("\nGoogle Speech Recognition could not understand the audio")
                    return False
                except sr.RequestError as e:
                    print(f"\nCould not request results from Google Speech Recognition service; {e}")
                    return False
                    
            except sr.WaitTimeoutError:
                print("\nNo speech detected within timeout period")
                return False
                
    except Exception as e:
        print(f"\nError during speech recognition test: {str(e)}")
        return False

def main():
    """Run all microphone tests"""
    try:
        # Test 1: List available microphones
        print(test_microphone_list())
        
        # Test 2: Record and playback
        input("Press Enter to start recording test...")
        record_and_play_test(5)
        
        # Test 3: Speech recognition
        input("\nPress Enter to start speech recognition test...")
        test_speech_recognition()
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")

if __name__ == "__main__":
    main()