import os
import re
import psycopg2
from dotenv import load_dotenv
from itemadapter import ItemAdapter
from datetime import datetime, timedelta
from transformers import AutoTokenizer, AutoModelForCausalLM, TextGenerationPipeline
import torch
from neo4j import GraphDatabase
import traceback

# Load environment variables
load_dotenv()
DB_CONNECTION_STRING = os.getenv("DB_CONNECTION_STRING")

# Safe allowed predicates map
ALLOWED_REL_TYPES = {
    "founded_by": "FOUNDED_BY",
    "acquired": "ACQUIRED",
    "has_ceo": "HAS_CEO",
    "owns_subsidiary": "OWNS_SUBSIDIARY",
    "operates_in_sector": "OPERATES_IN_SECTOR",
    "has_brand": "HAS_BRAND"
}

BLOCKED_ENTITIES = {
    "india", "usa", "united states", "bharat", "maharashtra", "karnataka",
    "tamil nadu", "kerala", "delhi", "punjab", "haryana", "uttar pradesh",
    "andhra pradesh", "gujarat", "west bengal", "rajasthan", "bihar", "assam",
    "n/a", "unknown", "unspecified","none"
}

ALLOWED_PREDICATES = {
    "founded_by",
    "acquired",
    "has_ceo",
    "owns_subsidiary",
    "operates_in_sector",
    "has_brand"
}


