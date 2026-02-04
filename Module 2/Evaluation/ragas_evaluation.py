"""
RAGAS Evaluation Script: Module 1 (Naive RAG) vs Module 2 (Advanced RAG)

This script evaluates and compares two RAG systems using RAGAS metrics:
- Faithfulness
- Answer Relevancy
- Context Precision
- Context Recall
"""

import os
import sys
import pandas as pd
import json
from datetime import datetime
from typing import List, Dict
import random

# RAGAS imports
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
from datasets import Dataset
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

# Import RAG wrappers
from module1_rag_wrapper import Module1RAGWrapper
from module2_rag_wrapper import Module2RAGWrapper


def load_validation_data(csv_path: str, sample_size: int = 5, random_seed: int = 42) -> pd.DataFrame:
    """
    Load validation dataset and randomly sample questions.
    
    Args:
        csv_path: Path to validation CSV file
        sample_size: Number of questions to sample
        random_seed: Random seed for reproducibility
        
    Returns:
        DataFrame with sampled questions
    """
    print(f"\n{'='*80}")
    print(f"LOADING VALIDATION DATA")
    print(f"{'='*80}\n")
    
    df = pd.read_csv(csv_path)
    print(f"✓ Loaded {len(df)} questions from {csv_path}")
    
    # Set random seed for reproducibility
    random.seed(random_seed)
    
    # Sample questions
    if sample_size < len(df):
        sampled_df = df.sample(n=sample_size, random_state=random_seed)
        print(f"✓ Randomly sampled {sample_size} questions (seed={random_seed})\n")
    else:
        sampled_df = df
        print(f"✓ Using all {len(df)} questions\n")
    
    return sampled_df


def evaluate_rag_system(
    rag_wrapper,
    questions: List[str],
    ground_truths: List[str],
    system_name: str
) -> Dict:
    """
    Evaluate a RAG system using RAGAS metrics.
    
    Args:
        rag_wrapper: RAG system wrapper (Module1RAGWrapper or Module2RAGWrapper)
        questions: List of questions
        ground_truths: List of ground truth answers
        system_name: Name of the system being evaluated
        
    Returns:
        Dictionary with evaluation results
    """
    print(f"\n{'='*80}")
    print(f"EVALUATING {system_name}")
    print(f"{'='*80}\n")
    
    # Initialize lists to store results
    answers = []
    contexts_list = []
    
    # Query the RAG system for each question
    for idx, question in enumerate(questions, 1):
        print(f"[{idx}/{len(questions)}] Processing: {question[:60]}...")
        
        result = rag_wrapper.query(question)
        answers.append(result["answer"])
        contexts_list.append(result["contexts"])
        
        print(f"  ✓ Answer generated ({len(result['answer'])} chars)")
        print(f"  ✓ Retrieved {len(result['contexts'])} contexts\n")
    
    # Prepare dataset for RAGAS
    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts_list,
        "ground_truth": ground_truths,
    }
    
    dataset = Dataset.from_dict(data)
    
    print(f"\n{'='*80}")
    print(f"COMPUTING RAGAS METRICS FOR {system_name}")
    print(f"{'='*80}\n")
    
    # Initialize embeddings for answer_relevancy
    # Find .env file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    dotenv_path = os.path.join(project_root, '.env')
    load_dotenv(dotenv_path)
    
    embeddings = OpenAIEmbeddings()
    answer_relevancy.embeddings = embeddings
    
    
    # Evaluate with RAGAS
    try:
        result = evaluate(
            dataset,
            metrics=[
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
            ],
        )
        
        print(f"✓ RAGAS evaluation complete for {system_name}\n")
        
        return {
            "system_name": system_name,
            "dataset": dataset,
            "ragas_result": result,
            "answers": answers,
            "contexts": contexts_list,
        }
        
    except Exception as e:
        print(f"❌ Error during RAGAS evaluation: {e}\n")
        return {
            "system_name": system_name,
            "dataset": dataset,
            "ragas_result": None,
            "answers": answers,
            "contexts": contexts_list,
            "error": str(e)
        }


