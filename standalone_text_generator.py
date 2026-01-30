"""
Standalone Text File Generator - Portable Banking Examination Document Generator

This module can be copied to any Python project with zero external dependencies.
Generates realistic supervisory letters, CAMELS summaries, and LFBO rating letters.

Usage:
    from standalone_text_generator import generate_example_documents

    # Generate all three document types
    supervisory_letter, camels_summary, lfbo_letter = generate_example_documents()

    # Save to files
    with open("supervisory_letter.txt", "w") as f:
        f.write(supervisory_letter)

Requirements: Python 3.7+
No external dependencies required!
"""

import random
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum


# ============================================================================
# CONSTANTS
# ============================================================================

CITATIONS_BY_RISK = {
    "Liquidity Risk Management": "SR 10-6 (Liquidity Risk Management); 12 CFR 252 Subpart F",
    "Credit Risk Management": "SR 07-1 (Interagency Guidance on Concentrations in CRE); 12 CFR 365",
    "Interest Rate Risk": "SR 12-7 (Stress Testing); 12 CFR 324 Appendix D",
    "Operational Risk": "SR 15-9 (Cybersecurity Assessment); FFIEC IT Handbook",
    "Information Security": "SR 11-9 (Information Security), FFIEC CAT",
    "BSA/AML Compliance": "BSA (31 CFR Chapter X); FFIEC BSA/AML Manual",
    "Compliance Risk": "Consumer compliance regulations as applicable (Reg Z/CC/E)",
    "Vendor Management": "SR 13-19 / CA 13-21 (Third-Party Risk Management)",
    "Capital Planning": "SR 15-18 / SR 15-19 (Capital Planning and Stress Testing)"
}

RATING_DESCRIPTIONS = {
    1: "Strongly Meets Expectations",
    2: "Broadly Meets Expectations",
    3: "Conditionally Meets Expectations",
    4: "Deficient-1",
    5: "Deficient-2"
}


# ============================================================================
# ENUMS
# ============================================================================

class RiskArea(Enum):
    CREDIT_RISK = "Credit Risk Management"
    INTEREST_RATE_RISK = "Interest Rate Risk"
    LIQUIDITY_RISK = "Liquidity Risk Management"
    OPERATIONAL_RISK = "Operational Risk"
    COMPLIANCE_RISK = "Compliance Risk"
    STRATEGIC_RISK = "Strategic Risk"
    REPUTATION_RISK = "Reputation Risk"
    BSA_AML = "BSA/AML Compliance"
    IT_SECURITY = "Information Security"
    VENDOR_MANAGEMENT = "Third-Party Risk Management"
    CAPITAL_PLANNING = "Capital Planning"
    ASSET_QUALITY = "Asset Quality"
    CONCENTRATION_RISK = "Concentration Risk"
    GOVERNANCE = "Corporate Governance"
    INTERNAL_AUDIT = "Internal Audit Function"


class FindingType(Enum):
    MRA = "Matter Requiring Attention"
    MRIA = "Matter Requiring Immediate Attention"


