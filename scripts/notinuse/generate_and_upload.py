import os
import csv
import random
import base64
from uuid import uuid4
from google.cloud import storage
from dotenv import load_dotenv
import openai

script_dir = os.path.dirname(os.path.abspath(__file__))                                                                                               
env_path = os.path.join(script_dir, 'tanzimat.env')                                                                                                   
                                                                                                                                                      
load_dotenv(env_path)
# === Setup ===
bucket_name = "my-form-uploads"
output_dir = "openai_clothing_catalog"
os.makedirs(output_dir, exist_ok=True)

openai.api_key = os.getenv("OPENAI_API_KEY")
gcs_client = storage.Client()

# === Upload to GCS ===
def upload_to_gcs(local_path, dest_blob):
    bucket = gcs_client.bucket(bucket_name)
    blob = bucket.blob(dest_blob)
    blob.upload_from_filename(local_path)
    image_url = f"https://storage.googleapis.com/{bucket_name}/{dest_blob}"
    print(image_url)
    return image_url

# === Generate image with OpenAI ===
def generate_image(prompt, save_path):
    try:
        print(f"🔄 Generating image: {prompt}")
        response = openai.images.generate(
            prompt=prompt,
            n=1,
            size="512x512",
            response_format="b64_json"
        )
        img_data = response.data[0].b64_json
        with open(save_path, "wb") as f:
            f.write(base64.b64decode(img_data))
        return True
    except Exception as e:
        print(f"❌ Image generation failed: {e}")
        return False

# === Product info pools ===
categories = ["T-Shirt", "Dress", "Jeans", "Hoodie", "Sneakers", "Blouse"]
colors = ["Black", "White", "Beige", "Olive", "Navy Blue", "Charcoal"]
adjectives = ["Minimalist", "Urban", "Elegant", "Vintage", "Relaxed", "Classic"]
materials = ["cotton", "linen", "denim", "wool", "polyester"]
sizes = ["S", "M", "L", "XL"]
genders = ["Men", "Women", "Unisex"]

# === Generate 20 products ===
csv_path = os.path.join(output_dir, "products.csv")
with open(csv_path, "w", newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=[
        "Name", "Price", "Description", "Image_URL", "Size", "Gender", "Category", "Color"
    ])
    writer.writeheader()

    for i in range(50):  # Use 20 to avoid burning too many credits
        category = random.choice(categories)
        color = random.choice(colors)
        adj = random.choice(adjectives)
        material = random.choice(materials)
        size = random.choice(sizes)
        gender = random.choice(genders)
        price = round(random.uniform(15.99, 89.99), 2)

        name = f"{adj} {color} {category}"
        description = f"{adj} {category} for {gender.lower()} made of soft {material}."
        prompt = f"{adj.lower()} {color.lower()} {category.lower()} on white background, product photo, {gender.lower()} fashion"
        filename = f"{uuid4()}.png"
        local_path = os.path.join(output_dir, filename)

        if generate_image(prompt, local_path):
            image_url = upload_to_gcs(local_path, f"products/{filename}")
        else:
            image_url = ""

        writer.writerow({
            "Name": name,
            "Price": price,
            "Description": description,
            "Image_URL": image_url,
            "Size": size,
            "Gender": gender,
            "Category": category,
            "Color": color
        })

print(f"\n✅ Done. Check your folder: {output_dir}/products.csv")
