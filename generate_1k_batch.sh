#!/bin/bash
# Generate 1000 test documents for batch processing benchmarks
#
# Usage: ./generate_1k_batch.sh [output_dir]
#
# Creates 1000 synthetic banking documents with realistic content
# for performance testing the embedding pipeline.

set -e

OUTPUT_DIR="${1:-batch_1k}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================================================"
echo "Generating 1000 Test Documents"
echo "========================================================================"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Generate documents using Python
python3 - "$OUTPUT_DIR" << 'EOF'
import os
import sys
import json
import random
from datetime import datetime, timedelta

OUTPUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "batch_1k"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Document templates
TEMPLATES = {
    "supervisory_letter": """
SUPERVISORY LETTER

Federal Reserve Bank of {district}
Banking Supervision Department
Date: {date}

TO: Board of Directors
    {bank_name}
    {city}, {state}

SUBJECT: Findings from Recent Safety and Soundness Examination

Dear Members of the Board:

This letter presents the findings from our recent examination of {bank_name} as of {exam_date}.
The examination focused on evaluating the Bank's financial condition, management practices, and
compliance with applicable laws and regulations.

EXECUTIVE SUMMARY

The Bank operates as a {business_model} institution with total assets of ${assets}M as of the
examination date. Overall, the Bank maintains {capital_status} capital levels and demonstrates
{management_quality} management oversight of key risk areas.

EXAMINATION SCOPE

The examination team conducted a comprehensive review of the Bank's operations, including:

- Credit risk management and loan portfolio quality
- Interest rate risk and liquidity management
- Capital adequacy and earnings performance
- Management oversight and internal controls
- Compliance with consumer protection regulations

FINDINGS

{num_findings} matter(s) requiring management attention were identified during the examination:

1. Credit Risk Management: The Bank's loan review function requires enhancement to ensure
   timely identification of credit quality deterioration. Our review of {sample_size} loan
   relationships revealed {classified_count} loans totaling ${classified_amount}M that were
   inadequately risk-rated.

2. Interest Rate Risk: The Bank's asset-liability management process should be strengthened
   to better quantify and monitor exposure to changing interest rates. Modeling assumptions
   require validation and stress testing scenarios should be expanded.

3. Internal Controls: Certain operational controls require enhancement, particularly in the
   areas of wire transfer authorization and dual control procedures for vault access.

REQUIRED ACTIONS

The Board and management are expected to address these matters and provide the Reserve Bank
with written plans for corrective action within 30 days of receipt of this letter.

We appreciate the cooperation extended to our examination team. Please contact {examiner_name}
at {phone} if you have questions regarding this letter.

Sincerely,

{officer_name}
{officer_title}
Federal Reserve Bank of {district}
""",

    "camels_summary": """
CAMELS RATING SUMMARY

Institution: {bank_name}
Examination Date: {exam_date}
Composite Rating: {composite}

COMPONENT RATINGS

Capital (C): {capital}
The Bank's capital ratios {capital_assessment}. Tier 1 Leverage Ratio is {tier1_pct}% and
Total Risk-Based Capital ratio is {total_rbc_pct}%. Capital levels are {capital_adequacy}
relative to the Bank's risk profile.

Asset Quality (A): {asset_quality}
Classified assets total ${classified}M, representing {classified_pct}% of Tier 1 Capital plus
ALLL. The level of criticized assets {asset_trend} since the prior examination. Net
charge-offs were {nco_pct}% of average loans for the year.

Management (M): {management}
Management demonstrates {mgmt_capability} in operating the institution. Board oversight is
{board_oversight}. Key risk management processes are {risk_mgmt_quality}.

Earnings (E): {earnings}
Return on Assets was {roa_pct}% for the year, reflecting {earnings_quality} performance.
Net interest margin of {nim_pct}% is {margin_assessment} relative to peer institutions.

Liquidity (L): {liquidity}
Liquidity position is {liquidity_assessment}. Core deposits represent {core_deposit_pct}% of
total deposits. The Bank maintains ${fed_funds}M in available credit lines.

Sensitivity to Market Risk (S): {sensitivity}
Interest rate risk exposure is {irr_assessment}. The Bank's IRR model indicates a {irr_impact}%
decline in Economic Value of Equity given a 200 basis point parallel rate shock.

CONCLUSION

The composite {composite} rating reflects {rating_rationale}. Management is expected to address
the examination findings noted in the supervisory letter and implement appropriate corrective
measures.
""",

    "lfbo_letter": """
LESS THAN FULLY SATISFACTORY (LFS) BOARD OVERSIGHT LETTER

Federal Reserve Bank of {district}
Date: {date}

Board of Directors
{bank_name}
{city}, {state}

Dear Members of the Board:

During our recent examination of {bank_name}, we identified deficiencies in board oversight
that require your immediate attention and corrective action.

SPECIFIC DEFICIENCIES

The following weaknesses in board oversight were identified:

1. {deficiency_1}
2. {deficiency_2}
3. {deficiency_3}

REQUIRED BOARD ACTIONS

The Board must take the following corrective actions:

• Ensure all directors receive comprehensive financial and regulatory reports before each
  board meeting, allowing adequate time for review and preparation

• Establish specific board committees with clearly defined responsibilities for overseeing
  key risk areas (Audit, Loan Review, Asset/Liability Management)

• Implement a director education program addressing regulatory expectations, key risk areas,
  and fiduciary responsibilities

• Enhance board meeting documentation to demonstrate substantive discussion, inquiry, and
  decision-making regarding examination findings and management recommendations

The Reserve Bank expects to see meaningful improvement in board oversight by the next examination.
We will monitor your progress through quarterly reports and may require additional meetings with
the board if progress is unsatisfactory.

Please provide a written response within 30 days outlining specific actions the Board will take
to address these deficiencies.

Sincerely,

{officer_name}
{officer_title}
"""
}

