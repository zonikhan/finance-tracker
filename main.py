import questionary
from rich.console import Console
from rich.panel import Panel
import os

# Import feature functions
from features.transactions.transactions import add_expense, add_income, list_transactions, show_balance
from features.budgets.budgets import set_budget, view_budgets
from features.analytics.analytics import analytics_menu
from features.smart_assistant.smart_assistant import smart_assistant_menu
from features.data_management.data_management import data_management_menu

# Create necessary directories if they don't exist
os.makedirs("database", exist_ok=True)


console = Console()

def budget_menu():
    """Displays the budget management submenu."""
    budget_actions = {
        "Set Budget": set_budget,
        "View Budgets": view_budgets,
        "Back to Main Menu": None
    }
    
    while True:
        console.print("\n")
        console.print(Panel("[bold cyan]Budget Management[/bold cyan]", expand=False, border_style="yellow"))
        
        choice = questionary.select(
            "Budget Options:",
            choices=list(budget_actions.keys())
        ).ask()

        if choice is None or choice == "Back to Main Menu":
            break
            
        action = budget_actions.get(choice)
        if action:
            action()
            input("\nPress Enter to return to the budget menu...")


def main():
    """Displays the main menu and handles user choices."""
    
    menu_actions = {
        "Add Expense": add_expense,
        "Add Income": add_income,
        "List Transactions": list_transactions,
        "Show Current Month Balance": show_balance,
        "Budget Management": budget_menu,
        "Financial Analytics": analytics_menu,
        "Smart Assistant": smart_assistant_menu,
        "Data Management": data_management_menu,
        "Exit": None
    }
    
    while True:
        console.print("\n")
        console.print(Panel("[bold cyan]Personal Finance Tracker[/bold cyan]", title="💰", expand=False, border_style="green"))
        
        choice = questionary.select(
            "What would you like to do?",
            choices=list(menu_actions.keys())
        ).ask()

        if choice is None or choice == "Exit":
            console.print("[bold yellow]Goodbye![/bold yellow]")
            break
        
        action = menu_actions.get(choice)
        if action:
            action()

        # Add a small pause for better UX for sub-menus
        if choice not in ["Budget Management", "Financial Analytics", "Smart Assistant", "Data Management", "Exit"]:
             input("\nPress Enter to return to the main menu...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[bold red]Application interrupted. Goodbye![/bold red]")
