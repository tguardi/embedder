#!/usr/bin/env python3
"""
Generate a batch of banking examination documents for load testing.

Usage:
    python generate_batch.py --count 10000 --output batch_documents/
"""

import argparse
import random
from pathlib import Path
from datetime import datetime, timedelta
from standalone_text_generator import (
    BankProfile, BusinessModel, CAMELSExamination,
    ExaminationFinding, RiskArea, FindingType, Severity,
    generate_supervisory_letter, generate_camels_summary,
    generate_lfbo_rating_letter, ExamHistorySnapshot
)


# Bank name templates for variety
BANK_NAMES = [
    "First National Bank",
    "Community Trust Bank",
    "State Bank",
    "Federal Savings Bank",
    "Regional Commerce Bank",
    "Metropolitan Bank",
    "Peoples Bank",
    "Heritage Bank",
    "Valley National Bank",
    "Coastal Bank",
    "Mountain Bank",
    "Riverside Bank",
    "Summit Bank",
    "Gateway Bank",
    "Crossroads Bank",
]

CITIES = [
    ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"),
    ("Houston", "TX"), ("Phoenix", "AZ"), ("Philadelphia", "PA"),
    ("San Antonio", "TX"), ("San Diego", "CA"), ("Dallas", "TX"),
    ("San Jose", "CA"), ("Austin", "TX"), ("Jacksonville", "FL"),
    ("San Francisco", "CA"), ("Columbus", "OH"), ("Charlotte", "NC"),
    ("Seattle", "WA"), ("Denver", "CO"), ("Boston", "MA"),
    ("Portland", "OR"), ("Nashville", "TN"),
]


def generate_random_bank(bank_id: int) -> BankProfile:
    """Generate a random bank profile."""
    name_base = random.choice(BANK_NAMES)
    city, state = random.choice(CITIES)
    name = f"{name_base} of {city}"

    # Random RSSD (7 digits)
    rssd = f"{random.randint(1000000, 9999999)}"

    # Random asset size (100M to 50B)
    total_assets = random.choice([
        random.uniform(100, 500),      # Small banks
        random.uniform(500, 2000),     # Medium banks
        random.uniform(2000, 10000),   # Large banks
        random.uniform(10000, 50000),  # Very large banks
    ])

    # Random charter date
    charter_year = random.randint(1950, 2010)
    charter_date = datetime(charter_year, random.randint(1, 12), random.randint(1, 28))

    # Random ratings (weighted toward 2s and 3s)
    rating_choices = [1, 2, 2, 2, 3, 3, 3, 4, 5]

    return BankProfile(
        name=name,
        rssd=rssd,
        total_assets=total_assets,
        location=(city, state),
        charter_date=charter_date,
        business_model=random.choice(list(BusinessModel)),
        composite_rating=random.choice(rating_choices),
        capital_rating=random.choice(rating_choices),
        asset_quality_rating=random.choice(rating_choices),
        management_rating=random.choice(rating_choices),
        earnings_rating=random.choice(rating_choices),
        liquidity_rating=random.choice(rating_choices),
        sensitivity_rating=random.choice(rating_choices),
    )


def generate_random_findings(count: int = None) -> list:
    """Generate random examination findings."""
    if count is None:
        count = random.randint(1, 5)

    findings = []
    risk_areas = random.sample(list(RiskArea), min(count, len(list(RiskArea))))

    for risk_area in risk_areas:
        # Higher probability of MRA vs MRIA
        finding_type = random.choices(
            [FindingType.MRA, FindingType.MRIA],
            weights=[0.8, 0.2]
        )[0]

        severity = random.choice(list(Severity))

        findings.append(ExaminationFinding(
            risk_area=risk_area,
            finding_type=finding_type,
            severity=severity,
        ))

    return findings