# Random data generators
DISTRICTS = ["Boston", "New York", "Philadelphia", "Cleveland", "Richmond", "Atlanta",
             "Chicago", "St. Louis", "Minneapolis", "Kansas City", "Dallas", "San Francisco"]
STATES = ["NY", "CA", "TX", "FL", "IL", "PA", "OH", "GA", "NC", "MI"]
CITIES = ["Springfield", "Franklin", "Clinton", "Georgetown", "Madison", "Arlington",
          "Fairview", "Salem", "Riverside", "Oakland"]
BUSINESS_MODELS = ["community banking", "commercial banking", "agricultural lending focused",
                   "small business lending", "regional commercial banking"]
EXAMINER_NAMES = ["John Smith", "Sarah Johnson", "Michael Williams", "Jennifer Brown",
                  "David Jones", "Emily Davis", "Robert Miller", "Lisa Wilson"]
OFFICER_TITLES = ["Vice President, Banking Supervision", "Assistant Vice President",
                  "Supervisory Officer", "Senior Examiner"]

def random_date(start_year=2020, end_year=2024):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return (start + timedelta(days=random_days)).strftime("%B %d, %Y")

def random_phone():
    return f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}"

def generate_supervisory_letter(doc_id):
    return TEMPLATES["supervisory_letter"].format(
        district=random.choice(DISTRICTS),
        date=random_date(),
        bank_name=f"First National Bank of {random.choice(CITIES)}",
        city=random.choice(CITIES),
        state=random.choice(STATES),
        exam_date=random_date(),
        business_model=random.choice(BUSINESS_MODELS),
        assets=random.randint(100, 5000),
        capital_status=random.choice(["adequate", "strong", "well-capitalized"]),
        management_quality=random.choice(["satisfactory", "strong", "acceptable"]),
        num_findings=random.randint(2, 5),
        sample_size=random.randint(50, 200),
        classified_count=random.randint(5, 30),
        classified_amount=round(random.uniform(5, 50), 1),
        examiner_name=random.choice(EXAMINER_NAMES),
        phone=random_phone(),
        officer_name=random.choice(EXAMINER_NAMES),
        officer_title=random.choice(OFFICER_TITLES)
    )

