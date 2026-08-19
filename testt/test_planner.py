import sys
import os

sys.path.append(os.path.abspath(".."))

from ai.planner import plan_query

questions = [
    "In which subject did I score the most?",
    "What's my best subject?",
    "Which subject am I weakest in?",
    "Where am I losing marks?",
    "How have I performed over the last three exams?",
    "Compare my Maths marks with Science.",
    "Which exam was my best?",
    "Which exam was my worst?",
    "How is my overall performance?",
    "Should I focus more on Mathematics?"
]

for q in questions:
    print("=" * 50)
    print(q)
    print(plan_query(q))