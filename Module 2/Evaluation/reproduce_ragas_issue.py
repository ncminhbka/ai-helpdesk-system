
import os
import sys
from dotenv import load_dotenv
from ragas import evaluate
from ragas.metrics import answer_relevancy
from datasets import Dataset
from langchain_openai import OpenAIEmbeddings

# Load env variables from project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
dotenv_path = os.path.join(project_root, '.env')

print(f"Loading .env from: {dotenv_path}")
load_dotenv(dotenv_path)

if not os.getenv("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY not found in environment!")
    sys.exit(1)

# Initialize embeddings
embeddings = OpenAIEmbeddings()

# Check if embeddings work
try:
    vec = embeddings.embed_query("test")
    print(f"Embeddings working, vector length: {len(vec)}")
except Exception as e:
    print(f"Embeddings initialization failed: {e}")
    sys.exit(1)

# Configure answer_relevancy with explicit embeddings
answer_relevancy.embeddings = embeddings

# Simple dataset
data = {
    "question": ["What is the capital of France?"],
    "answer": ["The capital of France is Paris."],
    "contexts": [["France is a country in Europe. Its capital is Paris."]],
    "ground_truth": ["Paris"]
}

dataset = Dataset.from_dict(data)

print("evaluating...")
try:
    result = evaluate(
        dataset,
        metrics=[answer_relevancy],
    )
    print("Result:", result)
except Exception as e:
    print("Error during evaluation:", e)
    import traceback
    traceback.print_exc()
