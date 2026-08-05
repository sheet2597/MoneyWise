import matplotlib
matplotlib.use("Agg")  

import matplotlib.pyplot as plt
import io
import base64
import numpy as np
from collections import defaultdict



class grep:
    def __init__(self, title):
        self.title = title

    def grap(self, x, y, y1=None):

        plt.figure(figsize=(8, 4))

        
        plt.gca().set_facecolor("#232b3b")
        plt.gcf().set_facecolor("#141821")

        if y1 is None:
            plt.plot(x, y, marker='o', color="#c5a059", linewidth=2)
        else:
            plt.plot(x, y, marker='o', label='Income',
                     color="#28c76f", linewidth=2)
            plt.plot(x, y1, marker='o', label='Expense',
                     color="#ff4d4f", linewidth=2)

            plt.legend(facecolor="#232b3b",
                       edgecolor="none",
                       labelcolor="white")

        plt.grid(True, linestyle="--", alpha=0.2, color="white")

        plt.xticks(color="white")
        plt.yticks(color="white")
        plt.title(self.title, color="white")
        plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format="png", transparent=True)
        img.seek(0)
        plt.close()

        return base64.b64encode(img.getvalue()).decode()



def category_budget_vs_used(income, expense_map):

    expense_map = {k.strip().title(): float(v)
                   for k, v in expense_map.items()}

    budgets = {
        "Food": income * 0.15,
        "Rent": income * 0.35,
        "Transport": income * 0.10,
        "Shopping": income * 0.10,
        "Bills": income * 0.10,
        "Health": income * 0.05,
        "Education": income * 0.05,
        "Other": income * 0.10,
    }

    categories = list(budgets.keys())
    budget_values = [float(v) for v in budgets.values()]
    used_values = [float(expense_map.get(cat, 0) or 0)
                   for cat in categories]

    x = np.arange(len(categories))
    width = 0.35

    plt.figure(figsize=(11, 5))

    plt.gca().set_facecolor("#232b3b")
    plt.gcf().set_facecolor("#141821")

    plt.bar(x - width/2, budget_values, width,
            label="Budget", color="#c5a059")
    plt.bar(x + width/2, used_values, width,
            label="Used", color="#28c76f")

    plt.xticks(x, categories, rotation=30, color="white")
    plt.yticks(color="white")
    plt.ylabel("Amount (₹)", color="white")
    plt.title("Budget vs Used (50-30-20 Rule)", color="white")

    plt.legend(facecolor="#232b3b",
               edgecolor="none",
               labelcolor="white")

    plt.grid(axis="y", linestyle="--",
             alpha=0.2, color="white")

    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format="png", transparent=True)
    img.seek(0)
    plt.close()

    return base64.b64encode(img.getvalue()).decode()



def asset_amount_vs_current_by_category(assets):

    
    category_data = defaultdict(lambda: {"amount": 0, "current": 0})

    for a in assets:
        category = a.get("category", "Other")
        category_data[category]["amount"] += float(a.get("amount", 0))
        category_data[category]["current"] += float(a.get("current_value", 0))

    categories = list(category_data.keys())
    amounts = [category_data[c]["amount"] for c in categories]
    currents = [category_data[c]["current"] for c in categories]

    x = np.arange(len(categories))
    width = 0.35

    plt.figure(figsize=(11, 5))

    
    plt.gca().set_facecolor("#232b3b")
    plt.gcf().set_facecolor("#141821")

    
    plt.bar(x - width/2, amounts, width,
            label="Invested Amount", color="#c5a059")

    plt.bar(x + width/2, currents, width,
            label="Current Value", color="#28c76f")

    
    plt.xticks(x, categories, rotation=30, color="white")
    plt.yticks(color="white")
    plt.ylabel("Amount (₹)", color="white")
    plt.title("Amount vs Current Value by Category",
              color="white")

    plt.legend(facecolor="#232b3b",
               edgecolor="none",
               labelcolor="white")

    plt.grid(axis="y", linestyle="--",
             alpha=0.2, color="white")

    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format="png", transparent=True)
    img.seek(0)
    plt.close()

    return base64.b64encode(img.getvalue()).decode()


def expense_category_pie_chart(category_rows):

    import matplotlib.pyplot as plt
    import io, base64

    if not category_rows:
        return None

    labels = [row[0] for row in category_rows]
    values = [float(row[1]) for row in category_rows]

    plt.figure(figsize=(6, 6))

    # Dark theme
    plt.gca().set_facecolor("#232b3b")
    plt.gcf().set_facecolor("#141821")

    colors = [
        "#c5a059", "#28c76f", "#ff4d4f",
        "#00cfe8", "#7367f0", "#ff9f43",
        "#1abc9c", "#e84393"
    ]

    wedges, texts, autotexts = plt.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        startangle=140,
        colors=colors[:len(labels)],
        textprops={"color": "white"}
    )

    plt.title("Expense Distribution by Category",
              color="white")

    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format="png", transparent=True)
    img.seek(0)
    plt.close()

    return base64.b64encode(img.getvalue()).decode()
