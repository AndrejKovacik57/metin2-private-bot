import os

# Define characters and combinations
characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
combinations = [a + b for a in characters for b in characters]
combo_to_id = {combo: idx for idx, combo in enumerate(combinations)}

# Number of classes
num_classes = len(combo_to_id)

# Define paths to your dataset
train_images_path = '../dataset/images/train'
val_images_path = '../dataset/images/val'

# Create YAML content
yaml_content = f"""
# YOLOv8 configuration for training

train: {train_images_path}
val: {val_images_path}

# Number of classes
nc: {num_classes}

# Class names
names: {list(combo_to_id.keys())}
"""

# Write to data.yaml file
yaml_file_path = 'data.yaml'
with open(yaml_file_path, 'w') as yaml_file:
    yaml_file.write(yaml_content)

print(f"'data.yaml' file created successfully with {num_classes} classes!")
print(f"YAML file saved at: {os.path.abspath(yaml_file_path)}")
