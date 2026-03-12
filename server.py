import os
import re
from datetime import datetime
from flask import Flask, request, render_template_string

app = Flask(__name__)

INBOX = os.path.join(os.path.dirname(__file__), "runtime_docs", "inbox")
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"}
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Kitchen Assistant Inbox</title>
  <style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto; padding: 0 16px; background: #f9f9f7; color: #222; }
    h1 { font-size: 1.4rem; margin-bottom: 24px; }
    form { background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-bottom: 24px; }
    label { display: block; font-weight: 600; margin-bottom: 6px; }
    textarea { width: 100%; height: 120px; padding: 8px; border: 1px solid #ccc; border-radius: 6px; font-size: 0.95rem; resize: vertical; }
    input[type=file] { display: block; margin-top: 4px; }
    button { margin-top: 14px; background: #2d6a4f; color: #fff; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 1rem; }
    button:hover { background: #1b4332; }
    .msg { padding: 10px 14px; border-radius: 6px; margin-bottom: 16px; }
    .success { background: #d8f3dc; border: 1px solid #74c69d; }
    .error   { background: #ffe0e0; border: 1px solid #f88; }
    .inbox { background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 16px; }
    .inbox h2 { font-size: 1rem; margin: 0 0 12px; }
    .submission { border: 1px solid #eee; border-radius: 6px; padding: 10px 12px; margin-bottom: 10px; }
    .submission .ts { font-size: 0.78rem; color: #888; margin-bottom: 4px; }
    .submission .prompt { font-size: 0.9rem; white-space: pre-wrap; margin-bottom: 4px; }
    .submission .files { font-size: 0.8rem; color: #666; }
    small { color: #888; }
  </style>
</head>
<body>
  <h1>Kitchen Assistant Inbox</h1>

  {% if message %}
    <div class="msg {{ message_class }}">{{ message }}</div>
  {% endif %}

  <form method="post" enctype="multipart/form-data">
    <label for="prompt">What do you want Claude to do?</label>
    <textarea id="prompt" name="prompt" placeholder="e.g. Add this recipe from the card in the photo. / Add these items to the grocery inventory. / Suggest a meal using what's in this fridge photo."></textarea>

    <label style="margin-top:14px;" for="files">Images (optional, select multiple)</label>
    <input type="file" id="files" name="files" accept="image/*" multiple>

    <button type="submit">Send to inbox</button>
  </form>

  <div class="inbox">
    <h2>Inbox</h2>
    {% if submissions %}
      {% for s in submissions %}
        <div class="submission">
          <div class="ts">{{ s.timestamp }}</div>
          <div class="prompt">{{ s.prompt }}</div>
          {% if s.images %}
            <div class="files">Images: {{ s.images | join(", ") }}</div>
          {% endif %}
        </div>
      {% endfor %}
    {% else %}
      <small>Empty — nothing saved yet.</small>
    {% endif %}
  </div>
</body>
</html>
"""


def timestamp():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def safe_filename(name: str) -> str:
    name = re.sub(r"[^\w\.\-]", "_", name)
    return name[:80]


def load_submissions():
    submissions = []
    for entry in sorted(os.listdir(INBOX), reverse=True):
        path = os.path.join(INBOX, entry)
        if not os.path.isdir(path):
            continue
        prompt_path = os.path.join(path, "prompt.txt")
        if not os.path.exists(prompt_path):
            continue
        with open(prompt_path, encoding="utf-8") as f:
            prompt = f.read().strip()
        images = sorted(
            fn for fn in os.listdir(path)
            if os.path.splitext(fn)[1].lower() in ALLOWED_IMAGE_EXTENSIONS
        )
        submissions.append({"timestamp": entry, "prompt": prompt, "images": images})
    return submissions


@app.route("/", methods=["GET", "POST"])
def index():
    message = None
    message_class = None

    if request.method == "POST":
        prompt = request.form.get("prompt", "").strip()
        files = request.files.getlist("files")

        if not prompt and not any(f.filename for f in files):
            message = "Nothing to save — enter a prompt or attach an image."
            message_class = "error"
        else:
            ts = timestamp()
            folder = os.path.join(INBOX, ts)
            os.makedirs(folder, exist_ok=True)

            with open(os.path.join(folder, "prompt.txt"), "w", encoding="utf-8") as f:
                f.write(prompt)

            saved_images = []
            bad_ext = []
            for file in files:
                if not file.filename:
                    continue
                ext = os.path.splitext(file.filename)[1].lower()
                if ext not in ALLOWED_IMAGE_EXTENSIONS:
                    bad_ext.append(file.filename)
                    continue
                fname = safe_filename(file.filename)
                file.save(os.path.join(folder, fname))
                saved_images.append(fname)

            if bad_ext:
                message = f"Saved, but skipped unsupported file(s): {', '.join(bad_ext)}"
                message_class = "error"
            else:
                parts = ["Saved submission"]
                if saved_images:
                    parts.append(f"with {len(saved_images)} image(s)")
                message = " ".join(parts) + f" → inbox/{ts}/"
                message_class = "success"

    submissions = load_submissions()
    return render_template_string(HTML, submissions=submissions, message=message, message_class=message_class)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8743, debug=False)