class Severity(Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    CRITICAL = "Critical"


class BusinessModel(Enum):
    COMMERCIAL = "Commercial Banking"
    COMMUNITY = "Community Banking"
    AGRICULTURAL = "Agricultural Banking"
    REAL_ESTATE = "Real Estate Focused"
    WEALTH_MANAGEMENT = "Wealth Management"
    SPECIALTY = "Specialty Finance"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ExamHistorySnapshot:
    """Historical snapshot of a prior examination"""
    exam_date: datetime
    composite_rating: int
    component_ratings: Dict[str, int]
    tier1_leverage: float
    total_rbc: float
    npa_ratio: float
    roa: float
    loan_to_deposit: float


@dataclass
class BankProfile:
    """Represents a synthetic bank with realistic characteristics"""
    name: str
    rssd: str
    total_assets: float  # in millions
    location: Tuple[str, str]  # (city, state)
    charter_date: datetime
    business_model: BusinessModel

    # Financial metrics
    tier1_leverage: float = 0.0
    total_rbc: float = 0.0
    npa_ratio: float = 0.0
    roa: float = 0.0
    roe: float = 0.0
    nim: float = 0.0
    efficiency_ratio: float = 0.0
    loan_to_deposit: float = 0.0

    # Ratings
    composite_rating: int = 2
    capital_rating: int = 1
    asset_quality_rating: int = 2
    management_rating: int = 2
    earnings_rating: int = 2
    liquidity_rating: int = 2
    sensitivity_rating: int = 2
    prior_examinations: List[ExamHistorySnapshot] = field(default_factory=list)

    def __post_init__(self):
        """Generate realistic financial metrics based on asset size and ratings"""
        if self.tier1_leverage == 0.0:
            self.tier1_leverage = self._generate_capital_ratio()
        if self.total_rbc == 0.0:
            self.total_rbc = round(self.tier1_leverage * random.uniform(1.3, 1.8), 2)
        if self.npa_ratio == 0.0:
            self.npa_ratio = self._generate_npa_ratio()
        if self.roa == 0.0:
            self.roa = self._generate_roa()
        if self.roe == 0.0:
            self.roe = round(self.roa * random.uniform(8, 12), 2)
        if self.nim == 0.0:
            self.nim = round(random.uniform(2.5, 4.5), 2)
        if self.efficiency_ratio == 0.0:
            self.efficiency_ratio = round(random.uniform(50, 75), 2)
        if self.loan_to_deposit == 0.0:
            self.loan_to_deposit = round(random.uniform(70, 95), 2)

    def _generate_capital_ratio(self) -> float:
        """Generate realistic capital ratios based on size and rating"""
        base = 8.0
        rating_adjustment = (3 - self.capital_rating) * 1.5
        size_adjustment = 2.0 if self.total_assets > 10000 else 0.0
        return round(base + rating_adjustment + size_adjustment + random.uniform(-1, 1), 2)

    def _generate_npa_ratio(self) -> float:
        """Generate NPA ratio based on asset quality rating"""
        base_npa = {1: 0.3, 2: 0.8, 3: 2.0, 4: 4.5, 5: 8.0}
        return round(base_npa[self.asset_quality_rating] * random.uniform(0.7, 1.3), 2)

    def _generate_roa(self) -> float:
        """Generate ROA based on earnings rating"""
        base_roa = {1: 1.4, 2: 1.1, 3: 0.7, 4: 0.3, 5: -0.5}
        return round(base_roa[self.earnings_rating] * random.uniform(0.8, 1.2), 2)


@dataclass
class ExaminationFinding:
    """Represents a supervisory finding"""
    risk_area: RiskArea
    finding_type: FindingType
    severity: Severity
    title: str = ""
    description: str = ""
    impact: str = ""
    required_action: str = ""
    timeframe_days: int = 180

    def __post_init__(self):
        """Generate finding content based on parameters"""
        if not self.title:
            self.title = self._generate_title()
        if not self.description:
            self.description = self._generate_description()
        if not self.impact:
            self.impact = self._generate_impact()
        if self.finding_type == FindingType.MRIA:
            self.timeframe_days = random.choice([15, 30, 45, 60])
        else:
            self.timeframe_days = random.choice([90, 120, 180, 270, 365])
        if not self.required_action:
            self.required_action = self._generate_required_action()

    def _generate_title(self) -> str:
        """Generate finding title"""
        templates = {
            RiskArea.CREDIT_RISK: [
                "Deficiencies in Credit Risk Management",
                "Inadequate Loan Review Function",
                "Weaknesses in Underwriting Standards",
            ],
            RiskArea.LIQUIDITY_RISK: [
                "Inadequate Liquidity Stress Testing",
                "Weaknesses in Contingency Funding Plan",
                "Deficiencies in Funds Management",
            ],
            RiskArea.BSA_AML: [
                "BSA/AML Compliance Deficiencies",
                "Inadequate Customer Due Diligence",
                "Suspicious Activity Monitoring Weaknesses",
            ],
        }
        templates_for_area = templates.get(self.risk_area, ["Deficiencies in " + self.risk_area.value])
        return random.choice(templates_for_area)

    def _generate_description(self) -> str:
        """Generate detailed finding description"""
        templates = {
            RiskArea.CREDIT_RISK: """During the examination, we identified deficiencies in the Bank's credit risk management processes.
Specifically, the Bank's loan review function lacks independence and adequate staffing to effectively
identify emerging credit quality issues. Our sample review revealed {issue_count} loans totaling ${loan_amount}M
that were inadequately risk-rated, with {pct}% requiring downgrade to classified status.""",

            RiskArea.LIQUIDITY_RISK: """The Bank's liquidity risk management framework has material weaknesses.
Internal liquidity stress testing does not adequately capture the Bank's funding vulnerabilities,
particularly related to the concentration of uninsured deposits ({pct}% of total deposits). The Bank's
contingency funding plan has not been updated since {year} and does not reflect current balance sheet composition.""",

            RiskArea.BSA_AML: """The Bank's BSA/AML compliance program has material deficiencies. Customer due
diligence procedures are inadequate for {pct}% of higher-risk customer relationships reviewed. The suspicious
activity monitoring system generated {issue_count} alerts that were inadequately investigated.""",
        }

        template = templates.get(self.risk_area,
            """Examiners identified deficiencies in the Bank's {risk_area} framework. During our review, we noted
{issue_count} instances where the Bank's practices did not meet supervisory expectations.""")

        return template.format(
            risk_area=self.risk_area.value,
            issue_count=random.randint(5, 25),
            loan_amount=round(random.uniform(10, 150), 1),
            pct=random.randint(15, 45),
            year=random.randint(2019, 2023),
        )

    def _generate_impact(self) -> str:
        """Generate impact statement"""
        impact_templates = {
            Severity.LOW: "These deficiencies present moderate risk to the Bank's safety and soundness if not addressed.",
            Severity.MODERATE: "These deficiencies present elevated risk to the Bank and could adversely impact financial condition if left unaddressed.",
            Severity.HIGH: "These deficiencies present significant risk to the Bank's safety and soundness and require prompt corrective action.",
            Severity.CRITICAL: "These deficiencies pose an immediate threat to the Bank's viability and must be addressed without delay."
        }
        return impact_templates[self.severity]

    def _generate_required_action(self) -> str:
        """Generate required action statement"""
        if self.finding_type == FindingType.MRIA:
            return f"""The Board of Directors is required to immediately ensure that management develops and implements
a comprehensive remediation plan to address the deficiencies noted above. This plan must include specific
milestones, responsible parties, and completion dates. A written response must be submitted to the Federal
Reserve within {min(30, self.timeframe_days)} days of this letter."""
        else:
            return f"""The Board of Directors is required to ensure that management develops and implements an enhanced
{self.risk_area.value.lower()} framework that addresses the deficiencies noted above. A detailed corrective
action plan should be submitted to the Federal Reserve within {min(90, self.timeframe_days)} days, with full
implementation expected within {self.timeframe_days} days of this letter."""


@dataclass
class CAMELSExamination:
    """Represents a full CAMELS examination"""
    bank: BankProfile
    exam_start_date: datetime
    exam_end_date: datetime
    report_date: datetime
    examination_type: str = "Full-Scope"
    findings: List[ExaminationFinding] = field(default_factory=list)
    loan_sample_pct: float = 0.0
    examiner_in_charge: str = ""

    def __post_init__(self):
        """Initialize examination details"""
        if not self.examiner_in_charge:
            self.examiner_in_charge = self._generate_examiner_name()
        if self.loan_sample_pct == 0.0:
            self.loan_sample_pct = round(random.uniform(20, 50), 1)

    def _generate_examiner_name(self) -> str:
        """Generate realistic examiner name"""
        first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia"]
        return f"{random.choice(first_names)} {random.choice(last_names)}"

    def latest_prior_snapshot(self) -> Optional[ExamHistorySnapshot]:
        """Get the most recent prior examination snapshot"""
        if not self.bank.prior_examinations:
            return None
        return max(self.bank.prior_examinations, key=lambda x: x.exam_date)


# ============================================================================
# TEXT GENERATION FUNCTIONS
# ============================================================================

def generate_supervisory_letter(
    examination: CAMELSExamination,
    findings: List[ExaminationFinding],
) -> str:
    """Generate supervisory letter text."""

    letter = f"""
BOARD OF GOVERNORS
OF THE
FEDERAL RESERVE SYSTEM
WASHINGTON, D.C. 20551

DIVISION OF SUPERVISION AND REGULATION

{examination.report_date.strftime('%B %d, %Y')}

CONFIDENTIAL SUPERVISORY INFORMATION

Board of Directors
{examination.bank.name}
{examination.bank.location[0]}, {examination.bank.location[1]}

Dear Members of the Board:

This letter summarizes supervisory concerns identified during the examination of {examination.bank.name}
(RSSD {examination.bank.rssd}) conducted by the Federal Reserve Bank as of {examination.exam_end_date.strftime('%B %d, %Y')}.

The examination reviewed the Bank's {', '.join([f.risk_area.value for f in findings[:3]])}{',' if len(findings) > 3 else ''}
{' and other areas' if len(findings) > 3 else ''} and identified {len(findings)} matter{'s' if len(findings) != 1 else ''}
requiring {'immediate ' if any(f.finding_type == FindingType.MRIA for f in findings) else ''}attention.

"""

    # Add each finding
    for i, finding in enumerate(findings, 1):
        letter += f"""
{'='*80}
FINDING #{i}: {finding.title}
{'='*80}

Type: {finding.finding_type.value}
Severity: {finding.severity.value}
Risk Area: {finding.risk_area.value}

Description:
{finding.description}

Impact:
{finding.impact}

Required Action:
{finding.required_action}

Context:
- Composite Rating: {examination.bank.composite_rating}
- Exam Loan Sample: {examination.loan_sample_pct}% of portfolio reviewed
- Total Assets: ${examination.bank.total_assets:,.1f} million; Business Model: {examination.bank.business_model.value}
- Expected Remediation Timeline: {finding.timeframe_days} days
- Citations: {CITATIONS_BY_RISK.get(finding.risk_area.value, 'Applicable supervisory guidance and CFR references')}
"""

    # MRIA Appendix
    mrias = [f for f in findings if f.finding_type == FindingType.MRIA]
    if mrias:
        letter += f"""
{'='*80}
APPENDIX I: MATTERS REQUIRING IMMEDIATE ATTENTION (MRIAs)
{'='*80}

"""
        for idx, finding in enumerate(mrias, 1):
            due_date = examination.report_date + timedelta(days=finding.timeframe_days)
            letter += f"""MRIA #{idx}: {finding.title}

Issue: {finding.description}
Required Action: Submit a remediation plan by {due_date.strftime('%B %d, %Y')} that includes milestones, responsible parties, and board approval steps.

"""

    # Closing
    letter += f"""
{'='*80}

The Board of Directors should review this letter and provide a written response addressing the
findings noted above. Please contact {examination.examiner_in_charge}, the examiner-in-charge,
at the Federal Reserve Bank with any questions.

Sincerely,

{examination.examiner_in_charge}
Senior Supervisory Officer
Federal Reserve Bank
"""

    return letter


def generate_camels_summary(examination: CAMELSExamination) -> str:
    """Generate CAMELS ratings summary section"""

    bank = examination.bank

    summary = f"""
{'='*80}
SUMMARY OF EXAMINATION RATINGS
{'='*80}

Institution: {bank.name}
RSSD: {bank.rssd}
Total Assets: ${bank.total_assets:,.1f} million
Location: {bank.location[0]}, {bank.location[1]}

Examination Period: {examination.exam_start_date.strftime('%B %d, %Y')} to {examination.exam_end_date.strftime('%B %d, %Y')}
Report Date: {examination.report_date.strftime('%B %d, %Y')}
Examination Type: {examination.examination_type}

UNIFORM FINANCIAL INSTITUTIONS RATING SYSTEM (CAMELS)

Current Ratings:
    Composite:          {bank.composite_rating}
    Capital:            {bank.capital_rating}
    Asset Quality:      {bank.asset_quality_rating}
    Management:         {bank.management_rating}
    Earnings:           {bank.earnings_rating}
    Liquidity:          {bank.liquidity_rating}
    Sensitivity:        {bank.sensitivity_rating}

Rating Definitions:
    1 = Strong - Highest rating indicating strong performance and risk management
    2 = Satisfactory - Satisfactory performance and risk management
    3 = Fair - Financial condition or risk management has weaknesses
    4 = Marginal - Serious financial weaknesses or unsatisfactory risk management
    5 = Unsatisfactory - Critical financial weaknesses and inadequate risk management

FINANCIAL PERFORMANCE SUMMARY

Capital Ratios:
    Tier 1 Leverage Ratio:          {bank.tier1_leverage}%
    Total Risk-Based Capital:       {bank.total_rbc}%

Asset Quality:
    NPAs / Total Assets:            {bank.npa_ratio}%

Earnings:
    Return on Assets (ROA):         {bank.roa}%
    Return on Equity (ROE):         {bank.roe}%
    Net Interest Margin (NIM):      {bank.nim}%
    Efficiency Ratio:               {bank.efficiency_ratio}%

Liquidity:
    Loan to Deposit Ratio:          {bank.loan_to_deposit}%

EXAMINATION SCOPE

This was a {examination.examination_type.lower()} examination of {bank.name}.
Examination procedures included a review of {examination.loan_sample_pct}% of the commercial loan portfolio,
assessment of risk management practices across all major risk areas, evaluation of internal controls,
and review of compliance with applicable laws and regulations.

MATTERS REQUIRING ATTENTION

The examination identified {len(examination.findings)} supervisory matter{'s' if len(examination.findings) != 1 else ''}
requiring attention, including {sum(1 for f in examination.findings if f.finding_type == FindingType.MRIA)} matter{'s' if sum(1 for f in examination.findings if f.finding_type == FindingType.MRIA) != 1 else ''}
requiring immediate attention (MRIA) and {sum(1 for f in examination.findings if f.finding_type == FindingType.MRA)} matter{'s' if sum(1 for f in examination.findings if f.finding_type == FindingType.MRA) != 1 else ''}
requiring attention (MRA).

{'='*80}
"""

    return summary


def generate_lfbo_rating_letter(examination: CAMELSExamination) -> str:
    """Generate an LFBO rating letter"""

    bank = examination.bank
    prior_snapshot = examination.latest_prior_snapshot()

    # Build rating table
    rows = [
        ("Capital Planning & Positions", 'capital', bank.capital_rating),
        ("Liquidity Risk Management", 'liquidity', bank.liquidity_rating),
        ("Governance & Controls", 'management', bank.management_rating)
    ]

    header = f"{'Component':<32} | {'Previous Rating':<30} | {'Current Rating':<30}"
    table_lines = [header, "-" * len(header)]

    for label, component_key, rating in rows:
        current_text = f"{RATING_DESCRIPTIONS.get(rating, 'Not Rated')} / {examination.report_date.strftime('%m/%d/%Y')}"
        if prior_snapshot:
            prev_value = prior_snapshot.component_ratings.get(component_key, prior_snapshot.composite_rating)
            prev_text = f"{RATING_DESCRIPTIONS.get(prev_value, 'Not Rated')} / {prior_snapshot.exam_date.strftime('%m/%d/%Y')}"
        else:
            prev_text = "Not Previously Rated"
        table_lines.append(f"{label:<32} | {prev_text:<30} | {current_text:<30}")

    rating_table = "\n".join(table_lines)

    # Generate address
    street_numbers = random.randint(100, 9999)
    street_names = ["Market Street", "Main Street", "First Avenue"]
    street = random.choice(street_names)

    if prior_snapshot:
        prior_text = f"previously communicated as {RATING_DESCRIPTIONS.get(prior_snapshot.composite_rating, 'Not Rated')} on {prior_snapshot.exam_date.strftime('%B %d, %Y')}"
    else:
        prior_text = "being conveyed for the first time"

    letter = f"""BOARD OF GOVERNORS
OF THE
FEDERAL RESERVE SYSTEM

LFBO DEDICATED SUPERVISORY TEAM LEAD
LARGE INSTITUTIONS SUPERVISION GROUP
SUPERVISION + CREDIT

{examination.report_date.strftime('%B %d, %Y')}

RESTRICTED FR // EXTERNAL
TRANSMITTED BY SECURE EMAIL

Board of Directors
{bank.name}
{street_numbers} {street}
{bank.location[0]}, {bank.location[1]}

Subject: LFBO Component Rating Communication

Dear Board Members:

This letter conveys the Large Financial Institution (LFI) rating conclusions for {bank.name} (RSSD {bank.rssd}).
The Federal Reserve's assessment reflects the body of horizontal, firm-specific, and continuous monitoring work,
and is {prior_text}.

LFI Rating Summary
{rating_table}

Supervisory Assessment

Capital Planning & Positions remain {RATING_DESCRIPTIONS.get(bank.capital_rating, 'Not Rated').lower()}.
The Tier 1 leverage ratio is {bank.tier1_leverage:.1f}%.
The total risk-based capital ratio is {bank.total_rbc:.1f}%.

Liquidity Risk Management is {RATING_DESCRIPTIONS.get(bank.liquidity_rating, 'Not Rated').lower()}.
The loan-to-deposit ratio is {bank.loan_to_deposit:.1f}%.
Stress testing discussions highlighted depositor behavior sensitivities and contingency funding assumptions requiring continued refinement.

Governance & Controls are {RATING_DESCRIPTIONS.get(bank.management_rating, 'Not Rated').lower()}, reflecting the linkage between risk management, earnings, and asset quality.
Nonperforming assets measure {bank.npa_ratio:.1f}% of total assets, {'elevated relative to peers' if bank.npa_ratio > 2.5 else 'within peer tolerances'};
return on assets of {bank.roa:.2f}% {'remains pressured' if bank.roa < 0.8 else 'supports capital generation'}.

Supervisory Expectations

The following actions are required to address outstanding supervisory concerns:
"""

    # Add finding bullets
    if examination.findings:
        sorted_findings = sorted(
            examination.findings,
            key=lambda f: (0 if f.finding_type == FindingType.MRIA else 1, -f.timeframe_days)
        )
        for finding in sorted_findings[:4]:
            action = "Submit" if finding.finding_type == FindingType.MRIA else "Provide"
            letter += f"• {action} a detailed plan addressing {finding.title} within {min(90, finding.timeframe_days)} days.\n"
    else:
        letter += "• Provide a progress update on prior remediation plans within 60 days.\n"

    letter += f"""
• Provide quarterly updates describing progress against capital planning milestones and liquidity monetization triggers.

The Federal Reserve will monitor remediation through ongoing supervision and targeted work. Please engage your Dedicated Supervisory
Team Lead if clarification is required.

Sincerely,

{examination.examiner_in_charge}
LFBO Dedicated Supervisory Team Lead
Large Institutions Supervision Group

CONFIDENTIAL SUPERVISORY INFORMATION
"""

    return letter


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_sample_bank() -> BankProfile:
    """Create a sample bank for testing"""
    return BankProfile(
        name="First National Bank of Commerce",
        rssd="1234567",
        total_assets=2500.0,
        location=("San Francisco", "CA"),
        charter_date=datetime(1985, 3, 15),
        business_model=BusinessModel.COMMERCIAL,
        composite_rating=3,
        capital_rating=2,
        asset_quality_rating=3,
        management_rating=3,
        earnings_rating=2,
        liquidity_rating=3,
        sensitivity_rating=2,
    )


def create_sample_findings() -> List[ExaminationFinding]:
    """Create sample examination findings"""
    return [
        ExaminationFinding(
            risk_area=RiskArea.LIQUIDITY_RISK,
            finding_type=FindingType.MRIA,
            severity=Severity.HIGH,
        ),
        ExaminationFinding(
            risk_area=RiskArea.CREDIT_RISK,
            finding_type=FindingType.MRA,
            severity=Severity.MODERATE,
        ),
        ExaminationFinding(
            risk_area=RiskArea.BSA_AML,
            finding_type=FindingType.MRA,
            severity=Severity.MODERATE,
        ),
    ]


def create_sample_examination() -> CAMELSExamination:
    """Create a sample examination for testing"""
    bank = create_sample_bank()
    findings = create_sample_findings()

    # Add prior examination history
    bank.prior_examinations.append(
        ExamHistorySnapshot(
            exam_date=datetime(2022, 6, 15),
            composite_rating=2,
            component_ratings={'capital': 2, 'liquidity': 2, 'management': 2},
            tier1_leverage=9.5,
            total_rbc=13.2,
            npa_ratio=1.2,
            roa=1.0,
            loan_to_deposit=82.0,
        )
    )

    exam_end = datetime.now()
    exam_start = exam_end - timedelta(days=45)
    report_date = exam_end + timedelta(days=30)

    return CAMELSExamination(
        bank=bank,
        exam_start_date=exam_start,
        exam_end_date=exam_end,
        report_date=report_date,
        examination_type="Full-Scope Safety and Soundness",
        findings=findings,
        loan_sample_pct=35.5,
    )


def generate_example_documents() -> Tuple[str, str, str]:
    """
    Generate all three document types using sample data.

    Returns:
        Tuple of (supervisory_letter, camels_summary, lfbo_letter)
    """
    examination = create_sample_examination()

    supervisory_letter = generate_supervisory_letter(examination, examination.findings)
    camels_summary = generate_camels_summary(examination)
    lfbo_letter = generate_lfbo_rating_letter(examination)

    return supervisory_letter, camels_summary, lfbo_letter


# ============================================================================
# MAIN - Example Usage
# ============================================================================

if __name__ == "__main__":
    print("Generating example documents...\n")

    supervisory_letter, camels_summary, lfbo_letter = generate_example_documents()

    # Save to files
    with open("example_supervisory_letter.txt", "w") as f:
        f.write(supervisory_letter)
    print("✓ Saved: example_supervisory_letter.txt")

    with open("example_camels_summary.txt", "w") as f:
        f.write(camels_summary)
    print("✓ Saved: example_camels_summary.txt")

    with open("example_lfbo_letter.txt", "w") as f:
        f.write(lfbo_letter)
    print("✓ Saved: example_lfbo_letter.txt")

    print("\nDone! All documents generated successfully.")
    print("\nYou can now copy this file to any Python project and use it standalone.")
