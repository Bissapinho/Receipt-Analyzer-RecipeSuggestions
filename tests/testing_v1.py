import unittest
import json
import os
from resources.fridge import Fridge
from resources.recipe_suggester_ollama import RecipeSuggesterOllama

##############################
# Run testing in terminal from project root so that all scripts can be accessed:
#
# With unittest:
#   - built-in python library
#   - no install needed
# Run:
#   python -m unittest tests.testing_v1 -v
#
# With pytest:
#   - third-party package
#   - needs to be installed via 'pip install pytest'
# Run:
#   python -m pytest tests/testing_v1.py -v
##############################

class TestFridge(unittest.TestCase):
    """Basic tests for Fridge class."""

    def setUp(self):
        self.fridge = Fridge("test_user")
        self.test_file = "test_fridges.json"

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_add_item(self):
        """Test adding items to fridge."""
        self.fridge.add_item("apple", 3)
        self.assertEqual(self.fridge.inventory["apple"], 3)

    def test_remove_item(self):
        """Test removing items from fridge."""
        self.fridge.add_item("apple", 5)
        self.fridge.remove_item("apple", 2)
        self.assertEqual(self.fridge.inventory["apple"], 3)

    def test_contains_operator(self):
        """Test checking if item is in fridge."""
        self.fridge.add_item("apple", 2)
        self.assertIn("apple", self.fridge)
        self.assertNotIn("orange", self.fridge)

    def test_save_and_load(self):
        """Test saving and loading fridge from file."""
        self.fridge.add_item("apple", 4)
        self.fridge.add_item("milk", 2)
        self.fridge.save_fridge(self.test_file)
        
        loaded_fridge = Fridge.load_fridge("test_user", self.test_file)
        self.assertEqual(loaded_fridge.inventory["apple"], 4)
        self.assertEqual(loaded_fridge.inventory["milk"], 2)


class TestRecipeSuggester(unittest.TestCase):
    """Basic tests for RecipeSuggesterOllama."""

    def setUp(self):
        self.suggester = RecipeSuggesterOllama(model="llama3.2")

    def test_initialization(self):
        """Test suggester initializes correctly."""
        self.assertEqual(self.suggester.model, "llama3.2")

    def test_prompt_building(self):
        """Test that prompt is built with inventory items."""
        inventory = {"apple": 2, "milk": 1}
        prompt = self.suggester._build_prompt(inventory, n_recipes=3)
        
        self.assertIn("apple", prompt)
        self.assertIn("milk", prompt)
        self.assertIn("3 recipes", prompt)

    def test_clean_json_with_markdown(self):
        """Test JSON cleaning removes markdown code blocks."""
        text = "```json\n[{\"name\": \"recipe\"}]\n```"
        cleaned = self.suggester._clean_json(text)
        
        self.assertIn("[", cleaned)
        self.assertIn("]", cleaned)
        self.assertNotIn("```", cleaned)


class TestAPI(unittest.TestCase):
    """Basic tests for API utilities."""

    def test_clean_ocr_item(self):
        """Test OCR item cleaning."""
        from resources.api import clean_ocr_item
        
        # Test price removal
        item, qty = clean_ocr_item("apple 2.50€", 1.0)
        self.assertEqual(item, "apple")
        
        # Test case normalization
        item, qty = clean_ocr_item("MILK", 1.0)
        self.assertEqual(item, "milk")
        
        # Test whitespace cleanup
        item, qty = clean_ocr_item("  bread  ", 1.0)
        self.assertEqual(item, "bread")


class TestMainFunctions(unittest.TestCase):
    """Basic tests for main.py functions."""

    def setUp(self):
        self.test_usernames_file = "test_usernames.json"
        self.test_fridges_file = "test_fridges.json"

    def tearDown(self):
        if os.path.exists(self.test_usernames_file):
            os.remove(self.test_usernames_file)
        if os.path.exists(self.test_fridges_file):
            os.remove(self.test_fridges_file)

    def test_prompt_username_creates_file(self):
        """Test that prompt_username creates usernames file."""
        from main import prompt_username
        from unittest.mock import patch
        
        with patch('builtins.input', return_value='newuser'):
            user = prompt_username(self.test_usernames_file)
        
        self.assertEqual(user, 'newuser')
        self.assertTrue(os.path.exists(self.test_usernames_file))

    def test_prompt_username_persists(self):
        """Test that existing usernames are loaded."""
        # Create initial file
        with open(self.test_usernames_file, 'w') as f:
            json.dump(['user1'], f)
        
        from main import prompt_username
        from unittest.mock import patch
        
        with patch('builtins.input', return_value='user2'):
            prompt_username(self.test_usernames_file)
        
        with open(self.test_usernames_file, 'r') as f:
            usernames = json.load(f)
        
        self.assertIn('user1', usernames)
        self.assertIn('user2', usernames)


if __name__ == "__main__":
    unittest.main(verbosity=2)
