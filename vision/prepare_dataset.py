#!/usr/bin/env python3
"""
Prepare collected training data for YOLO8 training
- Organize images
- Split into train/val/test sets
- Create dataset.yaml for YOLO8
- Package for transfer to training computer

Usage:
    python3 prepare_dataset.py --input training_data --output dataset
"""

import argparse
import shutil
import random
import yaml
from pathlib import Path
from collections import defaultdict


def prepare_dataset(input_dir, output_dir, train_split=0.7, val_split=0.2, test_split=0.1):
    """
    Prepare dataset for YOLO8 training

    Directory structure will be:
    dataset/
    ├── images/
    │   ├── train/
    │   ├── val/
    │   └── test/
    ├── labels/  (empty - to be labeled in Roboflow)
    │   ├── train/
    │   ├── val/
    │   └── test/
    └── dataset.yaml
    """

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Create output directories
    for split in ['train', 'val', 'test']:
        (output_path / 'images' / split).mkdir(parents=True, exist_ok=True)
        (output_path / 'labels' / split).mkdir(parents=True, exist_ok=True)

    # Collect all images by class
    images_by_class = defaultdict(list)

    for class_dir in input_path.iterdir():
        if not class_dir.is_dir():
            continue

        class_name = class_dir.name

        # Recursively find all images
        for img_file in class_dir.rglob('*.jpg'):
            images_by_class[class_name].append(img_file)

    if not images_by_class:
        print(f"No images found in {input_dir}")
        return

    # Display statistics
    print("\n" + "="*60)
    print("DATASET PREPARATION")
    print("="*60)
    print(f"Input: {input_dir}")
    print(f"Output: {output_dir}")
    print(f"\nSplit ratios: Train {train_split:.0%} | Val {val_split:.0%} | Test {test_split:.0%}")
    print(f"\nImages found:")

    total_images = 0
    for class_name, images in images_by_class.items():
        print(f"  {class_name}: {len(images)}")
        total_images += len(images)

    print(f"\nTotal: {total_images}")

    # Split and copy images
    print("\nSplitting dataset...")

    split_counts = {'train': 0, 'val': 0, 'test': 0}

    for class_name, images in images_by_class.items():
        # Shuffle images
        random.shuffle(images)

        # Calculate split indices
        n_images = len(images)
        n_train = int(n_images * train_split)
        n_val = int(n_images * val_split)

        # Split images
        train_images = images[:n_train]
        val_images = images[n_train:n_train + n_val]
        test_images = images[n_train + n_val:]

        # Copy images to respective directories
        for split_name, split_images in [
            ('train', train_images),
            ('val', val_images),
            ('test', test_images)
        ]:
            for img_file in split_images:
                # Create unique filename with class prefix
                new_name = f"{class_name}_{img_file.name}"
                dest = output_path / 'images' / split_name / new_name
                shutil.copy2(img_file, dest)
                split_counts[split_name] += 1

    print(f"  Train: {split_counts['train']}")
    print(f"  Val: {split_counts['val']}")
    print(f"  Test: {split_counts['test']}")

    # Create dataset.yaml
    classes = list(images_by_class.keys())

    # Remove 'negative' from classes if present (it's for background augmentation)
    if 'negative' in classes:
        classes.remove('negative')
        print("\nNote: 'negative' class excluded from YOLO classes (use for augmentation)")

    dataset_config = {
        'path': str(output_path.absolute()),
        'train': 'images/train',
        'val': 'images/val',
        'test': 'images/test',
        'nc': len(classes),
        'names': classes
    }

    yaml_path = output_path / 'dataset.yaml'
    with open(yaml_path, 'w') as f:
        yaml.dump(dataset_config, f, default_flow_style=False)

    print(f"\nCreated: {yaml_path}")

    # Create README
    readme_content = f"""# FRC Team 3267 Training Dataset

## Dataset Statistics
- Total images: {total_images}
- Classes: {', '.join(classes)}
- Train: {split_counts['train']} ({train_split:.0%})
- Val: {split_counts['val']} ({val_split:.0%})
- Test: {split_counts['test']} ({test_split:.0%})

## Directory Structure
```
dataset/
├── images/
│   ├── train/    # Training images
│   ├── val/      # Validation images
│   └── test/     # Test images
├── labels/       # Labels (to be created in Roboflow)
│   ├── train/
│   ├── val/
│   └── test/
└── dataset.yaml  # YOLO8 configuration
```

## Next Steps

### Option 1: Label in Roboflow (Recommended)
1. Upload images to Roboflow
2. Label bounding boxes for each game piece
3. Export in YOLO8 format
4. Train model on Google Colab

### Option 2: Label Locally
1. Use Label Studio or similar tool
2. Create YOLO format labels (class x_center y_center width height)
3. Save labels to labels/train/, labels/val/, labels/test/
4. Train with: `yolo train data=dataset.yaml model=yolov8n.pt epochs=100`

## Classes
{chr(10).join(f"- {i}: {name}" for i, name in enumerate(classes))}

## Collection Info
Images collected from OrangePi camera in various lighting conditions.
"""

    readme_path = output_path / 'README.md'
    with open(readme_path, 'w') as f:
        f.write(readme_content)

    print(f"Created: {readme_path}")

    # Create archive for easy transfer
    print("\nCreating archive for transfer...")
    archive_name = f"{output_path.name}_{split_counts['train']}imgs"
    shutil.make_archive(archive_name, 'zip', output_path.parent, output_path.name)
    print(f"Created: {archive_name}.zip")

    print("\n" + "="*60)
    print("DATASET READY")
    print("="*60)
    print(f"Location: {output_path}")
    print(f"Archive: {archive_name}.zip")
    print("\nTransfer to your computer for labeling:")
    print(f"  scp {archive_name}.zip user@yourcomputer:~/")
    print("\nOr upload directly to Roboflow:")
    print(f"  Upload images from: {output_path}/images/")
    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(description='Prepare training dataset for YOLO8')
    parser.add_argument('--input', default='training_data',
                       help='Input directory with collected images (default: training_data)')
    parser.add_argument('--output', default='dataset',
                       help='Output directory for prepared dataset (default: dataset)')
    parser.add_argument('--train', type=float, default=0.7,
                       help='Training set ratio (default: 0.7)')
    parser.add_argument('--val', type=float, default=0.2,
                       help='Validation set ratio (default: 0.2)')
    parser.add_argument('--test', type=float, default=0.1,
                       help='Test set ratio (default: 0.1)')

    args = parser.parse_args()

    # Validate split ratios
    if args.train + args.val + args.test != 1.0:
        parser.error("Split ratios must sum to 1.0")

    prepare_dataset(
        input_dir=args.input,
        output_dir=args.output,
        train_split=args.train,
        val_split=args.val,
        test_split=args.test
    )


if __name__ == '__main__':
    main()
