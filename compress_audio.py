from pydub import AudioSegment
import os

input_dir  = "assets/steps"
output_dir = "assets/steps"

for filename in os.listdir(input_dir):
    if filename.endswith(".wav"):
        name = filename.replace(".wav", "")
        wav  = AudioSegment.from_wav(os.path.join(input_dir, filename))
        wav.export(os.path.join(output_dir, f"{name}.ogg"), format="ogg", bitrate="96k")
        os.remove(os.path.join(input_dir, filename))
        print(f"Convertido: {name}")

print("Hecho.")