from api import TabscannerClient

#hello this is a quick test edit
receipt = input("Enter path to receipt")
test_scanner = TabscannerClient()
items = test_scanner.scan(receipt)

username = input("Enter your name")

class Fridge:
    """
    Fridge class, inventory management
    """
    def __init__(self, username):
        self.fridge
        self.user = username

    def __repr__(self):
        """
        How is represented as an object in shell
        """
        pass

    def __str__(self):
        """
        How fridge is represented when print is called
        """
        pass

    def __contains__(self):
        """
        How x in fridge behaves
        - useful for has_items method
        """
        pass

    def add_item(self, item):
        pass


    def remove_item(self, item):
        pass

        
    def deduct_by_recipe(self):
        """
        Deducts all items in a recipe if has been cooked
        """
        pass
    
    def has_items(self):
        """
        For checking whether recipe matches given fridge
        """
        pass

    def load_from_receipt(self):
        """
        Directly add all items from scanned receipt into fridge
        """
        pass
    
    def save_fridge(self):
        """
        Save all items into json file
        """
        pass
    
    def clear_fridge(self):
        """
        Empty fridge
        """
        pass