def generate_camels_summary(doc_id):
    composite = random.choice([1, 2, 2, 2, 3, 3])  # Weighted toward 2-3
    return TEMPLATES["camels_summary"].format(
        bank_name=f"{random.choice(['First', 'Community', 'United', 'Liberty'])} Bank of {random.choice(CITIES)}",
        exam_date=random_date(),
        composite=composite,
        capital=random.choice([1, 2, 2, 3]),
        capital_assessment=random.choice(["exceed well-capitalized standards", "meet regulatory minimums", "are adequate"]),
        tier1_pct=round(random.uniform(8.0, 15.0), 1),
        total_rbc_pct=round(random.uniform(12.0, 20.0), 1),
        capital_adequacy=random.choice(["appropriate", "adequate", "strong"]),
        asset_quality=random.choice([2, 2, 3, 3, 4]),
        classified=round(random.uniform(10, 100), 1),
        classified_pct=round(random.uniform(20, 80), 1),
        asset_trend=random.choice(["increased", "decreased", "remained stable"]),
        nco_pct=round(random.uniform(0.1, 1.5), 2),
        management=random.choice([2, 2, 3, 3]),
        mgmt_capability=random.choice(["adequate capability", "satisfactory performance", "competence"]),
        board_oversight=random.choice(["adequate", "satisfactory", "appropriate"]),
        risk_mgmt_quality=random.choice(["adequate", "generally sound", "acceptable"]),
        earnings=random.choice([1, 2, 2, 3]),
        roa_pct=round(random.uniform(0.5, 1.5), 2),
        earnings_quality=random.choice(["strong", "satisfactory", "acceptable", "modest"]),
        nim_pct=round(random.uniform(3.0, 4.5), 2),
        margin_assessment=random.choice(["comparable", "favorable", "adequate"]),
        liquidity=random.choice([1, 2, 2, 3]),
        liquidity_assessment=random.choice(["strong", "adequate", "satisfactory"]),
        core_deposit_pct=round(random.uniform(70, 90), 1),
        fed_funds=round(random.uniform(50, 500), 1),
        sensitivity=random.choice([2, 2, 3, 3]),
        irr_assessment=random.choice(["moderate", "manageable", "appropriate"]),
        irr_impact=round(random.uniform(5, 25), 1),
        rating_rationale=random.choice([
            "the Bank's overall sound condition",
            "adequate performance across all areas",
            "some areas requiring management attention"
        ])
    )

def generate_lfbo_letter(doc_id):
    deficiencies = [
        "Board meeting minutes lack evidence of substantive discussion of examination findings and management's action plans",
        "Directors do not consistently receive loan review reports before board meetings",
        "The board lacks an effective committee structure for overseeing key risk areas",
        "Director attendance at board meetings has been inconsistent",
        "Board members demonstrate insufficient knowledge of the Bank's key risks and regulatory requirements",
        "Board does not adequately challenge management or provide independent oversight",
        "No formal director education program exists to ensure directors maintain necessary expertise"
    ]

    selected_deficiencies = random.sample(deficiencies, 3)

    return TEMPLATES["lfbo_letter"].format(
        district=random.choice(DISTRICTS),
        date=random_date(),
        bank_name=f"{random.choice(['First', 'Community', 'Peoples'])} Bank of {random.choice(CITIES)}",
        city=random.choice(CITIES),
        state=random.choice(STATES),
        deficiency_1=selected_deficiencies[0],
        deficiency_2=selected_deficiencies[1],
        deficiency_3=selected_deficiencies[2],
        officer_name=random.choice(EXAMINER_NAMES),
        officer_title=random.choice(OFFICER_TITLES)
    )

# Generate 1000 documents with distribution
print(f"Generating 1000 documents in {OUTPUT_DIR}/")

doc_types = ["supervisory_letter"] * 500 + ["camels_summary"] * 350 + ["lfbo_letter"] * 150
random.shuffle(doc_types)

generators = {
    "supervisory_letter": generate_supervisory_letter,
    "camels_summary": generate_camels_summary,
    "lfbo_letter": generate_lfbo_letter
}

for i, doc_type in enumerate(doc_types):
    doc_id = f"doc_{i:04d}"
    content = generators[doc_type](doc_id)

    # Create document with metadata
    doc = {
        "id": doc_id,
        "type": doc_type,
        "content": content,
        "generated_at": datetime.now().isoformat()
    }

    output_path = os.path.join(OUTPUT_DIR, f"{doc_id}.json")
    with open(output_path, 'w') as f:
        json.dump(doc, f, indent=2)

    if (i + 1) % 100 == 0:
        print(f"  Generated {i + 1}/1000 documents...")

print(f"\n✓ Successfully generated 1000 documents")
print(f"  Location: {OUTPUT_DIR}/")
print(f"  Distribution: 500 supervisory letters, 350 CAMELS summaries, 150 LFBO letters")

EOF

# Count files
DOC_COUNT=$(ls -1 "$OUTPUT_DIR" | wc -l | tr -d ' ')
echo ""
echo "========================================================================"
echo "Complete! Generated $DOC_COUNT documents in $OUTPUT_DIR/"
echo "========================================================================"
echo ""
echo "Test the pipeline with:"
echo "  ./parallel_batch.sh $OUTPUT_DIR \"YOUR_API_URL\" 10 10 \\"
echo "    --vector-field bge_m3_vector \\"
echo "    --vector-dims 1024 \\"
echo "    --chunker paragraph \\"
echo "    --chunk-size 6000 \\"
echo "    --overlap 100 \\"
echo "    --api-batch-size 16 \\"
echo "    --no-verify-ssl"
echo ""
