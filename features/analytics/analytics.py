from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from collections import Counter
from datetime import datetime, timedelta
import questionary

from features.transactions.transactions import _get_transactions, EXPENSE_CATEGORIES
from features.budgets.budgets import _get_budgets

console = Console()

def _get_monthly_data(month_str):
    """Helper to get income, expenses, and savings for a specific month."""
    transactions = _get_transactions()
    income = 0
    expenses = 0
    expenses_by_cat = Counter()

    for t in transactions:
        if t['date'].startswith(month_str):
            if t['type'] == 'income':
                income += t['amount_paisa']
            else:
                expenses += t['amount_paisa']
                expenses_by_cat[t['category']] += t['amount_paisa']
                
    savings = income - expenses
    return income, expenses, savings, expenses_by_cat

def show_spending_analysis():
    """Displays a detailed analysis of spending for the current month."""
    console.print("\n[bold]────── Spending Analysis (Current Month) ──────[/bold]")
    
    current_month_str = datetime.now().strftime("%Y-%m")
    days_in_month = (datetime.now().replace(day=1) + timedelta(days=32)).day
    today = datetime.now().day

    _, total_expenses, _, expenses_by_cat = _get_monthly_data(current_month_str)

    if total_expenses == 0:
        console.print("[yellow]No spending data for the current month.[/yellow]")
        return

    # --- ASCII Pie Chart ---
    console.print(Panel("Spending by Category", style="bold blue"))
    table = Table(box=None, show_header=False)
    table.add_column(width=15)
    table.add_column(width=50)
    table.add_column(justify="right", style="bold")

    sorted_expenses = expenses_by_cat.most_common()
    
    for category, amount in sorted_expenses:
        percentage = (amount / total_expenses) * 100
        bar = '█' * int(percentage / 2)
        table.add_row(category, bar, f"{percentage:.1f}%")
    
    console.print(table)

    # --- Top 3 & Burn Rate ---
    console.print(Panel("Spending Insights", style="bold blue"))
    
    # Top 3
    top_3 = sorted_expenses[:3]
    top_3_str = ", ".join([f"{cat} ({amt/100:,.2f})" for cat, amt in top_3])
    console.print(f"🔥 [bold]Top Spending Categories:[/]	{top_3_str}")

    # Burn Rate
    avg_daily_expense = (total_expenses / today) / 100
    console.print(f"📈 [bold]Average Daily Expense (Burn Rate):[/]	{avg_daily_expense:,.2f}")

def show_income_analysis():
    """Displays a detailed analysis of income for the current month."""
    console.print("\n[bold]────── Income Analysis (Current Month) ──────[/bold]")
    current_month_str = datetime.now().strftime("%Y-%m")
    
    total_income, _, _, _ = _get_monthly_data(current_month_str)

    if total_income == 0:
        console.print("[yellow]No income data for the current month.[/yellow]")
        return
        
    transactions = _get_transactions()
    income_by_source = Counter()
    for t in transactions:
        if t['type'] == 'income' and t['date'].startswith(current_month_str):
            income_by_source[t['category']] += t['amount_paisa']

    table = Table(title="Income by Source", show_header=True, header_style="bold magenta")
    table.add_column("Source", style="cyan")
    table.add_column("Amount", justify="right")
    table.add_column("Percentage", justify="right")

    for source, amount in income_by_source.most_common():
        percentage = (amount / total_income) * 100
        table.add_row(source, f"{amount / 100:,.2f}", f"{percentage:.1f}%")
        
    console.print(table)
    console.print(f"\n[bold green]Total Income this month: {total_income / 100:,.2f}[/bold green]")

def show_savings_analysis():
    """Displays savings rate and trend."""
    console.print("\n[bold]────── Savings Analysis ──────[/bold]")
    
    today = datetime.now()
    current_month_str = today.strftime("%Y-%m")
    
    total_income, _, savings, _ = _get_monthly_data(current_month_str)

    if total_income == 0:
        console.print("[yellow]No income data for the current month to calculate savings rate.[/yellow]")
        return

    savings_rate = (savings / total_income) * 100 if total_income > 0 else 0
    
    console.print(f"💰 [bold]Current Month Savings:[/]	[green]{savings / 100:,.2f}[/green]")
    console.print(f"📊 [bold]Current Month Savings Rate:[/]	[bold {{'green' if savings_rate > 0 else 'red'}} ]{savings_rate:.2f}%[/bold]")

    # Trend Analysis (Last 3 Months)
    table = Table(title="Savings Trend (Last 3 Months)", show_header=True, header_style="bold magenta")
    table.add_column("Month", style="cyan")
    table.add_column("Savings", justify="right")
    
    for i in range(3):
        month = today - timedelta(days=i*30)
        month_str = month.strftime("%Y-%m")
        income, expenses, _, _ = _get_monthly_data(month_str)
        month_savings = income - expenses
        table.add_row(month.strftime("%B %Y"), f"{month_savings/100:,.2f}")
        
    console.print(table)

