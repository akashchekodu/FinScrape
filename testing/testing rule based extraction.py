from allennlp.predictors.predictor import Predictor
import allennlp_models.structured_prediction
import spacy

# Load models
predictor = Predictor.from_path(
    "https://storage.googleapis.com/allennlp-public-models/openie-model.2020.03.26.tar.gz"
)
nlp = spacy.load("en_core_web_md")  # Full pipeline with NER for filtering
nlp_no_ner = spacy.load("en_core_web_md", disable=["parser", "ner"])  # Faster preprocessing

def preprocess_text(text):
    doc = nlp_no_ner(text.lower())
    tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
    return " ".join(tokens)

def rewrite_sentence(text):
    doc = nlp_no_ner(text)
    rewritten = []
    used = set()
    for i, token in enumerate(doc):
        # Add phrase like "Jio, which is owned by Reliance"
        if token.dep_ in {"amod", "compound"} and token.head.pos_ == "PROPN":
            owner = token.text
            entity = token.head.text
            clause = f"{entity}, which is owned by {owner}"
            used.update({token.i, token.head.i})
            rewritten.append(clause)
        elif i not in used:
            rewritten.append(token.text)
    return " ".join(rewritten)

def extract_named_entities(text, arg_text):
    """
    Given the original sentence text and an argument text (e.g. ARG0),
    return a string with only the named entities (NERs) present in arg_text.
    If none found, fallback to original arg_text.
    """
    doc = nlp(text)
    ents = set(ent.text.lower() for ent in doc.ents)
    arg_tokens = arg_text.lower().split()
    filtered_tokens = [token for token in arg_tokens if token in ents]
    return " ".join(filtered_tokens) if filtered_tokens else arg_text

def main():
    test_sentences = [
        "Reliance owned Jio increases prices",
        "Apple acquired Beats Electronics in 2014",
        "Tesla was founded by Elon Musk",
        "Microsoft announced a new Surface product",
        "Google operates in the cloud computing sector",
        "Amazon owns Whole Foods Market",
        "Facebook's CEO Mark Zuckerberg spoke at the event",
        "Samsung has a new CEO appointed this year",
        "IBM acquired Red Hat for $34 billion",
        "Netflix launched its original series last month",
        "Intel operates in the semiconductor industry",
        "Uber owns several autonomous vehicle startups",
        "Google's parent company Alphabet was founded in 2015",
        "Spotify announced a partnership with Hulu",
        "Sony released the latest PlayStation console",
        "Ford acquired electric vehicle startup Rivian",
        "Facebook announced new features in its social media platform",
        "Tesla's CEO Elon Musk confirmed new battery technology",
        "Airbnb operates in the hospitality sector",
        "Apple's acquisition of Shazam improved its music capabilities",
    ]

    for raw_text in test_sentences:
        print(f"Original sentence: {raw_text}")

        rewritten = rewrite_sentence(raw_text)
        print("Rewritten sentence:", rewritten)

        clean_text = preprocess_text(rewritten)
        print("Preprocessed text:", clean_text)

        result = predictor.predict(sentence=clean_text)

        print("\nExtracted triples:")
        found_any = False
        for triple in result["verbs"]:
            description = triple["description"]
            print("Raw triple:", description)

            # Filter ARG0, ARG1, ARG2 to keep only named entities from original raw text
            for arg in ["ARG0", "ARG1", "ARG2"]:
                tag = f"[{arg}:"
                if tag in description:
                    start = description.find(tag) + len(tag)
                    end = description.find("]", start)
                    arg_text = description[start:end].strip()
                    filtered_arg = extract_named_entities(raw_text, arg_text)
                    description = description.replace(arg_text, filtered_arg)

            print("Filtered triple:", description)
            found_any = True
            print()

        if not found_any:
            print("No triples extracted.")

        print("-" * 60)

if __name__ == "__main__":
    main()
