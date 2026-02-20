import os
import csv
import random
from uuid import uuid4
from google.cloud import storage

# === Config ===
BUCKET_NAME = "my-form-uploads"
OUTPUT_DIR = "clothing_catalog"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === GCP Setup ===
client = storage.Client()

def upload_to_gcs(local_path, destination_blob):
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(destination_blob)
    blob.upload_from_filename(local_path)
    blob.make_public()
    return blob.public_url

# === Dummy image ===
dummy_path = os.path.join(OUTPUT_DIR, "dummy.png")
if not os.path.exists(dummy_path):
    with open(dummy_path, "wb") as f:
        f.write(os.urandom(1024))  # 1KB fake image

# === Sample product data ===
categories = ["T-Shirts", "Dresses", "Jeans", "Hoodies", "Shoes", "Accessories"]
colors = ["Black", "White", "Navy Blue", "Beige", "Olive", "Charcoal", "Red"]
adjectives = ["Minimalist", "Stylish", "Comfort Fit", "Slim", "Vintage", "Urban"]
materials = ["cotton", "linen", "denim", "polyester", "wool", "silk"]
sizes = ["S", "M", "L", "XL"]
genders = ["Men", "Women", "Unisex"]

# === CSV setup ===
csv_path = os.path.join(OUTPUT_DIR, "products.csv")
with open(csv_path, "w", newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=[
        "Name", "Price", "Description", "Image_URL", "Size", "Gender", "Category", "Color"
    ])
    writer.writeheader()

    for i in range(100):
        category = random.choice(categories)
        color = random.choice(colors)
        adj = random.choice(adjectives)
        material = random.choice(materials)
        size = random.choice(sizes)
        gender = random.choice(genders)
        price = round(random.uniform(10.99, 89.99), 2)

        name = f"{adj} {color} {category}"
        desc = f"A {adj.lower()} {category.lower()} made of soft {material}—designed for comfort and style."
        filename = f"{uuid4()}.png"
        local_img_path = os.path.join(OUTPUT_DIR, filename)

        os.system(f"cp {dummy_path} {local_img_path}")  # Copy dummy image
        image_url = upload_to_gcs(local_img_path, f"products/{filename}")

        writer.writerow({
            "Name": name,
            "Price": price,
            "Description": desc,
            "Image_URL": image_url,
            "Size": size,
            "Gender": gender,
            "Category": category,
            "Color": color
        })

print(f"\n✅ Done. CSV and images saved to: {OUTPUT_DIR}/")
print(f"📄 CSV file: {csv_path}")
