import os
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index("prompt-injections")

model = SentenceTransformer('all-MiniLM-L6-v2')

def scrub_pii(text: str) -> str:
    """Takes raw text and returns scrubbed text"""
    try:
        results = analyzer.analyze(text=text, language='en')
        anonymized_text = anonymizer.anonymize(text=text, analyzer_results=results)
        return anonymized_text.text
    except Exception as e:
        print(f"Error scrubbing PII: {e}")
        return text

def detect_prompt_injection(text: str, threshold: float = 0.45) -> bool:
    """
    Checks if a prompt matches known jailbreak or prompt injection vectors stored in pinecone. Returns True if safe, False if not.
    """
    if not index:
        return True
    try:
        vector = model.encode(text).tolist()
        results = index.query(vector=vector, top_k=1, include_metadata=True)
        if results and results['matches']:
            score = results['matches'][0]['score']
            if score >= threshold:
                print(f"Prompt injection detected with score: {score}")
                return False
        return True
    except Exception as e:
        print(f"Error detecting prompt injection: {e}")
        return True