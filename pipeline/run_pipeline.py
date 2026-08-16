"""
Master Pipeline Orchestrator
Executes all 7 stages of the Unilog Product Data Enrichment Pipeline sequentially.
"""
import sys
import time
from pathlib import Path

# Force UTF-8 stdout encoding for Windows compatibility
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent))

from stage1_ingest import load_and_clean
from stage2_brand_resolve import resolve_all_brands
from stage3_classify import classify_all
from stage4_attributes import extract_all_attributes
from stage5_describe import generate_descriptions
from stage6_score import score_all
from stage7_export import export_all
from config import INPUT_CSV


def run_pipeline(input_csv=None, on_stage=None):
    """
    Run all 7 pipeline stages.
    Args:
        input_csv: Path to input CSV (uses default if None)
        on_stage:  Optional callback(stage_num: int) called at each stage start
    """
    input_path = input_csv or INPUT_CSV

    def _stage(n):
        if on_stage:
            try: on_stage(n)
            except Exception: pass

    start_time = time.time()
    print("=" * 70)
    print("[UNILOG PRODUCT INTELLIGENCE ENRICHMENT PIPELINE]")
    print(f"   Input: {input_path}")
    print("=" * 70)

    _stage(1)
    print("\n-> [1/7] Ingesting & Cleaning Input Data...")
    df = load_and_clean(input_path)

    _stage(2)
    print("\n-> [2/7] Resolving Manufacturers & Brand Names...")
    df = resolve_all_brands(df)

    _stage(3)
    print("\n-> [3/7] Classifying Taxonomy (Dept > Class > Fine)...")
    df = classify_all(df)

    _stage(4)
    print("\n-> [4/7] Extracting & Normalising Product Attributes...")
    df = extract_all_attributes(df)

    _stage(5)
    print("\n-> [5/7] Generating Multi-Format Unilog Descriptions...")
    df = generate_descriptions(df)

    _stage(6)
    print("\n-> [6/7] Computing Confidence Scores & Human Review Flags...")
    df = score_all(df)

    _stage(7)
    print("\n-> [7/7] Exporting 252-Column Delivery CSV & Metrics...")
    metrics = export_all(df)

    elapsed = round(time.time() - start_time, 2)
    print("\n" + "=" * 70)
    print(f"SUCCESS: PIPELINE COMPLETE in {elapsed}s")
    print(f"   Processed: {metrics['total_processed']} rows")
    print(f"   Avg Confidence: {metrics['overall_confidence_avg']}/100")
    print(f"   Review Queue: {metrics['flagged_for_review']} rows")
    print("=" * 70)
    return df, metrics


if __name__ == "__main__":
    run_pipeline()
