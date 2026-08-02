import os
import re
import json
import pathlib
import torch
import spacy
import pypdf
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from typing import List, Dict, Any
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sentence_transformers import SentenceTransformer, util

# Sets up a directory for output files by stage
def setup_directories(base_dir: str = "GRC_Alternative_Hallucination_Results") -> Dict[str, pathlib.Path]:
    root = pathlib.Path(base_dir)
    dirs = {
        "root": root,
        "stage_1": root / "stage_1_audits",
        "stage_2": root / "stage_2_consolidated",
        "stage_3": root / "stage_3_visualizations"
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


# Stage 1 report analysis - individual framework reports
class Stage1Analysis:
    def __init__(
        self,
        nli_model_name: str = "cross-encoder/nli-deberta-v3-base",
        embed_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        spacy_model: str = "en_core_web_sm"
    ):
        print("\n[+] Stage 1: Initializing Deterministic Audit Engines")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # NLI Cross-Encoder - sentence exact word comparison (source text vs. LLM Output)
        print(f"Loading NLI Model ({nli_model_name})")
        self.nli_tokenizer = AutoTokenizer.from_pretrained(nli_model_name)
        self.nli_model = AutoModelForSequenceClassification.from_pretrained(nli_model_name).to(self.device)
        self.nli_model.eval()
        
        # Vector Embedder - covert unstructured text into vectors
        print(f"Loading Sentence Transformer ({embed_model_name})")
        self.embedder = SentenceTransformer(embed_model_name, device=self.device)

        # spaCy NER Engine - clusters similar language into distinct groups
        print(f"Loading spaCy Model ({spacy_model})")
        self.nlp = spacy.load(spacy_model)

    # Calculates exact NLI probabilities using DeBERTa Cross-Encoder
    def compute_nli_scores(self, premise: str, hypothesis: str) -> Dict[str, float]:
       
        if not premise.strip() or not hypothesis.strip():
            return {"unfaithfulness_risk": 1.0, "contradiction_prob": 0.0, "entailment_prob": 0.0}

        features = self.nli_tokenizer(
            premise, hypothesis, padding=True, truncation=True, max_length=512, return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            logits = self.nli_model(**features).logits
            probs = torch.softmax(logits, dim=-1).squeeze().cpu().numpy()

        contradiction_prob = float(probs[0])
        entailment_prob = float(probs[2])

        return {
            "unfaithfulness_risk": float(1.0 - entailment_prob),
            "contradiction_prob": contradiction_prob,
            "entailment_prob": entailment_prob
        }

    # Calculates cosine distance (1 - cosine similarity) between text embeddings
    def compute_semantic_drift(self, source_text: str, generated_text: str) -> float:
        if not source_text.strip() or not generated_text.strip():
            return 1.0

        embeddings = self.embedder.encode([source_text, generated_text], convert_to_tensor=True)
        cosine_sim = float(util.cos_sim(embeddings[0], embeddings[1])[0][0].cpu())
        return max(0.0, float(1.0 - cosine_sim))

    # Extracts named entities & control IDs to find exact string match omissions
    def audit_fabricated_entities(self, source_text: str, generated_text: str) -> Dict[str, Any]:
        doc_gen = self.nlp(generated_text)
        doc_src = self.nlp(source_text)

        source_entities = {ent.text.strip().lower() for ent in doc_src.ents}
        source_raw_text = source_text.lower()

        gen_entities = [ent.text.strip() for ent in doc_gen.ents if len(ent.text.strip()) > 1]
        
        # Regex for GRC Control ID formats (e.g., ID.AM-1)
        control_id_pattern = re.compile(r'\b[A-Z]{2}\.[A-Z]{2}-\d+\b')
        regex_gen_entities = control_id_pattern.findall(generated_text)
        all_gen_entities = list(set(gen_entities + regex_gen_entities))

        fabricated_entities = []
        for ent in all_gen_entities:
            ent_clean = ent.lower()
            if ent_clean not in source_entities and ent_clean not in source_raw_text:
                fabricated_entities.append(ent)

        return {
            "fabricated_count": len(fabricated_entities),
            "fabricated_list": fabricated_entities
        }

    # Processes a single run document and flattens outputs with deterministic audit scores
    def process_run(self, raw_json_data: Dict[str, Any], raw_source_pdf_text: str) -> List[Dict[str, Any]]:
        assessment_id = raw_json_data.get("assessment_id", "unknown_id")
        doc_name = raw_json_data.get("document_name", "unknown_document.pdf")
        folder_name = raw_json_data.get("folder_name", doc_name)

        flattened_audits = []

        for framework in raw_json_data.get("framework_results", []):
            fw_id = framework.get("framework_id", "unknown_fw")
            for control in framework.get("control_results", []):
                control_id = control.get("control_id")
                rationale = control.get("score_rationale", "")
                evidence_list = control.get("evidence", [])
                
                combined_evidence = " ".join(evidence_list) if evidence_list else raw_source_pdf_text[:1500]

                # Gather Stage 1 evidence
                nli_metrics = self.compute_nli_scores(premise=combined_evidence, hypothesis=rationale)
                drift_score = self.compute_semantic_drift(source_text=combined_evidence, generated_text=rationale)
                entity_metrics = self.audit_fabricated_entities(source_text=raw_source_pdf_text, generated_text=rationale)

                record = {
                    "assessment_id": assessment_id,
                    "document_name": doc_name,
                    "folder_name": folder_name,
                    "framework_id": fw_id,
                    "control_id": control_id,
                    "family": control.get("family"),
                    "maturity_score": control.get("maturity_score"),
                    "score_rationale": rationale,
                    "unfaithfulness_risk": nli_metrics["unfaithfulness_risk"],
                    "contradiction_prob": nli_metrics["contradiction_prob"],
                    "semantic_drift_risk": drift_score,
                    "fabricated_entities_count": entity_metrics["fabricated_count"],
                    "fabricated_entities": entity_metrics["fabricated_list"]
                }
                flattened_audits.append(record)

        return flattened_audits


# Stage 2 Analysis - Cosolidating individual framework report metric values by LLM and paper
def run_stage2_consolidation(audited_records: List[Dict[str, Any]], output_dir: pathlib.Path) -> Dict[str, Any]:
    print("\n[+] Stage 2: Consolidating Population Metrics")
    df = pd.DataFrame(audited_records)

    # Create columns for Seaborn analysis
    df["paper"] = df["folder_name"].apply(
        lambda x: "DeptEduc" if "DeptEduc" in str(x) else "Scott&Scott"
    )
    df["model"] = df["folder_name"].apply(
        lambda x: "Anthrop" if "Anthrop" in str(x) else ("GPT_4.1" if "GPT_4.1" in str(x) else "Llama_4_Mav")
    )
    df["run_id"] = df["paper"] + "_" + df["model"]

    # Calculate aggregations from framework report metrics for final table 
    matrix = df.groupby("run_id").agg(
        overall_hallucination_pct=("unfaithfulness_risk", lambda x: float((x > 0.5).mean())),
        unfaithfulness_risk=("unfaithfulness_risk", "mean"),
        direct_contradiction_prob=("contradiction_prob", "mean"),
        semantic_drift_risk=("semantic_drift_risk", "mean"),
        fabricated_entities_count=("fabricated_entities_count", "sum")
    ).reset_index()

    summary_payload = {
        "master_matrix": matrix.to_dict(orient="records"),
        "total_controls_audited": len(df)
    }

    # final hallicination metrics matrix
    summary_path = output_dir / "consolidated_hallucination_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)

    print(f"Consolidation saved to '{summary_path}'.")
    return summary_payload, df


# Stage 3 - Outputs the Master Hallucination Matrix and generates Seaborn plots to showcase key metrics
class Stage3HallucinationPresenter:
    def __init__(self, summary: Dict[str, Any], df: pd.DataFrame, output_dir: pathlib.Path):
        self.summary = summary
        self.df = df
        self.output_dir = output_dir

    # Prints Master Matrix in specific format and saves to file
    def print_master_matrix(self):
        matrix_df = pd.DataFrame(self.summary["master_matrix"])
        
        # Rename columns to match formal publication naming
        matrix_df.columns = [
            "Run Identifier", "Overall Hallucination %", "Unfaithfulness Risk",
            "Direct Contradiction Prob", "Semantic Drift Risk", "Fabricated Entities Count"
        ]

        print("Hallucination Analysis Matrix")
        print(matrix_df.to_csv(index=False))

        # Save CSV and Markdown
        matrix_df.to_csv(self.output_dir / "master_hallucination_matrix.csv", index=False)
        matrix_df.to_markdown(self.output_dir / "master_hallucination_matrix.md", index=False)
        print("Matrix saved to file")

    # Generate maturity score histogram and density plots by run_id
    def plot_distributions(self):
        # Maturity distribution 
        plt.figure(figsize=(10, 6))
        sns.histplot(
            data=self.df,
            x="maturity_score",
            hue="run_id",
            discrete=True,
            multiple="dodge",
            shrink=0.8
        )
        plt.title("Control Maturity Score Distribution by Run")
        plt.xlabel("Maturity Score")
        plt.ylabel("Control Count")
        plt.tight_layout()
        
        save_path = self.output_dir / "maturity_distribution.png"
        plt.savefig(save_path, dpi=300)
        plt.close()

        # Hallucination density histograms
        plt.figure(figsize=(10, 6))
        sns.histplot(
            data=self.df,
            x="unfaithfulness_risk",
            hue="run_id",
            kde=True,
            element="step"
        )
        plt.title("Unfaithfulness Risk Density by Run")
        plt.xlabel("Unfaithfulness Risk Score")
        plt.ylabel("Density")
        plt.tight_layout()

        density_path = self.output_dir / "hallucination_density_histograms.png"
        plt.savefig(density_path, dpi=300)
        plt.close()
        print(f" -> Generated visualizations: '{save_path.name}', '{density_path.name}'")

    # Radar profiles of the metrics balance by LLM for comparison
    def plot_radar_profiles(self):
        matrix_df = pd.DataFrame(self.summary["master_matrix"])
        if matrix_df.empty:
            return

        # Rename columns to match the publication names used in print_master_matrix
        matrix_df.columns = [
            "Run Identifier", "Overall Hallucination %", "Unfaithfulness Risk",
            "Direct Contradiction Prob", "Semantic Drift Risk", "Fabricated Entities Count"
        ]

        plt.figure(figsize=(12, 6))
        melted = pd.melt(
            matrix_df, 
            id_vars=["Run Identifier"], 
            value_vars=["Unfaithfulness Risk", "Direct Contradiction Prob", "Semantic Drift Risk"]
        )
        sns.barplot(data=melted, x="variable", y="value", hue="Run Identifier")
        plt.title("Comparative Risk Profiles Across Model Runs")
        plt.xlabel("Metric Type")
        plt.ylabel("Score")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()

        radar_path = self.output_dir / "hallucination_radar_profiles.png"
        plt.savefig(radar_path, dpi=300)
        plt.close()
        print(f" -> Generated visualization: '{radar_path.name}'")

    # Call to generate visuals
    def render_all(self):
        print("\n[+] Stage 3: Rendering Visualizations and Master Matrix...")
        self.print_master_matrix()
        self.plot_distributions()
        self.plot_radar_profiles()

# Main activation of each stage of analysis pipeline
if __name__ == "__main__":
    dirs = setup_directories()

    # Load source text pdfs
    source_texts_dir = pathlib.Path("Datasets/Policies_Templates")
    
    scott_path = source_texts_dir / "Scott & Scott Written-Information-Security-Policy.pdf"
    dept_path = source_texts_dir / "2023-cybersecurity-policy.pdf"

    # Extract doc content in usable foramt
    def extract_pdf_text(path: pathlib.Path) -> str:
        reader = pypdf.PdfReader(path)
        return " ".join([page.extract_text() for page in reader.pages])

    loaded_source_texts = {
        "Scott&Scott": extract_pdf_text(scott_path),
        "DeptEduc": extract_pdf_text(dept_path)
    }
    print(f"Loaded source policy: {scott_path.name}")
    print(f"Loaded source policy: {dept_path.name}")

    # Define the root directory containing model framework report folders, excluding GPT_5.1
    experiments_root = pathlib.Path(".")
    
    # Conduct Stage 1 Analysis
    stage1_auditor = Stage1Analysis()
    all_stage1_audits = []

    # Collect Key JSON framework GRC report files 
    model_folders = [
        f for f in experiments_root.glob("*_framework_reports") 
        if f.is_dir() and "GPT_5.1" not in f.name
    ]
    print(f"\n[+] Discovered {len(model_folders)} model report directories to analyze (GPT_5.1 excluded).")

    # Process each folder for JSON files and apply Stage 1 anlysis to each
    for folder in model_folders:
        print(f"Processing Folder: {folder.name}")
        
        active_source_text = loaded_source_texts["Scott&Scott"] if "Scott&Scott" in folder.name else loaded_source_texts["DeptEduc"]

        json_files = list(folder.glob("*.json"))
        print(f"Found {len(json_files)} JSON reports in {folder.name}.")

        for json_file in json_files:
            with open(json_file, "r", encoding="utf-8") as f:
                raw_grc_input = json.load(f)

            raw_grc_input["folder_name"] = folder.name

            run_audits = stage1_auditor.process_run(raw_grc_input, active_source_text)
            all_stage1_audits.extend(run_audits)

    # Save stage 1 output to file
    stage1_file = dirs["stage_1"] / "item_level_hallucination_audits.json"
    with open(stage1_file, "w", encoding="utf-8") as f:
        json.dump(all_stage1_audits, f, indent=2)

    # Apply Stage 2 Analysis and safe to file
    summary_payload, stage2_df = run_stage2_consolidation(all_stage1_audits, dirs["stage_2"])

    # Apply Stage 3 visual generation and save file
    presenter = Stage3HallucinationPresenter(summary_payload, stage2_df, dirs["stage_3"])
    presenter.render_all()

    print(f"\nFull Corpus Pipeline Execution Complete! All artifacts written to '{dirs['root']}'")