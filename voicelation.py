import tkinter as tk
import threading
import queue
import sounddevice as sd
import vosk
import json
import screeninfo
import sys
import os

q = queue.Queue()

def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

def recognize_speech_vosk(label, language):
    model_path = ""
    if language == "en":
        model_path = "/home/san/Documents/stt/vosk-model-small-en-us-0.15"
    elif language == "tl":
        model_path = "/home/san/Documents/stt/vosk-model-tl-ph-generic-0.6"

    if not os.path.exists(model_path):
        print(f"Model path not found: {model_path}")
        if language == "en":
            model_name = "vosk-model-small-en-us-0.15"
        else:
            model_name = "vosk-model-tl-ph-generic-0.1"
        try:
            model = vosk.Model(model_name=model_name)
        except Exception as e:
            print(f"Failed to download model {model_name}: {e}")
            return
    else:
        model = vosk.Model(model_path)

    with sd.RawInputStream(samplerate=16000, blocksize=8000, device=None, dtype='int16',
                            channels=1, callback=callback):
        print(f"Listening with vosk in {language}...")
        rec = vosk.KaldiRecognizer(model, 16000)
        recognized_text = ""
        while True:
            data = q.get()
            
            is_final = rec.AcceptWaveform(data)

            if is_final:
                result = json.loads(rec.Result())
                text = result.get('text', '')
                if text:
                    recognized_text += text + " "
                current_text_to_process = recognized_text
            else:
                partial_result = json.loads(rec.PartialResult())
                partial_text = partial_result.get('partial', '')
                current_text_to_process = recognized_text + partial_text

            if current_text_to_process:
                words = current_text_to_process.split()
                lines = []
                current_line = ""
                for word in words:
                    if len(current_line.split()) < 15:
                        if current_line:
                            current_line += " " + word
                        else:
                            current_line = word
                    else:
                        lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)
                
                display_text = "\n".join(lines[-3:])
                label.config(text=display_text)

def main():
    while True:
        print("Please select a language:")
        print("1: English")
        print("2: Filipino")
        choice = input("Enter 1 or 2: ")
        if choice == "1":
            language = "en"
            break
        elif choice == "2":
            language = "tl"
            break
        else:
            print("Invalid choice. Please try again.")

    root = tk.Tk()
    root.title("Voicelation")

    primary_monitor = None
    for m in screeninfo.get_monitors():
        if m.is_primary:
            primary_monitor = m
            break

    if not primary_monitor:
        primary_monitor = screeninfo.get_monitors()[0]

    screen_width = primary_monitor.width
    screen_height = primary_monitor.height
    window_width = 1000
    window_height = 250
    x_pos = (screen_width // 2) - (window_width // 2) + primary_monitor.x
    y_pos = (screen_height // 2) - (window_height // 2) + primary_monitor.y
    root.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")

    root.configure(bg='black')
    root.overrideredirect(True)
    root.wm_attributes("-topmost", True)
    root.wm_attributes("-alpha", 0.7)

    label = tk.Label(root, text="...", font=("Helvetica", 24), fg="white", bg="black", wraplength=780, justify=tk.LEFT)
    label.pack(expand=True, fill='both')

    def exit_app(event):
        root.destroy()

    label.bind("<Button-3>", exit_app)
    root.bind("<Button-3>", exit_app)

    thread = threading.Thread(target=recognize_speech_vosk, args=(label, language), daemon=True)
    thread.start()

    root.mainloop()

if __name__ == "__main__":
    main()