def show_financial_health_score():
    """Calculates and displays a financial health score."""
    console.print("\n[bold]────── Financial Health Score ──────[/bold]")
    
    today = datetime.now()
    current_month_str = today.strftime("%Y-%m")
    
    # --- 1. Savings Rate Score (30 points) ---
    total_income, total_expenses, savings, expenses_by_cat = _get_monthly_data(current_month_str)
    savings_rate = (savings / total_income) * 100 if total_income > 0 else -100 # Penalize if no income
    
    if savings_rate >= 20:
        savings_score = 30
    elif savings_rate >= 10:
        savings_score = 20
    elif savings_rate > 0:
        savings_score = 10
    else:
        savings_score = 0

    # --- 2. Budget Adherence Score (25 points) ---
    budgets = _get_budgets()
    budget_score = 0
    if budgets:
        total_budget = sum(budgets.values())
        if total_budget > 0 and total_expenses <= total_budget:
            budget_score = 25  # Full points if under budget
        elif total_budget > 0:
            # Prorated score if over budget
            overspend_ratio = (total_expenses - total_budget) / total_budget
            budget_score = max(0, 25 - (overspend_ratio * 50))
    else:
        budget_score = 5 # Small score for not having budgets

    # --- 3. Income vs Expenses Score (25 points) ---
    inc_exp_ratio = total_income / total_expenses if total_expenses > 0 else 2
    if inc_exp_ratio >= 1.5: # Earning 50% more than you spend
        inc_exp_score = 25
    elif inc_exp_ratio >= 1: # Earning more than you spend
        inc_exp_score = 15
    else:
        inc_exp_score = 0

    # --- 4. Debt Management (20 points) ---
    # Placeholder - assuming no debt data for now
    debt_score = 20
    
    # --- Final Score ---
    total_score = int(savings_score + budget_score + inc_exp_score + debt_score)
    
    score_color = "red"
    if total_score >= 80:
        score_color = "green"
    elif total_score >= 50:
        score_color = "yellow"

    console.print(Panel(f"Your Financial Health Score is: [{score_color} bold]{total_score} / 100[/]", expand=False))

    # Breakdown
    table = Table(title="Score Breakdown", show_header=False)
    table.add_column(style="cyan")
    table.add_column(justify="right", style="bold")
    table.add_row("Savings Rate (>10%)", f"{int(savings_score)} / 30")
    table.add_row("Budget Adherence", f"{int(budget_score)} / 25")
    table.add_row("Income vs. Expenses", f"{int(inc_exp_score)} / 25")
    table.add_row("Debt Management (Assumed)", f"{int(debt_score)} / 20")
    console.print(table)
    
    # Recommendations
    recs = []
    if savings_score < 20: recs.append("💡 Try to increase your savings rate to at least 10-20% of your income.")
    if budget_score < 20 and not budgets: recs.append("💡 Set up monthly budgets to better track and control your spending.")
    if budget_score < 20 and budgets: recs.append("💡 You're overspending in some categories. Review your budget vs. actuals.")
    if inc_exp_score < 15: recs.append("💡 Your expenses are high compared to your income. Look for areas to cut back.")
    if not recs: recs.append("🎉 You're doing great! Keep up the good work.")
    
    console.print(Panel("\n".join(recs), title="Recommendations", style="bold blue"))


def analytics_menu():
    """Displays the analytics submenu."""
    analytics_actions = {
        "Spending Analysis": show_spending_analysis,
        "Income Analysis": show_income_analysis,
        "Savings Analysis": show_savings_analysis,
        "Financial Health Score": show_financial_health_score,
        "Back to Main Menu": None
    }
    
    while True:
        console.print("\n")
        console.print(Panel("[bold cyan]Financial Analytics[/bold cyan]", expand=False, border_style="yellow"))
        
        choice = questionary.select(
            "Analytics Options:",
            choices=list(analytics_actions.keys())
        ).ask()

        if choice is None or choice == "Back to Main Menu":
            break
            
        action = analytics_actions.get(choice)
        if action:
            action()
            input("\nPress Enter to return to the analytics menu...")
