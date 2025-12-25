from api import TabscannerClient
from tabulate import tabulate
import json


class Fridge:
    """
    Fridge class, inventory management
    """
    def __init__(self, username, nr_ingredients=0, inventory=None):
        self.user = username
        self.inventory = inventory if inventory else {}
        self.nr_ingredients = len(self.inventory)

    def __repr__(self):
        """
        How is represented as an object in shell
        """
        return f'Fridge({self.user}, nr_ingr: {self.nr_ingredients})'

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
        return item in self.inventory and self.inventory[item] > 0


    def add_item(self, item, qty):
        item = item.lower().strip()
        self.inventory[item] = self.inventory.get(item, 0) + qty
        self.nr_ingredients = len(self.inventory)
    
    def remove_item(self, item, qty): # change into dic pair if better for rest of code?
        item = item.lower().strip()
        if item in self.inventory:
            self.inventory[item] = max(0, self.inventory[item] - qty)
            if self.inventory[item] == 0:
                del self.inventory[item]
        self.nr_ingredients = len(self.inventory)

        
    def deduct_by_recipe(self, recipe):
        """
        Deducts all items in a recipe if has been cooked
        Output from Ollama recipe suggester:
                {
            "name": "Recipe Name",
            "ingredients": ["item1", "item2"],
            "steps": ["step1", "step2"]
        }
        """
        if self.has_items(recipe) == False:
            print('Cant be deducted since not available in fridge')
            return None
        for ingredient in recipe['ingredients']:
            self.remove_item(ingredient, 1) # need to see how we can match number of ingredients with recipe output
        self.nr_ingredients = len(self.inventory)
        print('Ingredients have been removed from recipe')

    
    def has_items(self, recipe):
        """
        For checking whether recipe matches given fridge
        CHECK: recipe doesn't include number of ingredients needed
        """
        for item in recipe['ingredients']:
            if item not in self.inventory:
                print(f"There is no {item} in fridge.")
                return False
        return True

    def load_from_receipt(self, receipt_dic):
        """
        Directly add all items from scanned receipt into fridge
        """
        for item, qty in receipt_dic.items():
            self.add_item(item, qty)
        self.nr_ingredients = len(self.inventory)
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
        self.nr_ingredients = len(self.inventory)



if __name__ == '__main__':
    # a = TabscannerClient()
    # items = a.scan(r"C:\2_MSc\IntroToPython\Project\IMG_8947.jpg")
    # print(items)
    items = {
        'milk': 2.0,
        'eggs': 1.0,
        'bread': 1.0
    }

    b = Fridge('Elvira')

    b.load_from_receipt(items)

    # Test deduct_by_recipe
    recipe = {
        'name': 'Omelette',
        'ingredients': ['eggs', 'milk'],
        'steps': ['beat eggs', 'cook']
    }
    b.deduct_by_recipe(recipe)
    print(b)