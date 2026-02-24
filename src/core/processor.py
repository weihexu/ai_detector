import nltk

nltk.download("punkt_tab", quiet=True)


def split_sentences(text: str) -> list[str]:
    return nltk.sent_tokenize(text.strip())
