import os
import re
import pyperclip
import openai

# === SETUP OPENAI CLIENT ===
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === CHARACTER LOADING ===
def load_characters():
    characters = {}
    current = None
    with open("characters.txt", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("Name:"):
                current = line.split(":", 1)[1].strip()
                characters[current] = ""
            elif current:
                characters[current] += line.strip() + " "
    return characters

# === PARSING ===
def extract_blocks(text):
    visual = re.search(r"Visual:\s*(.*)", text, re.DOTALL)
    characters = re.search(r"Characters:\s*(.*)", text)
    if not visual or not characters:
        return None, None
    visual_text = visual.group(1).strip()
    char_list = [c.strip() for c in re.split(r",|and", characters.group(1)) if c.strip()]
    return visual_text, char_list

# === PROMPT TO OPENAI ===
def build_prompt(visual, char_list, char_data):
    header = f"Visual scene description:\n{visual}\n\n"
    descs = "\n".join(f"- {name}: {char_data[name].strip()}" for name in char_list)
    instruction = (
        "\nRewrite the visual description above, replacing vague terms like 'a woman', 'a man', or 'the woman' "
        "with the full visual descriptions of the characters listed. Do not mention names or repeat 'the same woman'. "
        "Make the rewritten scene flow naturally and cinematically."
    )
    return header + "Character descriptions:\n" + descs + instruction

def rewrite_with_gpt(prompt):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant who rewrites visual scene prompts for AI image generation."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=800
    )
    return response.choices[0].message.content.strip()

# === MAIN ===
def main():
    char_data = load_characters()

    print("Paste your full prompt (include 'Visual:' and 'Characters:' lines), then Ctrl+D:")
    input_text = ""
    try:
        while True:
            input_text += input() + "\n"
    except EOFError:
        pass

    visual, char_list = extract_blocks(input_text)
    if not visual or not char_list:
        print("❌ Could not parse 'Visual:' or 'Characters:' section.")
        return

    missing = [c for c in char_list if c not in char_data]
    if missing:
        print(f"❌ Missing character(s): {', '.join(missing)}")
        return

    prompt = build_prompt(visual, char_list, char_data)
    print("\n⏳ Rewriting via OpenAI...\n")
    rewritten = rewrite_with_gpt(prompt)
    print("✅ Rewritten Visual:\n")
    print(rewritten)
    pyperclip.copy(rewritten)
    print("\n📋 Copied to clipboard.")

if __name__ == "__main__":
    main()