def generate_random_examination(bank: BankProfile) -> CAMELSExamination:
    """Generate a random examination."""
    # Add prior examination history
    if random.random() > 0.3:  # 70% chance of having prior exam
        prior_year = random.randint(2020, 2023)
        bank.prior_examinations.append(
            ExamHistorySnapshot(
                exam_date=datetime(prior_year, random.randint(1, 12), random.randint(1, 28)),
                composite_rating=random.choice([1, 2, 2, 3, 3, 4]),
                component_ratings={
                    'capital': random.choice([1, 2, 2, 3]),
                    'liquidity': random.choice([1, 2, 2, 3]),
                    'management': random.choice([1, 2, 2, 3]),
                },
                tier1_leverage=round(random.uniform(7.0, 12.0), 2),
                total_rbc=round(random.uniform(10.0, 18.0), 2),
                npa_ratio=round(random.uniform(0.5, 3.0), 2),
                roa=round(random.uniform(0.5, 1.5), 2),
                loan_to_deposit=round(random.uniform(70, 95), 2),
            )
        )

    exam_end = datetime.now()
    exam_start = exam_end - timedelta(days=45)  # 45 days ago
    report_date = exam_end + timedelta(days=30)  # 30 days from now

    findings = generate_random_findings()

    return CAMELSExamination(
        bank=bank,
        exam_start_date=exam_start,
        exam_end_date=exam_end,
        report_date=report_date,
        examination_type=random.choice([
            "Full-Scope Safety and Soundness",
            "Targeted Examination",
            "Continuous Monitoring",
        ]),
        findings=findings,
        loan_sample_pct=round(random.uniform(15, 50), 1),
    )


def generate_batch(output_dir: Path, count: int, doc_type: str = "all"):
    """Generate a batch of documents."""
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating {count} documents in {output_dir}/")
    print(f"Document type: {doc_type}")
    print("")

    for i in range(count):
        # Generate random bank and examination
        bank = generate_random_bank(i)
        examination = generate_random_examination(bank)

        # Determine which document type(s) to generate
        if doc_type == "all":
            doc_types = random.choice([
                ["supervisory"],
                ["camels"],
                ["lfbo"],
                ["supervisory", "camels"],
                ["supervisory", "lfbo"],
                ["supervisory", "camels", "lfbo"],
            ])
        else:
            doc_types = [doc_type]

        # Generate selected document types
        for dtype in doc_types:
            if dtype == "supervisory":
                content = generate_supervisory_letter(examination, examination.findings)
                filename = output_dir / f"doc{i:06d}_supervisory_{bank.rssd}.txt"
            elif dtype == "camels":
                content = generate_camels_summary(examination)
                filename = output_dir / f"doc{i:06d}_camels_{bank.rssd}.txt"
            elif dtype == "lfbo":
                content = generate_lfbo_rating_letter(examination)
                filename = output_dir / f"doc{i:06d}_lfbo_{bank.rssd}.txt"

            with open(filename, 'w') as f:
                f.write(content)

        # Progress indicator
        if (i + 1) % 100 == 0:
            print(f"  Generated {i + 1}/{count} documents...")

    print(f"\n✓ Generated {count} documents in {output_dir}/")

    # Show statistics
    files = list(output_dir.glob("*.txt"))
    total_size = sum(f.stat().st_size for f in files)
    avg_size = total_size / len(files) if files else 0

    print(f"\nStatistics:")
    print(f"  Total files: {len(files)}")
    print(f"  Total size: {total_size / 1024 / 1024:.1f} MB")
    print(f"  Average file size: {avg_size / 1024:.1f} KB")


def main():
    parser = argparse.ArgumentParser(description="Generate batch banking documents")
    parser.add_argument("--count", type=int, default=100, help="Number of documents to generate")
    parser.add_argument("--output", default="batch_documents", help="Output directory")
    parser.add_argument("--type", choices=["all", "supervisory", "camels", "lfbo"],
                       default="all", help="Document type to generate")
    args = parser.parse_args()

    output_dir = Path(args.output)

    print("=" * 70)
    print("BATCH DOCUMENT GENERATOR")
    print("=" * 70)
    print("")

    generate_batch(output_dir, args.count, args.type)

    print("")
    print("You can now process these documents with:")
    print(f"  python batch_embedder.py {args.output}/ --api-url YOUR_URL")


if __name__ == "__main__":
    main()
