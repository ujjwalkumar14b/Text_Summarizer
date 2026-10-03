import os
import traceback
from flask import Flask, render_template, request, jsonify
from summarizer import summarize_text

app = Flask(__name__)
app.secret_key = os.urandom(24)
MAX_CHAR_LIMIT = 15000
MAX_FILE_SIZE = 1 * 1024 * 1024   

# ROUTES
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        input_mode = request.form.get("input_mode", "text")
        format_type = request.form.get("format_type", "paragraph")

        try:
            num_sentences = int(request.form.get("num_sentences", 3))
        except ValueError:
            num_sentences = 3

        # Clamp slider value
        num_sentences = max(2, min(num_sentences, 15))

        text = ""
        trimmed = False

        
        if input_mode == "text":
            text = request.form.get("input_text", "")
        elif input_mode == "file":

            uploaded_file = request.files.get("uploaded_file")

            if not uploaded_file or uploaded_file.filename == "":
                return jsonify({
                    "success": False,
                    "message": "Please upload a .txt file."
                }), 400

            if not uploaded_file.filename.lower().endswith(".txt"):
                return jsonify({
                    "success": False,
                    "message": "Only .txt files are supported."
                }), 400

            uploaded_file.seek(0, os.SEEK_END)
            file_size = uploaded_file.tell()
            uploaded_file.seek(0)

            if file_size > MAX_FILE_SIZE:
                return jsonify({
                    "success": False,
                    "message": "File too large. Maximum 1MB allowed."
                }), 400

            try:
                raw_bytes = uploaded_file.read()

                try:
                    text = raw_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    text = raw_bytes.decode("utf-16")

            except Exception:
                return jsonify({
                    "success": False,
                    "message": "Error reading uploaded file."
                }), 400

        else:
            return jsonify({
                "success": False,
                "message": "Invalid input mode."
            }), 400

        text = text.strip()

        if not text:
            return jsonify({
                "success": False,
                "message": "No readable text found."
            }), 400

        if len(text) < 50:
            return jsonify({
                "success": False,
                "message": "Text must contain at least 50 characters."
            }), 400

        if len(text) > MAX_CHAR_LIMIT:
            text = text[:MAX_CHAR_LIMIT]
            trimmed = True

        summary = summarize_text(
            text=text,
            num_sentences=num_sentences,
            format_type=format_type
        )

        if not summary:
            return jsonify({
                "success": False,
                "message": "Summarization failed."
            }), 500

        original_words = len(text.split())
        summary_words = len(summary.split())

        reduction = round(
            (1 - summary_words / original_words) * 100, 2
        ) if original_words > 0 else 0

        return jsonify({
            "success": True,
            "summary": summary,
            "original_words": original_words,
            "summary_words": summary_words,
            "reduction": reduction,
            "trimmed": trimmed
        })

    except Exception:
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred."
        }), 500


if __name__ == "__main__":
    app.run(debug=True)
