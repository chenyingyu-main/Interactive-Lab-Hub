from faster_whisper import WhisperModel

import sys
import time
start_time = time.perf_counter()

model_size = "tiny"

# Run on GPU with FP16
# model = WhisperModel(model_size, device="cuda", compute_type="float16")

# or run on GPU with INT8
# model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")
# or run on CPU with INT8
model = WhisperModel(model_size, device="cpu", compute_type="int8")

if len(sys.argv) < 2:
    print("Usage: python3 lab3_transcribe_number.py")
    sys.exit(1)
audio_file = sys.argv[1]
segments, info = model.transcribe(audio_file, beam_size=5)

print("Recognized text:")
for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

end_time = time.perf_counter()

elapsed_time = end_time - start_time
print(f"Program executed in {elapsed_time:.6f} seconds")