def save_results(
    module1_results: Dict,
    module2_results: Dict,
    questions: List[str],
    ground_truths: List[str],
    output_dir: str = "ragas_results"
):
    """
    Save evaluation results to files.
    
    Args:
        module1_results: Results from Module 1 evaluation
        module2_results: Results from Module 2 evaluation
        questions: List of questions
        ground_truths: List of ground truth answers
        output_dir: Directory to save results
    """
    print(f"\n{'='*80}")
    print(f"SAVING RESULTS")
    print(f"{'='*80}\n")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Save detailed results for each module
    for results in [module1_results, module2_results]:
        if results["ragas_result"] is not None:
            # Convert to DataFrame
            df = results["ragas_result"].to_pandas()
            
            # Add questions and ground truths
            df.insert(0, "question", questions)
            df.insert(1, "ground_truth", ground_truths)
            df.insert(2, "answer", results["answers"])
            
            # Save to CSV
            csv_path = os.path.join(output_dir, f"{results['system_name'].lower().replace(' ', '_')}_results.csv")
            df.to_csv(csv_path, index=False)
            print(f"✓ Saved {results['system_name']} detailed results to {csv_path}")
    
    # Create comparison summary
    comparison_summary = {
        "evaluation_date": datetime.now().isoformat(),
        "num_questions": len(questions),
        "module1": {},
        "module2": {},
    }
    
    # Add metrics for each module
    for module_key, results in [("module1", module1_results), ("module2", module2_results)]:
        if results["ragas_result"] is not None:
            df = results["ragas_result"].to_pandas()
            
            comparison_summary[module_key] = {
                "system_name": results["system_name"],
                "metrics": {
                    "faithfulness": {
                        "mean": float(df["faithfulness"].mean()),
                        "std": float(df["faithfulness"].std()),
                    },
                    "answer_relevancy": {
                        "mean": float(df["answer_relevancy"].mean()),
                        "std": float(df["answer_relevancy"].std()),
                    },
                    "context_precision": {
                        "mean": float(df["context_precision"].mean()),
                        "std": float(df["context_precision"].std()),
                    },
                    "context_recall": {
                        "mean": float(df["context_recall"].mean()),
                        "std": float(df["context_recall"].std()),
                    },
                }
            }
    
    # Save comparison summary as JSON
    json_path = os.path.join(output_dir, "comparison_summary.json")
    with open(json_path, "w") as f:
        json.dump(comparison_summary, f, indent=2)
    print(f"✓ Saved comparison summary to {json_path}")
    
    # Create markdown report
    create_markdown_report(comparison_summary, questions, module1_results, module2_results, output_dir)
    
    print(f"\n✓ All results saved to {output_dir}/\n")


