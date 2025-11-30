import questionary
from rich.console import Console
import os
import csv
import json
import shutil
from datetime import datetime

from features.transactions.transactions import _get_transactions, _write_transaction

console = Console()
DATABASE_DIR = "database"
EXPORTS_DIR = "exports"
BACKUPS_DIR = "backups"
TRANSACTIONS_FILE = os.path.join(DATABASE_DIR, "transactions.txt")

def _ensure_dirs():
    """Ensure that directories for exports and backups exist."""
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    os.makedirs(BACKUPS_DIR, exist_ok=True)

def export_transactions_csv():
    """Exports all transactions to a CSV file."""
    _ensure_dirs()
    transactions = _get_transactions()
    if not transactions:
        console.print("[yellow]No transactions to export.[/yellow]")
        return
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(EXPORTS_DIR, f"transactions_{timestamp}.csv")
    
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=transactions[0].keys())
        writer.writeheader()
        writer.writerows(transactions)
        
    console.print(f"[green]✔ Successfully exported {len(transactions)} transactions to {filename}[/green]")

def export_transactions_json():
    """Exports all transactions to a JSON file."""
    _ensure_dirs()
    transactions = _get_transactions()
    if not transactions:
        console.print("[yellow]No transactions to export.[/yellow]")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(EXPORTS_DIR, f"transactions_{timestamp}.json")

    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(transactions, file, indent=4)
        
    console.print(f"[green]✔ Successfully exported {len(transactions)} transactions to {filename}[/green]")


def import_transactions_csv():
    """Imports transactions from a user-specified CSV file."""
    console.print("\n[bold]⚠️ Transaction Import[/bold]")
    console.print("The CSV must have headers: date,type,category,description,amount_paisa")
    
    try:
        filepath = questionary.text("Enter the full path to the CSV file:").ask()
        if not filepath or not os.path.exists(filepath):
            console.print("[red]File not found or path is empty.[/red]")
            return

        with open(filepath, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            new_transactions = list(reader)

        # Basic validation
        required_headers = {"date", "type", "category", "description", "amount_paisa"}
        if not new_transactions or not required_headers.issubset(new_transactions[0].keys()):
            console.print("[red]Invalid CSV format or missing headers.[/red]")
            return
            
        # Deduplication
        existing_transactions = _get_transactions()
        existing_ids = {f"{t['date']}-{t['type']}-{t['amount_paisa']}-{t['description']}" for t in existing_transactions}
        
        transactions_to_add = []
        for t in new_transactions:
            t_id = f"{t['date']}-{t['type']}-{t['amount_paisa']}-{t['description']}"
            if t_id not in existing_ids:
                # Further validation
                try:
                    t['amount_paisa'] = int(t['amount_paisa'])
                    datetime.strptime(t['date'], "%Y-%m-%d")
                    transactions_to_add.append(t)
                except (ValueError, TypeError):
                    console.print(f"[yellow]Skipping invalid record: {t}[/yellow]")
                    continue

        if not transactions_to_add:
            console.print("[yellow]No new, unique transactions to import.[/yellow]")
            return
            
        console.print(f"Found {len(transactions_to_add)} new transactions.")
        confirm = questionary.confirm("Do you want to import these transactions?").ask()

        if confirm:
            for t in transactions_to_add:
                _write_transaction(t)
            console.print(f"[green]✔ Successfully imported {len(transactions_to_add)} transactions.[/green]")
        else:
            console.print("[yellow]Import cancelled.[/yellow]")

    except Exception as e:
        console.print(f"[bold red]An error occurred during import: {e}[/bold red]")


def create_backup():
    """Creates a timestamped zip archive of the database directory."""
    _ensure_dirs()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = os.path.join(BACKUPS_DIR, f"backup-{timestamp}")
    
    try:
        shutil.make_archive(backup_filename, 'zip', DATABASE_DIR)
        console.print(f"[green]✔ Backup created successfully: {backup_filename}.zip[/green]")
        
        # Auto-cleanup old backups (keep last 10)
        backups = sorted(os.listdir(BACKUPS_DIR), reverse=True)
        if len(backups) > 10:
            for old_backup in backups[10:]:
                os.remove(os.path.join(BACKUPS_DIR, old_backup))
            console.print("[cyan]Cleaned up old backups.[/cyan]")

    except Exception as e:
        console.print(f"[bold red]Backup failed: {e}[/bold red]")

def data_management_menu():
    """Displays the data management submenu."""
    menu_actions = {
        "Export Transactions to CSV": export_transactions_csv,
        "Export Transactions to JSON": export_transactions_json,
        "Import Transactions from CSV": import_transactions_csv,
        "Create Backup": create_backup,
        "Back to Main Menu": None
    }
    
    while True:
        console.print("\n")
        console.print(Panel("[bold cyan]🗃️ Data Management[/bold cyan]", expand=False, border_style="yellow"))
        
        choice = questionary.select(
            "Data Options:",
            choices=list(menu_actions.keys())
        ).ask()

        if choice is None or choice == "Back to Main Menu":
            break
            
        action = menu_actions.get(choice)
        if action:
            action()
            input("\nPress Enter to return to the data menu...")
