import questionary
from rich.console import Console
from rich.panel import Panel
import os

# Import feature functions
from features.transactions.transactions import add_expense, add_income, list_transactions, show_balance

# Create necessary directories if they don't exist
os.makedirs("database", exist_ok=True)


console = Console()

def main():
    """Displays the main menu and handles user choices."""
    
    menu_actions = {
        "Add Expense": add_expense,
        "Add Income": add_income,
        "List Transactions": list_transactions,
        "Show Current Month Balance": show_balance,
        "Budget Management": lambda: console.print("\n[bold yellow]Budget management is coming soon![/bold yellow]"),
        "Financial Analytics": lambda: console.print("\n[bold yellow]Financial analytics are coming soon![/bold yellow]"),
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

        # Add a small pause for better UX
        if choice != "Exit":
            input("\nPress Enter to return to the main menu...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[bold red]Application interrupted. Goodbye![/bold red]")