def create_markdown_report(
    summary: Dict,
    questions: List[str],
    module1_results: Dict,
    module2_results: Dict,
    output_dir: str
):
    """Create a human-readable markdown report."""
    
    report_path = os.path.join(output_dir, "comparison_report.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# RAGAS Evaluation Report: Module 1 vs Module 2\n\n")
        f.write(f"**Evaluation Date**: {summary['evaluation_date']}\n\n")
        f.write(f"**Number of Questions**: {summary['num_questions']}\n\n")
        
        f.write("## Overview\n\n")
        f.write("This report compares two RAG systems:\n")
        f.write("- **Module 1**: Naive RAG with basic retrieval\n")
        f.write("- **Module 2**: Advanced RAG with HyDE, hybrid search (BM25 + Vector), and FlashRank reranking\n\n")
        
        f.write("## Metrics Comparison\n\n")
        f.write("| Metric | Module 1 (Mean ± Std) | Module 2 (Mean ± Std) | Winner |\n")
        f.write("|--------|----------------------|----------------------|--------|\n")
        
        metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
        for metric in metrics:
            m1 = summary["module1"]["metrics"][metric]["mean"]
            m1_std = summary["module1"]["metrics"][metric]["std"]
            m2 = summary["module2"]["metrics"][metric]["mean"]
            m2_std = summary["module2"]["metrics"][metric]["std"]
            
            winner = "🏆 Module 2" if m2 > m1 else ("🏆 Module 1" if m1 > m2 else "Tie")
            
            f.write(f"| {metric.replace('_', ' ').title()} | {m1:.4f} ± {m1_std:.4f} | {m2:.4f} ± {m2_std:.4f} | {winner} |\n")
        
        f.write("\n## Detailed Metrics\n\n")
        
        for module_key, system_name in [("module1", "Module 1"), ("module2", "Module 2")]:
            f.write(f"### {system_name}\n\n")
            
            for metric in metrics:
                mean_val = summary[module_key]["metrics"][metric]["mean"]
                std_val = summary[module_key]["metrics"][metric]["std"]
                f.write(f"- **{metric.replace('_', ' ').title()}**: {mean_val:.4f} (± {std_val:.4f})\n")
            
            f.write("\n")
        
        f.write("## Sample Questions Evaluated\n\n")
        for idx, question in enumerate(questions[:3], 1):  # Show first 3 questions
            f.write(f"{idx}. {question}\n")
        
        if len(questions) > 3:
            f.write(f"\n... and {len(questions) - 3} more questions.\n")
        
        f.write("\n## Files Generated\n\n")
        f.write("- `module1_naive_rag_results.csv`: Detailed per-question results for Module 1\n")
        f.write("- `module2_advanced_rag_results.csv`: Detailed per-question results for Module 2\n")
        f.write("- `comparison_summary.json`: Statistical comparison in JSON format\n")
        f.write("- `comparison_report.md`: This report\n")
    
    print(f"✓ Saved markdown report to {report_path}")


def main():
    """Main execution function."""
    
    print(f"\n{'#'*80}")
    print(f"# RAGAS EVALUATION: MODULE 1 (NAIVE RAG) VS MODULE 2 (ADVANCED RAG)")
    print(f"{'#'*80}\n")
    
    # Configuration
    CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "val_dataset.csv")
    SAMPLE_SIZE = 5
    RANDOM_SEED = 42
    OUTPUT_DIR = "ragas_results"
    
    # 1. Load validation data
    df = load_validation_data(CSV_PATH, SAMPLE_SIZE, RANDOM_SEED)
    
    questions = df["question"].tolist()
    ground_truths = df["ground_truth"].tolist()
    
    # 2. Initialize RAG systems
    print(f"\n{'='*80}")
    print(f"INITIALIZING RAG SYSTEMS")
    print(f"{'='*80}\n")
    
    print("Initializing Module 1 (Naive RAG)...")
    module1_wrapper = Module1RAGWrapper()
    print("✓ Module 1 initialized\n")
    
    print("Initializing Module 2 (Advanced RAG)...")
    module2_wrapper = Module2RAGWrapper()
    print("✓ Module 2 initialized\n")
    
    # 3. Evaluate Module 1
    module1_results = evaluate_rag_system(
        module1_wrapper,
        questions,
        ground_truths,
        "Module1 Naive RAG"
    )
    
    # 4. Evaluate Module 2
    module2_results = evaluate_rag_system(
        module2_wrapper,
        questions,
        ground_truths,
        "Module2 Advanced RAG"
    )
    
    # 5. Save and compare results
    save_results(module1_results, module2_results, questions, ground_truths, OUTPUT_DIR)
    
    # 6. Print summary
    print(f"\n{'#'*80}")
    print(f"# EVALUATION COMPLETE")
    print(f"{'#'*80}\n")
    
    print(f"Results saved to: {OUTPUT_DIR}/")
    print(f"\nTo view the comparison:")
    print(f"  - Open {OUTPUT_DIR}/comparison_report.md for a summary")
    print(f"  - Open {OUTPUT_DIR}/comparison_summary.json for detailed metrics")
    print(f"  - Open CSV files for per-question analysis\n")


if __name__ == "__main__":
    main()
