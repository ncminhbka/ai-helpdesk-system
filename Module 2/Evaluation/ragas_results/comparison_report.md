# RAGAS Evaluation Report: Module 1 vs Module 2

**Evaluation Date**: 2026-01-30T15:12:50.999057

**Number of Questions**: 5

## Overview

This report compares two RAG systems:
- **Module 1**: Naive RAG with basic retrieval
- **Module 2**: Advanced RAG with HyDE, hybrid search (BM25 + Vector), and FlashRank reranking

## Metrics Comparison

| Metric | Module 1 (Mean ± Std) | Module 2 (Mean ± Std) | Winner |
|--------|----------------------|----------------------|--------|
| Faithfulness | 0.5977 ± 0.2906 | 0.8417 ± 0.2050 | 🏆 Module 2 |
| Answer Relevancy | 0.5616 ± 0.5133 | 0.5835 ± 0.5068 | 🏆 Module 2 |
| Context Precision | 0.5000 ± 0.5000 | 0.5000 ± 0.5000 | 🏆 Module 2 |
| Context Recall | 0.2000 ± 0.4472 | 0.4000 ± 0.5477 | 🏆 Module 2 |

## Detailed Metrics

### Module 1

- **Faithfulness**: 0.5977 (± 0.2906)
- **Answer Relevancy**: 0.5616 (± 0.5133)
- **Context Precision**: 0.5000 (± 0.5000)
- **Context Recall**: 0.2000 (± 0.4472)

### Module 2

- **Faithfulness**: 0.8417 (± 0.2050)
- **Answer Relevancy**: 0.5835 (± 0.5068)
- **Context Precision**: 0.5000 (± 0.5000)
- **Context Recall**: 0.4000 (± 0.5477)

## Sample Questions Evaluated

1. When does the Personal Data Privacy Policy (for Customers) state that it takes effect?
2. Both the Employee Personal Data Protection Policy and the Customer Personal Data Privacy Policy define “Personal data.” What is that definition, and who is the “data subject” group in each policy (employees vs customers)?
3. Which specific categories of customer personal data does the Customer Personal Data Privacy Policy explicitly state FPT Software will absolutely not collect?

... and 2 more questions.

## Files Generated

- `module1_naive_rag_results.csv`: Detailed per-question results for Module 1
- `module2_advanced_rag_results.csv`: Detailed per-question results for Module 2
- `comparison_summary.json`: Statistical comparison in JSON format
- `comparison_report.md`: This report
