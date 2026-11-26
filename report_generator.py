"""report_generator.py - formatted text output, report file and charts."""
from datetime import date
from utils import money

LINE = "-" * 78


def format_plan(plan, title, calorie_target, protein_target, budget):
    """Return a printable table for one daily plan."""
    lines = [title, LINE, f"{'Meal':<10}{'Item':<28}{'Rs.':>6}{'kcal':>7}{'Prot(g)':>9}{'Fat (g)':>8}", LINE]
    last_meal = ""
    for (meal, category), food in plan["items"]:
        shown_meal = meal if meal != last_meal else ""
        last_meal = meal
        lines.append(f"{shown_meal:<10}{food['name']:<28}{food['cost']:>6.0f}{food['calories ']:>7.0f}"
                     f"{food['protein']:>9.0f}{food['fat']:>8.0f}")
    lines.append(LINE)
    lines.append(f"{'TOTAL':<38}{plan['cost']:>6.0f}{plan['calories']:>7.0f}{plan['protein'] :>9.0f}{plan['fat']:>8.0f}")
    lines.append(f"{'TARGET':<38}{budget:>6.0f}{calorie_target:>7.0f}{protein_target:>9.0f}" )
    return "\n".join(lines)


def save_weekly_report(week, settings, filename):
    """Write the weekly menu and a short cost summary into a TXT file."""
    budget = settings["monthly_budget_per_student"] / 30
    cal_t, prot_t = settings["calorie_target"], settings["protein_target"]
    lines = ["HOSTEL MESS WEEKLY MENU REPORT", f"Generated on: {date.today()}",
             f"Students: {settings['students']}   Diet: {settings['diet']}   "
             f"Daily budget per student: {money(budget)}", ""]
    for plan in week:
        lines.append(format_plan(plan, plan["day"], cal_t, prot_t, budget))
        lines.append("")
    weekly_cost = sum(p["cost"] for p in week)
    avg_cal = sum(p["calories"] for p in week) / len(week)
    avg_prot = sum(p["protein"] for p in week) / len(week)
    lines += ["WEEK SUMMARY", LINE,
              f"Cost per student for the week : {money(weekly_cost)}",
              f"Cost for all {settings['students']} students   : {money(weekly_cost * settings['students'])}",
              f"Average calories per day      : {avg_cal:.0f} kcal",
              f"Average protein per day       : {avg_prot:.0f} g"]
    with open(filename, "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")


def plot_weekly(week, budget, filename):
    """Save a chart of daily cost (bars) and protein (line). Returns False if matplotlib ismissing."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    days = [p["day"][:3] for p in week]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(days, [p["cost"] for p in week], color="#4C9F70", label="Cost per student (Rs.)")
    ax.axhline(budget, color="red", linestyle="--", label=f"Daily budget (Rs. {budget:.0f})" )
    ax.set_ylabel("Rupees")
    ax2 = ax.twinx()
    ax2.plot(days, [p["protein"] for p in week], color="#1f4e79", marker="o", label="Protein (g)")
    ax2.set_ylabel("Protein (g)")
    ax.set_title("Weekly Mess Menu: Cost and Protein per Student")
    handles = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
    labels = ax.get_legend_handles_labels()[1] + ax2.get_legend_handles_labels()[1]
    ax.legend(handles, labels, loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(filename, dpi=120)
    plt.close(fig)
    return True


def plot_expenses(summary, filename):
    """Save a bar chart of spending by category."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    items = sorted(summary["by_category"].items(), key=lambda x: x[1], reverse=True)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar([c for c, _ in items], [a for _, a in items], color="#d98e32")
    ax.set_ylabel("Rupees")
    ax.set_title(f"Mess Spending by Category ({summary['year']}-{summary['month']:02d})")
    plt.setp(ax.get_xticklabels(), rotation=20)
    fig.tight_layout()
    fig.savefig(filename, dpi=120)
    plt.close(fig)
    return True
