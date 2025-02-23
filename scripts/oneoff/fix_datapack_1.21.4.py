#!/usr/bin/env python
from pathlib import Path
import json


def process_json_file(file_path):
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        modified = False

        # Check if it's a shaped recipe and modify it
        if data.get("type") == "minecraft:crafting_shaped":
            for key, value in data.get("key", {}).items():
                if isinstance(value, dict) and "item" in value:
                    data["key"][key] = value["item"]  # Simplify key
                    modified = True

        # Check if it's a shapeless recipe and modify it
        elif data.get("type") == "minecraft:crafting_shapeless":
            new_ingredients = []
            for ingredient in data.get("ingredients", []):
                if isinstance(ingredient, dict) and "item" in ingredient:
                    new_ingredients.append(ingredient["item"])
                    modified = True
                else:
                    new_ingredients.append(ingredient)
            data["ingredients"] = new_ingredients

        elif data.get("type") == "minecraft:stonecutting":
            ingredient = data.get("ingredient")
            if isinstance(ingredient, dict) and "item" in ingredient:
                data["ingredient"] = ingredient["item"]
                modified = True

        # Write back if modified
        if modified:
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"Updated: {file_path}")
        else:
            print(f"No changes needed: {file_path}")

    except (json.JSONDecodeError, OSError) as e:
        print(f"Error processing {file_path}: {e}")


def find_and_process_json_files(directory):
    directory = Path(directory)
    for file_path in directory.rglob("*.json"):
        if "recipe" in file_path.parts:  # Ensure it's in a 'recipe' folder
            process_json_file(file_path)


if __name__ == "__main__":
    base_directory = Path.cwd()  # Change this if needed
    find_and_process_json_files(base_directory)
