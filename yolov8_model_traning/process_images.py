import os
import shutil
import random


# Function to move files
def move_files(data, split, existing_images_dir, images_dir, labels_dir):
    for img_file, label_file in data:
        # Move image files
        shutil.move(os.path.join(existing_images_dir, img_file),
                    os.path.join(images_dir, split, img_file))
        # Move label files
        shutil.move(os.path.join(existing_images_dir, label_file),
                    os.path.join(labels_dir, split, label_file))


def create_dataset_structure():
    # Define paths
    base_dir = '../dataset'
    images_dir = os.path.join(base_dir, 'images')
    labels_dir = os.path.join(base_dir, 'labels')

    # Create directories
    os.makedirs(os.path.join(images_dir, 'train'), exist_ok=True)
    os.makedirs(os.path.join(images_dir, 'val'), exist_ok=True)
    os.makedirs(os.path.join(images_dir, 'test'), exist_ok=True)
    os.makedirs(os.path.join(labels_dir, 'train'), exist_ok=True)
    os.makedirs(os.path.join(labels_dir, 'val'), exist_ok=True)
    os.makedirs(os.path.join(labels_dir, 'test'), exist_ok=True)

    # Path to your existing images and labels
    existing_images_dir = '../training_images'

    # Get all images and label files
    image_files = [f for f in os.listdir(existing_images_dir) if f.endswith('.png')]
    label_files = [f.replace('.png', '.txt') for f in image_files]

    # Shuffle data
    data = list(zip(image_files, label_files))
    random.shuffle(data)

    # Define split ratios
    train_ratio = 0.7
    val_ratio = 0.2
    test_ratio = 0.1

    # Calculate split indices
    train_idx = int(train_ratio * len(data))
    val_idx = int(val_ratio * len(data)) + train_idx

    # Split data
    train_data = data[:train_idx]
    val_data = data[train_idx:val_idx]
    test_data = data[val_idx:]

    # Move files to train, val, and test folders
    move_files(train_data, 'train', existing_images_dir, images_dir, labels_dir)
    move_files(val_data, 'val', existing_images_dir, images_dir, labels_dir)
    move_files(test_data, 'test', existing_images_dir, images_dir, labels_dir)

    print("Dataset structure created successfully!")

create_dataset_structure()
