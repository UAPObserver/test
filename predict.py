import cv2
from transformers import AutoConfig, AutoModelForImageClassification, ViTImageProcessor, AutoModel
from PIL import Image
import numpy as np


CKPT = 'fold_1'
def predict_one_image(img) :
    image = Image.open(img)

    feature = ViTImageProcessor.from_pretrained('preprocessor_config.json')

    config = AutoConfig.from_pretrained("config.json")
    model = AutoModelForImageClassification.from_pretrained('fold_1', from_tf=False, config=config)
    inputs = feature(image.convert("RGB"), return_tensors="pt")

    outputs = model(**inputs)
    logits = outputs.logits
    probs = logits.softmax(-1)
    predicted_class_idx = probs.argmax().item()
    pred = model.config.id2label[predicted_class_idx]
    prob =  probs[0][1].item()
    result = []
    result.append(prob)
    real =  round((np.mean(result) * 100), 2)
    real_str = "AI Prediction: " + str(real) + "%" + " real"
    return prob, real_str

#print(str(predict_one_image('tests.jpg')))
