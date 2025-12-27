from fridge import Fridge


def show_dashboard(user):
    """Summarizes fridge status and recent history for V2 UI."""
    print("\n" + "=" * 30)
    print(f"📊 {user.upper()}'S DASHBOARD")
    print("=" * 30)

    # 1. Top Inventory
    fridge = Fridge.load_fridge(user)
    inv = fridge.inventory
    print(f"\n[ Top Stock ]")
    if not inv:
        print("Fridge is empty.")
    else:
        # Sort by quantity descending
        for item, qty in sorted(inv.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f" - {item}: {qty}")

    # 2. Recent History
    print(f"\n[ Recent Activity ]")
    try:
        with open("history_log.txt", "r", encoding="utf-8") as f:
            lines = f.readlines()
            # Filter for accepted recipes in log
            history = [l.strip() for l in lines if "Accepted:" in l]
            for record in history[-5:]:  # Show last 5
                print(f"  {record}")
    except FileNotFoundError:
        print("No history logs found.")

    print("=" * 30)