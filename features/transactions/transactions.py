import questionary
from rich.console import Console
from rich.table import Table
from datetime import datetime, timedelta
import csv
import os

TRANSACTIONS_FILE = "database/transactions.txt"
console = Console()

EXPENSE_CATEGORIES = ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Health", "Other"]
INCOME_CATEGORIES = ["Salary", "Freelance", "Business", "Investment", "Gift", "Other"]

def _get_transactions():
    """Reads all transactions from the storage file."""
    if not os.path.exists(TRANSACTIONS_FILE):
        return []
    
    transactions = []
    with open(TRANSACTIONS_FILE, mode='r', newline='', encoding='utf-8') as file:
        try:
            reader = csv.DictReader(file)
            for row in reader:
                row['amount_paisa'] = int(row['amount_paisa'])
                transactions.append(row)
        except (csv.Error, ValueError, KeyError) as e:
            console.print(f"[bold red]Error reading transactions file: {e}[/bold red]")
            return []
        except StopIteration:
            return []  # Empty file
    return transactions

def _write_transaction(transaction):
    """Writes a single transaction to the storage file."""
    file_exists = os.path.exists(TRANSACTIONS_FILE) and os.path.getsize(TRANSACTIONS_FILE) > 0
    with open(TRANSACTIONS_FILE, mode='a', newline='', encoding='utf-8') as file:
        fieldnames = ["date", "type", "category", "description", "amount_paisa"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(transaction)

def add_expense():
    """Adds a new expense transaction."""
    console.print("\n[bold red]────── Add Expense ──────[/bold red]")
    try:
        amount_str = questionary.text(
            "Enter amount:",
            validate=lambda text: text.replace('.', '', 1).isdigit() or "Please enter a valid positive number."
        ).ask()
        if amount_str is None: return

        amount_paisa = int(float(amount_str) * 100)
        if amount_paisa <= 0:
            console.print("[bold red]Amount must be positive.[/bold red]")
            return

        category = questionary.select(
            "Select category:",
            choices=EXPENSE_CATEGORIES
        ).ask()
        if category is None: return

        description = questionary.text("Enter description:").ask()
        if description is None: return

        date_str = questionary.text(
            "Enter date (YYYY-MM-DD) or leave empty for today:",
            default=datetime.now().strftime("%Y-%m-%d")
        ).ask()
        if date_str is None: return
        
        # Validate date format
        datetime.strptime(date_str, "%Y-%m-%d")

        transaction = {
            "date": date_str,
            "type": "expense",
            "category": category,
            "description": description,
            "amount_paisa": amount_paisa
        }
        _write_transaction(transaction)
        console.print("[bold green]✔ Expense added successfully![/bold green]")
    except (KeyboardInterrupt, TypeError):
        console.print("\n[bold yellow]Operation cancelled.[/bold yellow]")
    except ValueError:
        console.print("[bold red]Invalid date format. Please use YYYY-MM-DD.[/bold red]")


def add_income():
    """Adds a new income transaction."""
    console.print("\n[bold green]────── Add Income ──────[/bold green]")
    try:
        amount_str = questionary.text(
            "Enter amount:",
            validate=lambda text: text.replace('.', '', 1).isdigit() or "Please enter a valid positive number."
        ).ask()
        if amount_str is None: return

        amount_paisa = int(float(amount_str) * 100)
        if amount_paisa <= 0:
            console.print("[bold red]Amount must be positive.[/bold red]")
            return

        category = questionary.select(
            "Select source:",
            choices=INCOME_CATEGORIES
        ).ask()
        if category is None: return

        description = questionary.text("Enter description:").ask()
        if description is None: return

        date_str = questionary.text(
            "Enter date (YYYY-MM-DD) or leave empty for today:",
            default=datetime.now().strftime("%Y-%m-%d")
        ).ask()
        if date_str is None: return
        
        datetime.strptime(date_str, "%Y-%m-%d")

        transaction = {
            "date": date_str,
            "type": "income",
            "category": category,
            "description": description,
            "amount_paisa": amount_paisa
        }
        _write_transaction(transaction)
        console.print("[bold green]✔ Income added successfully![/bold green]")
    except (KeyboardInterrupt, TypeError):
        console.print("\n[bold yellow]Operation cancelled.[/bold yellow]")
    except ValueError:
        console.print("[bold red]Invalid date format. Please use YYYY-MM-DD.[/bold red]")


def list_transactions():
    """Lists all transactions with filtering options."""
    console.print("\n[bold]────── List Transactions ──────[/bold]")
    transactions = _get_transactions()
    if not transactions:
        console.print("[bold yellow]No transactions found.[/bold yellow]")
        return

    try:
        filter_choice = questionary.select(
            "Filter transactions:",
            choices=["All", "Last 7 days", "Current Month", "Expenses only", "Income only"]
        ).ask()
        if filter_choice is None: return

        today = datetime.now()
        seven_days_ago = today - timedelta(days=7)
        current_month_str = today.strftime("%Y-%m")

        filtered_transactions = []
        for t in transactions:
            try:
                transaction_date = datetime.strptime(t['date'], "%Y-%m-%d")
                if filter_choice == "All":
                    filtered_transactions.append(t)
                elif filter_choice == "Last 7 days" and transaction_date >= seven_days_ago:
                    filtered_transactions.append(t)
                elif filter_choice == "Current Month" and t['date'].startswith(current_month_str):
                    filtered_transactions.append(t)
                elif filter_choice == "Expenses only" and t['type'] == 'expense':
                    filtered_transactions.append(t)
                elif filter_choice == "Income only" and t['type'] == 'income':
                    filtered_transactions.append(t)
            except (ValueError, KeyError):
                console.print(f"[bold red]Skipping corrupted transaction record: {t}[/bold red]")


        if not filtered_transactions:
            console.print("[bold yellow]No transactions match the filter.[/bold yellow]")
            return

        filtered_transactions.sort(key=lambda x: x['date'], reverse=True)

        table = Table(title=f"Transactions ({filter_choice})", show_header=True, header_style="bold magenta")
        table.add_column("Date", style="cyan", width=12)
        table.add_column("Type", width=10)
        table.add_column("Category", style="yellow")
        table.add_column("Description", width=40)
        table.add_column("Amount", justify="right")

        for t in filtered_transactions:
            amount_str = f"{t['amount_paisa'] / 100:.2f}"
            style = "green" if t['type'] == 'income' else "red"
            type_str = f"[{style}]{t['type'].capitalize()}[/{style}]"
            table.add_row(
                t['date'],
                type_str,
                t['category'],
                t['description'],
                f"[{style}]{amount_str}[/]"
            )
        console.print(table)
    except (KeyboardInterrupt, TypeError):
        console.print("\n[bold yellow]Operation cancelled.[/bold yellow]")


def show_balance():
    """Shows the current month's financial balance."""
    console.print("\n[bold]────── Current Month's Balance ──────[/bold]")
    transactions = _get_transactions()
    current_month = datetime.now().strftime("%Y-%m")

    total_income = 0
    total_expenses = 0

    for t in transactions:
        if t['date'].startswith(current_month):
            if t['type'] == 'income':
                total_income += t['amount_paisa']
            else:
                total_expenses += t['amount_paisa']

    balance = total_income - total_expenses
    balance_color = "green" if balance >= 0 else "red"

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold")
    table.add_column(justify="right")
    table.add_row("Total Income:", f"[green]{total_income / 100:,.2f}[/green]")
    table.add_row("Total Expenses:", f"[red]{total_expenses / 100:,.2f}[/red]")
    table.add_row("─" * 20, "─" * 15)
    table.add_row("Net Balance:", f"[{balance_color}]{balance / 100:,.2f}[/{balance_color}]")
    
    console.print(table)
