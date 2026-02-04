import pandas as pd
import matplotlib.pyplot as plt

# Data
data = {
    "Metric": ["Faithfulness", "Answer Relevancy", "Context Precision", "Context Recall"],
    "Module 1 (Naive RAG)": [0.5977, 0.5616, 0.5000, 0.2000],
    "Module 2 (Advanced RAG)": [0.8417, 0.5535, 0.5000, 0.4000],
    "Change": ["+0.2440", "-0.0081", "0.0000", "+0.2000"]
}

df = pd.DataFrame(data)

# Create a figure
fig, ax = plt.subplots(figsize=(10, 4)) # Adjust size as needed
ax.axis('tight')
ax.axis('off')

# Create the table
table = ax.table(cellText=df.values, colLabels=df.columns, cellLoc='center', loc='center')

# Styling
table.auto_set_font_size(False)
table.set_fontsize(12)
table.scale(1.2, 1.2) # Scale width and height

# Header formatting
for (row, col), cell in table.get_celld().items():
    if row == 0:
        cell.set_text_props(weight='bold', color='white')
        cell.set_facecolor('#4A90E2') # Blue header
    elif  col == 0:
        cell.set_text_props(weight='bold')

    # Highlight Module 2 Faithfulness and Context Recall
    if row == 1 and col == 2: # Faithfulness Mod 2
         cell.set_text_props(weight='bold', color='green')
    if row == 4 and col == 2: # Context Recall Mod 2
         cell.set_text_props(weight='bold', color='green')

# Save
output_path = r"d:\New_VS_Code\Intern\FPT Intern AI Roadmap\Module 2\Evaluation\ragas_results\comparison_table.png"
plt.savefig(output_path, bbox_inches='tight', dpi=300)

print(f"Table saved to {output_path}")
