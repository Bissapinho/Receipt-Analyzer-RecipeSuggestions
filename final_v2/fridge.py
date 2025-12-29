from api import TabscannerClient
from tabulate import tabulate
import json
import os


class Fridge:
    """
    The Fridge class tracks items and quantities, supports loading from scanned receipts,
    saving/loading from persistent JSON storage, and deducting ingredients after cooking recipes.

    Usage:
        # Create or load existing fridge
        fridge = Fridge.load_fridge('username')
        
        # Add items from receipt
        fridge.load_from_receipt({'milk': 2, 'eggs': 12})
        
        # Check and deduct recipe ingredients
        if fridge.has_items(recipe):
            fridge.deduct_by_recipe(recipe)
        
        # Save to persistent storage
        fridge.save_fridge()
    
    Storage Format:
    JSON file with structure: {username: {'inventory': {item: qty, ...}}, ...}
    """
    def __init__(self, username, nr_ingredients=0, inventory=None):
        self.user = username
        self.inventory = inventory if inventory else {}
        self.nr_ingredients = len(self.inventory)

    def __repr__(self):
        return f'Fridge({self.user}, nr_ingr: {self.nr_ingredients})'

    def __str__(self):
        """
        When print is called, fridge is represented as a table with all ingredients contained in fridge and their quantity.
        """
        if not self.inventory:
            return f"{self.user}'s Fridge is empty"

        # Convert dict to list of lists
        table_data = [[k, v] for k, v in self.inventory.items()]
        return f"{self.user}'s Fridge:\n" + tabulate(table_data, headers=["Item", "Quantity"], tablefmt="grid")

    def __contains__(self, item):
        """
        How x in Fridge() behaves.
        Returns true if item is in inventory.
        """
        item = item.lower().strip()
        return item in self.inventory and self.inventory[item] > 0


    def add_item(self, item, qty):
        """
        Adds a single food item and a quantity to the inventory of a fridge.
        """
        item = item.lower().strip()
        self.inventory[item] = self.inventory.get(item, 0) + qty
        self.nr_ingredients = len(self.inventory)
    
    def remove_item(self, item, qty):
        """
        Removes a single food item and a quantity of it from a fridge's inventory.
        """
        item = item.lower().strip()
        if item in self.inventory:
            self.inventory[item] = max(0, self.inventory[item] - qty)
            if self.inventory[item] == 0:
                del self.inventory[item]
        self.nr_ingredients = len(self.inventory)

        
    def deduct_by_recipe(self, recipe):
        """
        Deducts all items in a recipe if has been chosen.

        Paramater 'recipe':
            Output from Ollama recipe suggester:
                # Example:
                    {
                "name": "Recipe Name",
                "ingredients": ["item1", "item2"],
                "steps": ["step1", "step2"]
            }

        Notes:
        - If more than 1 unit is needed in the recipe, LLM will output this ingredient several times, so it will be deducted
            the amount of times that it is needed
        """
        if self.has_items(recipe) == False:
            print('Cant be deducted since not available in fridge')
            return None
        for ingredient in recipe['ingredients']:
            self.remove_item(ingredient, 1) # need to see how we can match number of ingredients with recipe output
        self.nr_ingredients = len(self.inventory)
        print('Ingredients have been removed from recipe')
        print(f'Inventory left in fridge is: \n {self.inventory}')

    
    def has_items(self, recipe):
        """
        For checking whether recipe matches items given in fridge.
        """
        for item in recipe['ingredients']:
            if item not in self.inventory:
                print(f"There is no {item} in fridge.")
                return False
        return True

    def load_from_receipt(self, receipt_dic):
        """
        Directly adds all items from scanned receipt into fridge.

        Parameters:
        'receipt_dic':
            # dictionary with ingredient as key and quantity as value
            # example:
                {'ingredient1': 1.0,
                'ingredient2': 1.0,
                'ingredient3': 1.0}
        """
        for item, qty in receipt_dic.items():
            self.add_item(item, qty)
        self.nr_ingredients = len(self.inventory)
        print('Items have been added to fridge!')
            
    
    def save_fridge(self, filename='data/all_fridges.json'):
        """
        Stores fridges and their inventory into json file, according to username.
        Can later be restored using load_fridge() method.
        """
        # Load or create new file
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                all_data = json.load(f)
        else:
            all_data = {}
        
        # Update users fridge:
        all_data[self.user] = {'inventory': self.inventory}

        with open(filename, 'w') as f:
            json.dump(all_data, f, indent=2)

    
    def clear_fridge(self, confirm=True):
        """
        Empties fridge's inventory. When confirm is True, asks for CLI confirmation; when False, clears immediately (for non-interactive calls like the web app).
        """
        if confirm:
            double_checker = input('Are you sure you want to delete all items from fridge? [Yes/No] \n')
            if double_checker != 'Yes':
                self.nr_ingredients = len(self.inventory)
                return

        self.inventory = {}
        print('All items deleted from fridge')
        self.nr_ingredients = len(self.inventory)
    
    @classmethod # creates a new instance of fridge by loading from json file
    def load_fridge(cls, user, filename='data/all_fridges.json'):
        """
        Loads a user's stored fridge from json file if available.
        Otherwise, creates a new Fridge() object.
        """
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            return cls(user, inventory=data[user]['inventory'])
        except (FileNotFoundError, KeyError):
            # Create new fridge if file doesn't exist or user not in file
            return cls(user)


# if __name__ == '__main__':
#     # a = TabscannerClient()
#     # items = a.scan(r"C:\2_MSc\IntroToPython\Project\IMG_8947.jpg")
#     # print(items)
#     items = {
#         'milk': 2.0,
#         'eggs': 1.0,
#         'bread': 1.0
#     }

#     b = Fridge('Elvira')

#     b.load_from_receipt(items)

#     # Test deduct_by_recipe
#     recipe = {
#         'name': 'Omelette',
#         'ingredients': ['eggs', 'milk'],
#         'steps': ['beat eggs', 'cook']
#     }
#     b.deduct_by_recipe(recipe)
#     print(b)