#!/usr/bin/env python
# Convert seed lines into ones with replacement
import re
from pathlib import Path

pattern = re.compile(r"(\d{10,})")

# Define a function to transform the input lines based on folder name
def transform_line(line, suffix):
    # Regex pattern to match the number at the end of the line
    match = pattern.search(line)

    if match:
        # Extract the number and shorten it by trimming the last 10 digits
        number = match.group(0)
        shortened_number = number[:-7]
        # Replace the original number with the shortened number and append the appropriate suffix
        return pattern.sub(f"{shortened_number}{{{{ {suffix} }}}}", line)
    return line


# Function to process a single file
def process_file(file_path, suffix):
    with file_path.open("r") as infile:
        lines = infile.readlines()

    # Apply transformation to each line
    transformed_lines = [transform_line(line, suffix) for line in lines]

    # Write the transformed lines to the same file (or another if you prefer)
    with file_path.open("w") as outfile:
        outfile.writelines(transformed_lines)

    print(f"Processed {file_path}")


# Function to get the appropriate suffix based on folder name
def get_suffix_from_folder_name(folder_name):
    if folder_name == "world":
        return "FEATURE_SEED_SUFFIX_OVERWORLD"
    elif folder_name == "world_nether":
        return "FEATURE_SEED_SUFFIX_NETHER"
    elif folder_name == "world_the_end":
        return "FEATURE_SEED_SUFFIX_END"
    raise ValueError(folder_name)


# Function to find and process all paper-world.yml files in any 'world*' folder
def process_all_world_files(root_directory):
    # Use pathlib to find all paper-world.yml files in folders starting with 'world'
    world_folders = Path(root_directory).glob("world*/paper-world.yml")

    # Process each found file
    for world_file in world_folders:
        # Extract folder name from the path
        folder_name = str(world_file.parent)

        # Get the correct suffix based on the folder name
        suffix = get_suffix_from_folder_name(folder_name)

        # Process the file with the determined suffix
        process_file(world_file, suffix)


# Example usage:
root_directory = "."  # Starting directory, you can modify this if needed
process_all_world_files(root_directory)

print("Processing complete.")
