from transformers import AutoTokenizer, AutoModel
from huggingface import pipeline
import torch

class ClinicalBERTChatbot:
    def __init__(self):
        self.tokenizer = AutoTokenizer.from_pretrained("medicalai/ClinicalBERT")
        self.model = AutoModel.from_pretrained("medicalai/ClinicalBERT")
        self.ner_pipeline = pipeline(
            "ner",model="kamalkraj/bert-base-uncased-medical-ner",tokenizer="kamalkraj/bert-base-uncased-medical-ner"
        )

    def extract_medical_entities(self, text: str):
        entities = self.ner_pipeline(text)
        return [(ent["word"], ent["entity"]) for ent in entities]

    def classify_intent(self, embedding, text: str):
        if "pain" in text.lower() or "fever" in text.lower():
            return "symptom inquiry"
        elif "medicine" in text.lower() or "drug" in text.lower():
            return "treatment inquiry"
        else:
            return "general inquiry"

    def query_medical_knowledge_base(self, entities, intent):
        if not entities:
            return "I need more details about your symptoms."
        return f"Based on {entities[0][0]}, it seems like you are asking about {intent}. Please consult a healthcare professional."

    def generate_response(self, kb_response):
        return kb_response

    def chat(self, text: str):
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        input_ids = inputs["input_ids"]
        attention_mask = inputs["attention_mask"]

        with torch.no_grad():
            outputs = self.model(input_ids, attention_mask=attention_mask)
            contextual_embeddings = outputs.last_hidden_state

        medical_entities = self.extract_medical_entities(text)

        user_intent = self.classify_intent(contextual_embeddings, text)
        knowledge_base_response = self.query_medical_knowledge_base(medical_entities, user_intent)
        chatbot_response = self.generate_response(knowledge_base_response)
        return chatbot_response

# if __name__ == "__main__":
#     chatbot = ClinicalBERTChatbot()
#     user_input = "..."
#     response = chatbot.chat(user_input)
#     print("Chatbot:", response)