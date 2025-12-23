from api import TabscannerClient
from tabulate import tabulate
import json

receipt = input("Enter path to receipt: \n")
test_scanner = TabscannerClient()
items2 = test_scanner.scan(f"{receipt}")

username = input("Enter your name: \n")

class Fridge:
    """
    Fridge class, inventory management
    """
    def __init__(self, username, nr_ingredients, inventory=None):
        self.user = username
        self.nr_ingredients = len(inventory)
        self.inventory = inventory if inventory else {}

    def __repr__(self):
        """
        How is represented as an object in shell
        """
        return f'Fridge({self.name}, nr_ingr: {self.nr_ingredients}'

    def __str__(self):
        """
        How fridge is represented when print is called
        """
        if not self.inventory:
            return f"{self.user}'s Fridge is empty"

        # Convert dict to list of lists
        table_data = [[k, v] for k, v in self.inventory.items()]
        return f"{self.user}'s Fridge:\n" + tabulate(table_data, headers=["Item", "Quantity"], tablefmt="grid")

    def __contains__(self, item):
        """
        How x in fridge behaves
        will return true is item is in inventory
        """
        item = item.lower().strip()
        if item in self.inventory and self.inventory[item] > 0:
            return True

    def add_item(self, item, qty):
        item = item.lower().strip()
        self.inventory[item] = self.inventory.get(item, 0) + qty
    
    def remove_item(self, item, qty):
        item = item.lower().strip()
        if item in self.inventory:
            self.inventory[item] = max(0, self.inventory[item] - qty)

        
    def deduct_by_recipe(self, recipe):
        """
        Deducts all items in a recipe if has been cooked
        """
        for ingredient, qty in recipe:
            self.remove_item(ingredient, qty)
    
    def has_items(self, recipe):
        """
        For checking whether recipe matches given fridge
        """
        for item in recipe:
            if item not in self.inventory:
                return f"There in no {item} in fridge."
            else:
                return True

    def load_from_receipt(self, receipt_dic):
        """
        Directly add all items from scanned receipt into fridge
        """
        for item, qty in receipt_dic:
            self.add_item(item, qty)
        print('Items have been added to fridge!')
        
    
    def save_fridge(self, filename=None):
        """
        Save all items into json file
        """
        if filename is None:
            filename = f'{self.user}_fridge.json'
        data = {
            'username': self.user,
            'inventory': self.inventory
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)  # indent=2 makes it readable

    
    def clear_fridge(self):
        """
        Empty fridge
        """
        double_checker = input('Are you sure you want to delete all items from fridge? [Yes/No] \n')
        if double_checker == 'Yes':
            self.inventory = {}
            print('All items deleted from fridge')