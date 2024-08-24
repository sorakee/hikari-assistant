from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TextClassificationPipeline
)

model_name = 'qanastek/XLMRoberta-Alexa-Intents-Classification'
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
classifier = TextClassificationPipeline(model=model, tokenizer=tokenizer)


if __name__ == "__main__":
    while True:
        user = input("> ")
        result = classifier(user)
        print(result)