class NewsScraperPipeline:
    def __init__(self):
        model_name = "TheBloke/Mistral-7B-Instruct-v0.2-GPTQ"
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True
        )
        self.pipeline = TextGenerationPipeline(model=self.model, tokenizer=self.tokenizer)
        self.neo_driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASS"))
        )

    def insert_triple_into_neo4j(self, subject: str, predicate_key: str, obj: str, source: str, title: str, spider) -> None:
        pred_clean = ALLOWED_REL_TYPES.get(predicate_key.lower())
        if not pred_clean:
            spider.logger.warning(f"Skipped unsupported predicate: {predicate_key}")
            return

        with self.neo_driver.session() as session:
            session.execute_write(self._create_triple, subject, pred_clean, obj, source, title, spider)

    @staticmethod
    def _create_triple(tx, subj: str, pred: str, obj: str, source: str, title: str, spider):
        if pred == "OPERATES_IN_SECTOR":
            # Delete only if different
            tx.run("""
                MATCH (s:Entity {name: $subj})-[r:OPERATES_IN_SECTOR]->(o)
                WHERE o.name <> $obj
                DELETE r
            """, subj=subj, obj=obj)

        cypher = f"""
            MERGE (s:Entity {{name: $subj}})
            MERGE (o:Entity {{name: $obj}})
            MERGE (s)-[r:`{pred}`]->(o)
            SET r.source = $source, r.title = $title
            RETURN id(r) as rel_id
        """
        spider.logger.info(f"Attempting to insert triple: [{subj}, {pred}, {obj}]")
        result = tx.run(cypher, subj=subj, obj=obj, source=source, title=title)
        record = result.single()
        if record:
            rel_id = record["rel_id"]
            spider.logger.info(f"Inserted relationship with id: {rel_id}")
        else:
            spider.logger.warning("No relationship created")

    def open_spider(self, spider) -> None:
        self.connection = psycopg2.connect(DB_CONNECTION_STRING)
        self.cursor = self.connection.cursor()
        self.delete_old_news(spider)

    def close_spider(self, spider) -> None:
        try:
            self.cursor.close()
            self.connection.close()
            self.neo_driver.close()
        except Exception as e:
            spider.logger.error(f"Error closing resources: {e}\n{traceback.format_exc()}")

    def extract_triples(self, title: str, description: str) -> str:
        prompt = f"""
            You are a precise assistant helping build a structured knowledge graph for financial and business news.

            Your task is to extract only factual and high-value [subject, predicate, object] triples from the following news. The triples must be directly supported by the input text.

            Only include information about companies, brands, CEOs, acquisitions, subsidiaries, sectors, and founders.

            ---

            ⚠️ IMPORTANT RULES:
            - Only use these predicates:  
            * founded_by  
            * acquired  
            * has_CEO  
            * owns_subsidiary  
            * operates_in_sector  
            * has_brand

            - If **no allowed predicate** is applicable, return nothing.
            - If the news contains **places (countries, cities, states, etc.)** in the subject or object, **exclude those triples**.
            - Do **not guess or hallucinate entities** not present in the text.
            - Do not generate triples where the subject or object is 'unknown', 'unspecified', 'n/a', or any word with similar meaning.
            - Output format: One triple per line, exactly like:  
            [subject, predicate, object]
            - DO NOT output any explanations, enumerations, lists, or additional text.
            - DO NOT output placeholders or bracketed options inside the triple elements.
            - If no triples, output nothing (empty).

            ---

            Example of wrong output (do NOT do this):

            1. NSDL, operates_in_sector, [technology or financial sector]
            2. NSE, operates_in_sector, [technology or financial sector]

            Example of correct output:

            [NSDL, operates_in_sector, Technology]
            [NSE, operates_in_sector, Financial Sector]

            ---

            Now extract triples from this news:

            \"\"\"{title}. {description}\"\"\"

            Triples:
            """
        outputs = self.pipeline(prompt, max_new_tokens=256, temperature=0.2)
        return outputs[0]["generated_text"]

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        title = adapter.get('title')
        description = adapter.get('description')
        spider.logger.info(f"Processing item with title: {title}")
        data = (
            title,
            adapter.get('link'),
            adapter.get('date'),
            description,
            adapter.get('source')
        )

        MAX_WORDS = 4

        try:
            triples_response = self.extract_triples(title, description)
            spider.logger.info(f"LLM output:\n{triples_response}")

            text_output = triples_response if isinstance(triples_response, str) else triples_response.generated_text
            triples = []

            for line in text_output.strip().split("\n"):
                line = line.strip()

                # Skip numbered list lines or lines starting with digits + dot
                if re.match(r'^\d+\.', line):
                    continue

                # Must start and end with brackets
                if not (line.startswith("[") and line.endswith("]")):
                    continue

                parts = [p.strip().strip('"').strip("'") for p in line.strip("[]").split(",")]
                if len(parts) != 3:
                    continue

                subj, pred, obj = parts

                # Skip if placeholders like [...] inside subject or object
                if "[" in subj or "]" in subj or "[" in obj or "]" in obj:
                    continue

                # Skip if subject or object too long (>4 words)
                if len(subj.split()) > MAX_WORDS or len(obj.split()) > MAX_WORDS:
                    continue

                subj_lower, pred_lower, obj_lower = subj.lower(), pred.lower(), obj.lower()

                # Filter out invalid triples
                if (
                    pred_lower not in ALLOWED_PREDICATES or
                    subj_lower in BLOCKED_ENTITIES or
                    obj_lower in BLOCKED_ENTITIES or
                    subj_lower == "unspecified" or
                    obj_lower == "unspecified"
                ):
                    continue

                triples.append({
                    "subject": subj,
                    "predicate": pred_lower,
                    "object": obj,
                    "source": adapter.get("link"),
                    "title": title
                })

            # Insert into Neo4j
            for triple in triples:
                try:
                    self.insert_triple_into_neo4j(
                        triple["subject"],
                        triple["predicate"],
                        triple["object"],
                        triple["source"],
                        triple["title"],
                        spider
                    )
                except Exception as e:
                    spider.logger.error(f"Failed to insert triple {triple}: {e}\n{traceback.format_exc()}")

        except Exception as e:
            spider.logger.error(f"Error extracting triples: {e}\n{traceback.format_exc()}")

        # Insert original news into DB
        try:
            self.cursor.execute("""
                INSERT INTO news (title, link, date, description, source)
                VALUES (%s, %s, %s, %s, %s)
            """, data)
            self.connection.commit()
        except Exception as e:
            spider.logger.error(f"Error inserting news into DB: {e}\n{traceback.format_exc()}")

        return item

    def delete_old_news(self, spider) -> None:
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        try:
            self.cursor.execute("""
                DELETE FROM news
                WHERE date < %s OR created_at < %s
            """, (one_day_ago, one_day_ago))
            self.connection.commit()
            spider.logger.info("Old news deleted successfully.")
        except Exception as e:
            spider.logger.error(f"Error deleting old news: {e}\n{traceback.format_exc()}")
