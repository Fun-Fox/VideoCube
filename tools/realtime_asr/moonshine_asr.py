import torch
from transformers import AutoProcessor, MoonshineForConditionalGeneration
from datasets import load_dataset

processor = AutoProcessor.from_pretrained("UsefulSensors/moonshine-tiny-zh")
model = MoonshineForConditionalGeneration.from_pretrained("UsefulSensors/moonshine-tiny-zh")

ds = load_dataset("hf-internal-testing/librispeech_asr_dummy", "clean", split="validation")
audio_array = ds[0]["audio"]["array"]

inputs = processor(audio_array, return_tensors="pt")

generated_ids = model.generate(**inputs)

transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
print(transcription)