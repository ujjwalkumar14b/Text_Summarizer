import os
import string
import nltk
from collections import defaultdict
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize


NLTK_DATA_DIR = os.path.join(os.getcwd(), "nltk_data")
os.makedirs(NLTK_DATA_DIR, exist_ok=True)

nltk.data.path.append(NLTK_DATA_DIR)

def ensure_nltk_data():
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt", download_dir=NLTK_DATA_DIR)

    try:
        nltk.data.find("corpora/stopwords")
    except LookupError:
        nltk.download("stopwords", download_dir=NLTK_DATA_DIR)

ensure_nltk_data()

STOP_WORDS = set(stopwords.words("english"))


try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


def summarize_text(
    text: str,
    mode: str = "basic",
    max_tokens: int = 300,
    num_sentences: int = 3,
    format_type: str = "paragraph"
) -> str:

    if not text or len(text.strip()) < 50:
        return "Error: Text is too short. Please provide more content."

    # =========================
    # LLM MODE (Optional)
    # =========================
    if mode == "llm" and Anthropic is not None:
        try:
            api_key = os.environ.get("ANTHROPIC_API_KEY")

            if api_key:
                client = Anthropic(api_key=api_key)

                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=max_tokens,
                    messages=[
                        {
                            "role": "user",
                            "content": f"Summarize clearly in {num_sentences} sentences:\n\n{text}"
                        }
                    ]
                )

                summary = response.content[0].text.strip()
                if summary:
                    return summary

        except Exception as e:
            print(f"Anthropic API Error: {e}")

    return basic_summarize(
        text=text,
        num_sentences=num_sentences,
        mode=format_type
    )


def basic_summarize(text: str, num_sentences: int = 3, mode: str = "paragraph") -> str:

    sentences = sent_tokenize(text)

    if not sentences:
        return "Error: Could not extract sentences."

    num_sentences = max(1, min(num_sentences, len(sentences)))

    words = word_tokenize(text.lower())
    freq_table = defaultdict(int)

    for word in words:
        if word not in STOP_WORDS and word not in string.punctuation:
            freq_table[word] += 1

    if not freq_table:
        return "Error: Could not analyze text content."

    sentence_scores = defaultdict(float)

    for sentence in sentences:
        word_count = 0

        for word in word_tokenize(sentence.lower()):
            if word in freq_table:
                sentence_scores[sentence] += freq_table[word]
                word_count += 1

        if word_count > 0:
            sentence_scores[sentence] /= word_count

    sorted_sentences = sorted(
        sentence_scores,
        key=sentence_scores.get,
        reverse=True
    )

    top_sentences = sorted_sentences[:num_sentences]

    if mode == "bullets":
        return "\n\n".join([f"• {s.strip()}" for s in top_sentences])

    return " ".join(top_sentences)


# Standalone test
if __name__ == "__main__":
    sample_text = """
    Claude is an advanced AI assistant developed by Anthropic.
    It leverages sophisticated language models to provide helpful,
    honest, and harmless responses across a wide range of tasks.
    The AI is designed to be versatile and capable of nuanced interactions.
    """

    print(summarize_text(sample_text))
