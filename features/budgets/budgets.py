import questionary
from rich.console import Console
from rich.table import Table
from rich.progress_bar import ProgressBar
from datetime import datetime
import csv
import os

from features.transactions.transactions import _get_transactions

BUDGETS_FILE = "database/budgets.txt"
console = Console()

EXPENSE_CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Health", "Other"]

def _get_budgets():
    """Reads all budgets from the storage file."""
    if not os.path.exists(BUDGETS_FILE):
        return {}
    
    budgets = {}
    with open(BUDGETS_FILE, mode='r', newline='', encoding='utf-8') as file:
        try:
            reader = csv.reader(file)
            for row in reader:
                if row:
                    budgets[row[0]] = int(row[1])
        except (csv.Error, ValueError, IndexError) as e:
            console.print(f"[bold red]Error reading budgets file: {e}[/bold red]")
            return {}
    return budgets

def _save_budgets(budgets):
    """Saves all budgets to the storage file."""
    with open(BUDGETS_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for category, amount_paisa in budgets.items():
            writer.writerow([category, amount_paisa])

def set_budget():
    """Sets a monthly budget for a specific category."""
    console.print("\n[bold]────── Set Monthly Budget ──────[/bold]")
    try:
        category = questionary.select(
            "Select category to budget:",
            choices=EXPENSE_CATEGORIES
        ).ask()
        if category is None: return

        amount_str = questionary.text(
            f"Enter monthly budget for '{category}':",
            validate=lambda text: text.replace('.', '', 1).isdigit() or "Please enter a valid positive number."
        ).ask()
        if amount_str is None: return

        amount_paisa = int(float(amount_str) * 100)
        if amount_paisa <= 0:
            console.print("[bold red]Budget amount must be positive.[/bold red]")
            return

        budgets = _get_budgets()
        budgets[category] = amount_paisa
        _save_budgets(budgets)
        
        console.print(f"[bold green]✔ Budget for '{category}' set to {amount_paisa / 100:.2f}[/bold green]")

    except (KeyboardInterrupt, TypeError):
        console.print("\n[bold yellow]Operation cancelled.[/bold yellow]")

def view_budgets():
    """Displays budget status against actual spending for the current month."""
    console.print("\n[bold]────── Budget vs. Spending (Current Month) ──────[/bold]")
    budgets = _get_budgets()
    if not budgets:
        console.print("[bold yellow]No budgets set. Use 'Set Budget' to create one.[/bold yellow]")
        return

    transactions = _get_transactions()
    current_month = datetime.now().strftime("%Y-%m")
    
    spent_by_category = {cat: 0 for cat in EXPENSE_CATEGORIES}
    for t in transactions:
        if t['type'] == 'expense' and t['date'].startswith(current_month):
            if t['category'] in spent_by_category:
                spent_by_category[t['category']] += t['amount_paisa']

    table = Table(title="Monthly Budget Status", show_header=True, header_style="bold magenta")
    table.add_column("Category", style="cyan")
    table.add_column("Budget", justify="right")
    table.add_column("Spent", justify="right")
    table.add_column("Remaining", justify="right")
    table.add_column("Utilization", width=25)
    table.add_column("Status", justify="center")

    total_budget = 0
    total_spent = 0

    for category, budget_paisa in budgets.items():
        spent_paisa = spent_by_category.get(category, 0)
        remaining_paisa = budget_paisa - spent_paisa
        utilization = (spent_paisa / budget_paisa) * 100 if budget_paisa > 0 else 0

        total_budget += budget_paisa
        total_spent += spent_paisa

        budget_str = f"{budget_paisa / 100:,.2f}"
        spent_str = f"{spent_paisa / 100:,.2f}"
        remaining_str = f"{remaining_paisa / 100:,.2f}"
        
        status_style = "green"
        status_text = "OK"
        if utilization >= 100:
            status_style = "bold red"
            status_text = "OVER"
        elif utilization >= 70:
            status_style = "yellow"
            status_text = "WARN"

        progress_color = "red" if utilization > 100 else "yellow" if utilization > 70 else "green"
        
        # Clamp utilization for progress bar display
        display_utilization = min(utilization, 100)
        
        bar = ProgressBar(total=100, completed=display_utilization, width=20, complete_style=progress_color)


        table.add_row(
            category,
            budget_str,
            f"[{'red' if spent_paisa > 0 else 'white'}]{spent_str}[/]",
            f"[{'green' if remaining_paisa >= 0 else 'red'}]{remaining_str}[/]",
            bar,
            f"[{status_style}]{status_text}[/{status_style}]"
        )

    console.print(table)
    
    # --- Summary ---
    summary_table = Table(show_header=False, box=None, padding=(0, 2))
    summary_table.add_column(style="bold")
    summary_table.add_column(justify="right")
    
    total_remaining = total_budget - total_spent
    overall_utilization = (total_spent / total_budget) * 100 if total_budget > 0 else 0
    
    summary_table.add_row("Overall Budget:", f"[cyan]{total_budget / 100:,.2f}[/cyan]")
    summary_table.add_row("Total Spent:", f"[red]{total_spent / 100:,.2f}[/red]")
    summary_table.add_row("Total Remaining:", f"[{'green' if total_remaining >=0 else 'red'}]{total_remaining / 100:,.2f}[/]")
    
    console.print(summary_table)

    if total_spent > total_budget:
        console.print("[bold red]🚨 You are over your total monthly budget![/bold red]")
