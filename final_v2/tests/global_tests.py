import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from api import clean_ocr_item 
from fridge import Fridge
from recipe_suggester_ollama import RecipeSuggesterOllama


#This file is the conglomerate of all jupyter notebooks we used for testing our code
#Each function tests one or more feature we had issues with

def test_clean_ocr_item():
    print("\nTEST clean_ocr_item")

    samples = [
        ("BANANES VRAC 0,156 kg 1.99 €/kg", 1),
        ("LINGUINE BARILLA 500G", 1),
        ("SAC KRAFT BRUN POIGNEES", 1),
        ("FILETS DE HARENGS FUMES", 1),
    ]

    for raw_name, qty in samples:
        name, q = clean_ocr_item(raw_name, qty)
        print(f"RAW: {raw_name}")
        print(f" -> CLEAN: {name}, QTY: {q}")
        print("-" * 40)



def test_fridge_basic_operations():
    print("\nTEST Fridge basic operations")

    fridge = Fridge("test_user")

    fridge.add_item("milk", 2)
    fridge.add_item("eggs", 6)
    fridge.add_item("banana", 0.3)

    print(fridge)

    assert "milk" in fridge
    assert "eggs" in fridge

    fridge.remove_item("eggs", 2)
    print("\nAfter removing eggs:")
    print(fridge)


def test_load_from_receipt():
    print("\nTEST load_from_receipt")

    receipt_data = {
        "milk": 1.0,
        "eggs": 12.0,
        "cheese": 0.2
    }

    fridge = Fridge("receipt_user")
    fridge.load_from_receipt(receipt_data)

    print(fridge)
    assert fridge.inventory["milk"] == 1.0
    assert fridge.inventory["eggs"] == 12.0


def test_deduct_by_recipe():
    print("\nTEST deduct_by_recipe")

    fridge = Fridge("cook_user")
    fridge.load_from_receipt({
        "egg": 3,
        "milk": 1
    })

    recipe = {
        "name": "Simple Omelette",
        "ingredients": ["egg", "egg", "milk"],
        "steps": ["Beat eggs", "Cook"]
    }

    if fridge.has_items(recipe):
        fridge.deduct_by_recipe(recipe)

    print("\nAfter cooking:")
    print(fridge)


def test_recipe_suggester():
    print("\nTEST RecipeSuggesterOllama")

    inventory = {
        "egg": 2,
        "milk": 1,
        "cheese": 0.2
    }

    suggester = RecipeSuggesterOllama()
    recipes = suggester.suggest(inventory, n_recipes=2)

    print("\nSuggested recipes:")
    for r in recipes:
        print(f"- {r.get('name')}")
        print(f"  Ingredients: {r.get('ingredients')}")
        print(f"  Steps: {r.get('steps')}")
        print("-" * 30)


if __name__ == "__main__":
    print("\n")
    print(" RUNNING PROJECT TEST SUITE ")
    print("------------------------")

    test_clean_ocr_item()
    test_fridge_basic_operations()
    test_load_from_receipt()
    test_deduct_by_recipe()

    
    test_recipe_suggester()
