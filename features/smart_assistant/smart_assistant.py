from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from datetime import datetime
import calendar
import questionary

from features.transactions.transactions import _get_transactions
from features.budgets.budgets import _get_budgets
from features.analytics.analytics import _get_monthly_data

console = Console()

def _get_alerts():
    """Gathers all active financial alerts."""
    alerts = []
    today = datetime.now()
    current_month_str = today.strftime("%Y-%m")
    
    # --- Data Gathering ---
    budgets = _get_budgets()
    total_income, total_expenses, _, expenses_by_cat = _get_monthly_data(current_month_str)
    
    # --- Alert Generation ---
    # 1. Budget Warnings
    if budgets:
        for category, budget_paisa in budgets.items():
            spent_paisa = expenses_by_cat.get(category, 0)
            utilization = (spent_paisa / budget_paisa) * 100 if budget_paisa > 0 else 0
            if utilization >= 100:
                alerts.append(f"❗️ [bold red]OVERBUDGET:[/] You've spent {spent_paisa/100:,.2f} in '{category}', exceeding your budget of {budget_paisa/100:,.2f}.")
            elif utilization >= 80:
                alerts.append(f"⚠️ [yellow]Budget Warning:[/] You've used {utilization:.0f}% of your '{category}' budget.")

    # 2. Large Transaction Alert
    if total_income > 0:
        transactions = _get_transactions()
        large_tx_threshold = total_income * 0.2 # Transaction > 20% of monthly income
        for t in transactions:
            if t['date'].startswith(current_month_str) and t['type'] == 'expense' and t['amount_paisa'] > large_tx_threshold:
                alerts.append(f"💸 [cyan]Large Transaction:[/] A purchase of {t['amount_paisa']/100:,.2f} for '{t['description']}' was detected.")

    return alerts

def daily_financial_check():
    """Shows a smart daily financial check-up."""
    console.print(f"\n[bold]📊 Daily Financial Check ({datetime.now().strftime('%b %d, %Y')})[/bold]")
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    transactions = _get_transactions()
    
    # --- Today's Spending ---
    todays_spending = sum(t['amount_paisa'] for t in transactions if t['date'] == today_str and t['type'] == 'expense')
    console.print(f"\nToday's Spending: [bold red]{todays_spending/100:,.2f}[/bold red]")

    # --- Daily Budget ---
    budgets = _get_budgets()
    if budgets:
        total_budget = sum(budgets.values())
        _, num_days = calendar.monthrange(datetime.now().year, datetime.now().month)
        daily_budget = total_budget / num_days
        remaining_daily = daily_budget - todays_spending
        
        color = "green" if remaining_daily >= 0 else "red"
        console.print(f"Daily Budget Guideline: {daily_budget/100:,.2f}")
        console.print(f"Remaining for Today: [{color}]{remaining_daily/100:,.2f}[/{color}]")

    # --- Alerts ---
    alerts = _get_alerts()
    if alerts:
        alert_str = "\n".join(f"• {a}" for a in alerts)
        console.print(Panel(alert_str, title="[bold]Active Alerts[/bold]", border_style="yellow", expand=False))
    else:
        console.print("[green]✔ No immediate alerts.[/green]")

    # --- Quick Tip ---
    _, _, savings, _ = _get_monthly_data(datetime.now().strftime("%Y-%m"))
    tip = ""
    if not budgets:
        tip = "You don't have any budgets set. Creating them can help you gain control over your spending."
    elif todays_spending == 0:
        tip = "No spending today! Great job. Maybe transfer a small amount to your savings?"
    elif savings < 0:
        tip = "Your expenses are higher than your income this month. Look for opportunities to cut back."
    else:
        tip = "You're on track this month. Keep up the great work!"
    
    console.print(f"\n💡 [bold]Tip of the Day:[/] [i]{tip}[/i]")


def show_smart_recommendations():
    """Generates and displays personalized financial recommendations."""
    console.print("\n[bold]💡 Smart Recommendations[/bold]")
    
    recs = []
    today = datetime.now()
    current_month_str = today.strftime("%Y-%m")
    
    # Data gathering
    budgets = _get_budgets()
    total_income, total_expenses, savings, expenses_by_cat = _get_monthly_data(current_month_str)
    
    # Rule-based recommendations
    if not budgets:
        recs.append(("Set Budgets", "Create monthly budgets for top spending categories like 'Food' and 'Shopping' to gain better financial control."))
    else:
        overspent_cats = []
        for cat, spent in expenses_by_cat.items():
            budget = budgets.get(cat, 0)
            if budget > 0 and spent > budget:
                overspent_cats.append(cat)
        if overspent_cats:
            recs.append(("Reduce Overspending", f"You're over budget in {', '.join(overspent_cats)}. Review recent transactions in these areas to find potential savings."))

    savings_rate = (savings / total_income) * 100 if total_income > 0 else -100
    if savings_rate < 10:
        recs.append(("Improve Savings Rate", "Your savings rate is below 10%. Try adopting the 50/30/20 rule (50% needs, 30% wants, 20% savings) to boost it."))

    if total_income == 0:
        recs.append(("Track Income", "No income has been recorded this month. Make sure to log all income sources to get a clear financial picture."))
        
    if not recs:
        recs.append(("Great Job!", "You're managing your finances well. Consider setting a new savings goal or increasing your investment contributions."))

    table = Table(box=None, show_header=False)
    table.add_column(width=20, style="bold cyan")
    table.add_column()
    for title, desc in recs:
        table.add_row(f"• {title}", desc)
    console.print(table)


def smart_assistant_menu():
    """Displays the smart assistant submenu."""
    assistant_actions = {
        "Daily Financial Check": daily_financial_check,
        "Smart Recommendations": show_smart_recommendations,
        # "Savings Opportunities": lambda: console.print("Coming soon!"),
        # "Set Financial Goals": lambda: console.print("Coming soon!"),
        "Back to Main Menu": None
    }
    
    while True:
        console.print("\n")
        console.print(Panel("[bold cyan]🤖 Smart Financial Assistant[/bold cyan]", expand=False, border_style="yellow"))
        
        choice = questionary.select(
            "Assistant Options:",
            choices=list(assistant_actions.keys())
        ).ask()

        if choice is None or choice == "Back to Main Menu":
            break
            
        action = assistant_actions.get(choice)
        if action:
            action()
            input("\nPress Enter to return to the assistant menu...")
