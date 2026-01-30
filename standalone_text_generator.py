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
that were inadequately risk-rated, with {pct}% requiring downgrade to classified status.

The examination team conducted a comprehensive review of the Bank's lending portfolio, including commercial real estate,
commercial and industrial, and consumer loans. We analyzed {sample_size} loan relationships representing approximately
{sample_pct}% of the total loan portfolio. Our analysis revealed systematic weaknesses in the loan origination process,
particularly in the areas of financial statement analysis, collateral valuation, and covenant monitoring.

Furthermore, the Bank's credit policy lacks specific guidance on acceptable debt service coverage ratios, loan-to-value limits,
and industry concentration thresholds. The credit administration function does not have adequate systems to track and report
credit exceptions, resulting in {exception_count} instances where loans were approved outside of established credit parameters
without proper exception documentation or board approval. These weaknesses increase the Bank's exposure to credit losses and
diminish the Board's ability to provide effective oversight of credit risk.""",

            RiskArea.LIQUIDITY_RISK: """The Bank's liquidity risk management framework has material weaknesses.
Internal liquidity stress testing does not adequately capture the Bank's funding vulnerabilities,
particularly related to the concentration of uninsured deposits ({pct}% of total deposits). The Bank's
contingency funding plan has not been updated since {year} and does not reflect current balance sheet composition.

Our examination included a thorough review of the Bank's asset-liability management practices, funding strategies, and
liquidity risk monitoring systems. We identified significant concerns regarding the Bank's reliance on volatile funding sources,
including brokered deposits totaling ${broker_deposits}M ({broker_pct}% of total deposits) and borrowings from the Federal
Home Loan Bank of ${fhlb_amount}M. The Bank's internal liquidity stress scenarios do not adequately consider the potential
for concurrent deposit outflows and reduced borrowing capacity during stressed conditions.

Additionally, the Bank's liquidity buffer consists primarily of investment securities with embedded interest rate risk,
and the contingent borrowing capacity has not been validated through test transactions in over {months} months. The funds
management committee meets only quarterly, which is insufficient given the current volatility in funding markets and the
Bank's aggressive growth strategy. Management information systems do not provide real-time visibility into deposit flows
or concentration metrics, limiting the Bank's ability to respond quickly to emerging liquidity pressures.""",

            RiskArea.BSA_AML: """The Bank's BSA/AML compliance program has material deficiencies. Customer due
diligence procedures are inadequate for {pct}% of higher-risk customer relationships reviewed. The suspicious
activity monitoring system generated {issue_count} alerts that were inadequately investigated.

The examination included a comprehensive review of the Bank's BSA/AML compliance program, including customer due diligence,
suspicious activity monitoring, currency transaction reporting, and OFAC compliance. We identified systemic deficiencies in
the Bank's ability to identify, monitor, and report potentially suspicious activity. The Bank processed {alert_count} alerts
during the review period, but only filed {sar_count} Suspicious Activity Reports, raising concerns about the adequacy of
alert disposition and investigation processes.

The Bank's customer risk rating methodology does not adequately consider all relevant risk factors, including geographic risk,
product/service risk, and customer behavior. We identified {high_risk_count} high-risk customer relationships that lacked
enhanced due diligence documentation, including {pep_count} politically exposed persons and {msb_count} money service businesses.
Transaction monitoring scenarios have not been validated or tuned in over {validation_months} months, and several scenarios
are generating excessive false positive alerts without proper management review or optimization.

Additionally, the BSA Officer position has experienced {turnover_count} turnovers in the past {turnover_years} years, and
current BSA staffing levels are inadequate given the Bank's risk profile and transaction volumes. Independent testing of the
BSA/AML program identified {testing_issues} issues in the prior examination cycle, and management has not fully addressed
these deficiencies. The Board receives limited information regarding BSA/AML compliance, and board members demonstrated
limited understanding of the Bank's BSA/AML risk exposure during examination interviews.""",
        }

        template = templates.get(self.risk_area,
            """Examiners identified deficiencies in the Bank's {risk_area} framework. During our review, we noted
{issue_count} instances where the Bank's practices did not meet supervisory expectations.

Our examination included a detailed assessment of the Bank's policies, procedures, and operational controls related to
{risk_area}. We reviewed {sample_size} transactions and activities, interviewed key personnel, and analyzed management
reporting systems. The examination revealed gaps in risk identification, measurement, monitoring, and control processes.

Specific deficiencies include inadequate board and senior management oversight, insufficient staffing and expertise,
outdated or incomplete policies and procedures, and management information systems that do not provide timely and accurate
risk reporting. These weaknesses limit the Bank's ability to effectively manage {risk_area} and increase the potential for
operational losses, regulatory sanctions, and reputational damage.""")

        return template.format(
            risk_area=self.risk_area.value,
            issue_count=random.randint(5, 25),
            loan_amount=round(random.uniform(10, 150), 1),
            pct=random.randint(15, 45),
            year=random.randint(2019, 2023),
            sample_size=random.randint(50, 200),
            sample_pct=random.randint(20, 50),
            exception_count=random.randint(15, 45),
            broker_deposits=round(random.uniform(50, 500), 1),
            broker_pct=random.randint(10, 30),
            fhlb_amount=round(random.uniform(100, 800), 1),
            months=random.randint(12, 36),
            alert_count=random.randint(500, 5000),
            sar_count=random.randint(5, 50),
            high_risk_count=random.randint(20, 80),
            pep_count=random.randint(2, 15),
            msb_count=random.randint(5, 25),
            validation_months=random.randint(18, 48),
            turnover_count=random.randint(2, 5),
            turnover_years=random.randint(2, 4),
            testing_issues=random.randint(8, 20),
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

    prior = examination.latest_prior_snapshot()
    assets_change = ((examination.bank.total_assets - (prior.total_assets if prior and hasattr(prior, 'total_assets') else examination.bank.total_assets * 0.9)) /
                    (prior.total_assets if prior and hasattr(prior, 'total_assets') else examination.bank.total_assets * 0.9) * 100) if prior else random.uniform(-5, 15)

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
The examination was conducted in accordance with Federal Reserve System policies and procedures and covered the period
from {examination.exam_start_date.strftime('%B %d, %Y')} through {examination.exam_end_date.strftime('%B %d, %Y')}.

EXECUTIVE SUMMARY

The Bank operates as a {examination.bank.business_model.value.lower()} institution with total assets of ${examination.bank.total_assets:,.1f} million
as of the examination date, representing {'+' if assets_change > 0 else ''}{assets_change:.1f}% {'growth' if assets_change > 0 else 'contraction'} since the prior examination.
The Bank was chartered on {examination.bank.charter_date.strftime('%B %d, %Y')} and operates {random.randint(1, 8)} {'branch' if random.randint(1, 8) == 1 else 'branches'} in
{examination.bank.location[0]}, {examination.bank.location[1]}{' and surrounding communities' if random.randint(1, 8) > 1 else ''}.

The examination scope included a comprehensive review of the Bank's financial condition, risk management practices, and compliance
with applicable laws and regulations. Examiners conducted detailed assessments of capital adequacy, asset quality, management capabilities,
earnings performance, liquidity position, and sensitivity to market risk. The examination team reviewed approximately {examination.loan_sample_pct}%
of the Bank's loan portfolio, totaling ${examination.bank.total_assets * random.uniform(0.15, 0.30):,.1f} million, and conducted interviews with
{random.randint(12, 25)} members of the Board, senior management, and key personnel.

The examination reviewed the Bank's {', '.join([f.risk_area.value for f in findings[:3]])}{',' if len(findings) > 3 else ''}
{' and other areas' if len(findings) > 3 else ''} and identified {len(findings)} matter{'s' if len(findings) != 1 else ''}
requiring {'immediate ' if any(f.finding_type == FindingType.MRIA for f in findings) else ''}attention.
{'These matters represent significant concerns regarding the Banks safety and soundness' if any(f.finding_type == FindingType.MRIA for f in findings) else 'These matters require Board attention and management action'}
and must be addressed in accordance with the timelines specified in this letter.

EXAMINATION SCOPE AND METHODOLOGY

The examination team consisted of {random.randint(4, 12)} examiners and specialists who spent {random.randint(15, 45)} days on-site and conducted
additional off-site analysis. The examination included the following key activities:

- Review of board and committee meeting minutes from the past {random.randint(12, 24)} months
- Analysis of the Bank's strategic plan, budget, and financial projections
- Assessment of the loan portfolio through statistical sampling and targeted transaction testing
- Evaluation of the Bank's internal audit function and independent risk review processes
- Testing of information technology systems, cybersecurity controls, and business continuity planning
- Review of compliance management systems and consumer protection practices
- Assessment of vendor management and third-party risk management frameworks
- Evaluation of the Bank's capital planning processes and stress testing capabilities

The examination was led by {examination.examiner_in_charge}, Examiner-in-Charge, with support from specialists in credit risk,
operational risk, compliance, and information technology. The examination findings and conclusions were discussed with the
Board of Directors and senior management during the exit meeting on {examination.exam_end_date.strftime('%B %d, %Y')}.

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

CONCLUSION AND NEXT STEPS

The Board of Directors is responsible for ensuring that management develops and implements comprehensive corrective action
plans to address all matters identified in this letter. Each corrective action plan must include specific action steps,
responsible parties, implementation timelines, and metrics for measuring progress and effectiveness.

The Bank is required to submit written responses to the Federal Reserve within {'30 days' if mrias else '90 days'} of the date
of this letter, describing the corrective actions that have been or will be taken to address each matter. The response should
include detailed action plans with milestones and expected completion dates. Management should provide regular progress updates
to the Board of Directors, and the Board should ensure appropriate oversight of remediation efforts.

The Federal Reserve will conduct follow-up examinations and targeted reviews to assess the Bank's progress in addressing the
matters identified in this letter. Failure to take timely and effective corrective action may result in additional supervisory
measures, including formal enforcement actions. The Board and senior management should contact the Federal Reserve if they have
questions regarding the matters identified in this letter or require clarification regarding supervisory expectations.

BOARD RESPONSIBILITIES

The Board of Directors has ultimate responsibility for ensuring the safe and sound operation of the Bank. The Board should:

- Review and discuss this letter at the next regularly scheduled Board meeting
- Ensure that management develops comprehensive corrective action plans for each matter
- Establish clear accountability and assign responsibility for remediation efforts
- Monitor progress regularly through detailed management reporting
- Ensure adequate resources are allocated to address identified deficiencies
- Consider engaging external expertise if internal capabilities are insufficient
- Communicate regularly with the Federal Reserve regarding remediation progress

The Federal Reserve expects the Board to maintain active oversight of the Bank's risk profile and to ensure that management
operates the Bank in a safe and sound manner in compliance with applicable laws and regulations. The Board should ensure that
the Bank has appropriate risk management frameworks, internal controls, and governance structures to identify, measure, monitor,
and control risks across all material business activities.

REGULATORY EXPECTATIONS

The Federal Reserve emphasizes the importance of timely and effective remediation of the matters identified in this letter.
The Bank should prioritize remediation efforts based on the severity and potential impact of each matter, with immediate attention
to matters requiring immediate attention. Management should provide the Board with regular updates on remediation progress, including
status updates on action plan milestones, identification of any impediments to timely completion, and requests for additional resources
if needed.

The Bank should ensure that all corrective actions are sustainable and that appropriate policies, procedures, systems, and controls
are in place to prevent recurrence of similar deficiencies. The Federal Reserve will evaluate the adequacy of the Bank's corrective
actions through ongoing supervision and follow-up examinations.

This letter is considered confidential supervisory information and should be maintained in the Bank's examination records. Distribution
should be limited to the Board of Directors, senior management, and other individuals with a need to know. Unauthorized disclosure
of confidential supervisory information may result in regulatory sanctions.

If you have any questions regarding this letter or the matters identified herein, please contact {examination.examiner_in_charge} at
the Federal Reserve Bank.

Sincerely,

{examination.examiner_in_charge}
Senior Supervisory Officer
Federal Reserve Bank

CC: {examination.bank.name} Management
    Federal Reserve Bank Examination File
    Federal Reserve Board of Governors
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

DETAILED COMPONENT ANALYSIS

CAPITAL (C) - Rating: {bank.capital_rating}

The Capital component assesses the level and quality of capital and the overall financial condition of the institution.
The Bank's Tier 1 Leverage Ratio of {bank.tier1_leverage}% and Total Risk-Based Capital ratio of {bank.total_rbc}%
{'exceed' if bank.tier1_leverage > 8 else 'meet' if bank.tier1_leverage > 6 else 'fall below'} well-capitalized standards.
Capital planning processes {'are adequate' if bank.capital_rating <= 2 else 'require improvement'} and stress testing
capabilities {'align with' if bank.capital_rating <= 2 else 'do not meet'} supervisory expectations for an institution
of this size and complexity.

The Bank's capital position is {'strong' if bank.capital_rating == 1 else 'adequate' if bank.capital_rating == 2 else 'satisfactory' if bank.capital_rating == 3 else 'weak'}
relative to the Bank's risk profile. The Bank maintains {'diverse' if bank.capital_rating <= 2 else 'limited'} capital raising
capabilities through {'multiple channels including' if bank.capital_rating <= 2 else 'primarily'} retained earnings
{', equity issuance, and subordinated debt' if bank.capital_rating <= 2 else ''}. The capital planning process
{'incorporates comprehensive stress testing' if bank.capital_rating <= 2 else 'requires enhanced stress testing'} that
{'adequately considers' if bank.capital_rating <= 2 else 'does not fully reflect'} the Bank's key risks and vulnerabilities.

ASSET QUALITY (A) - Rating: {bank.asset_quality_rating}

The Asset Quality component reflects the quantity of existing and potential credit risk associated with the loan and investment
portfolios. The Bank's nonperforming assets to total assets ratio of {bank.npa_ratio}% is {'favorable' if bank.npa_ratio < 1 else 'acceptable' if bank.npa_ratio < 2 else 'elevated'}
compared to peer institutions of similar size and business model.

Credit risk management practices are {'sound' if bank.asset_quality_rating <= 2 else 'adequate' if bank.asset_quality_rating == 3 else 'weak'}
with {'strong' if bank.asset_quality_rating <= 2 else 'acceptable' if bank.asset_quality_rating == 3 else 'inadequate'} underwriting
standards, loan review processes, and portfolio monitoring systems. The loan portfolio composition reflects
{'appropriate' if bank.asset_quality_rating <= 2 else 'elevated'} concentration risk in {bank.business_model.value.lower()} lending.
Management {'maintains' if bank.asset_quality_rating <= 2 else 'should enhance'} effective problem loan identification and
workout processes.

The Allowance for Loan and Lease Losses (ALLL) methodology is {'comprehensive and well-documented' if bank.asset_quality_rating <= 2 else 'adequate but requires improvement' if bank.asset_quality_rating == 3 else 'deficient'},
incorporating {'appropriate' if bank.asset_quality_rating <= 2 else 'limited'} quantitative and qualitative risk factors.
The current ALLL level of ${bank.total_assets * 0.012:,.2f} million ({round(random.uniform(0.8, 1.5), 2)}% of loans) is
{'adequate' if bank.asset_quality_rating <= 2 else 'marginally adequate' if bank.asset_quality_rating == 3 else 'insufficient'}
to absorb expected credit losses based on current portfolio risk characteristics.

MANAGEMENT (M) - Rating: {bank.management_rating}

The Management component reflects the capability of the board of directors and management to identify, measure, monitor, and
control the risks of the institution's activities. Board and management oversight is {'strong' if bank.management_rating <= 2 else 'satisfactory' if bank.management_rating == 3 else 'weak'},
with {'appropriate' if bank.management_rating <= 2 else 'adequate' if bank.management_rating == 3 else 'insufficient'} strategic
planning, risk management frameworks, and internal controls.

The Board of Directors demonstrates {'strong' if bank.management_rating <= 2 else 'adequate' if bank.management_rating == 3 else 'limited'}
understanding of the Bank's risk profile and provides {'active' if bank.management_rating <= 2 else 'satisfactory' if bank.management_rating == 3 else 'insufficient'}
oversight through {'well-functioning' if bank.management_rating <= 2 else 'adequately structured' if bank.management_rating == 3 else 'ineffective'}
board committees. Senior management possesses {'deep' if bank.management_rating <= 2 else 'sufficient' if bank.management_rating == 3 else 'limited'}
industry expertise and {'demonstrates' if bank.management_rating <= 2 else 'generally demonstrates' if bank.management_rating == 3 else 'lacks'}
sound judgment in managing the Bank's operations.

Risk management information systems provide {'comprehensive and timely' if bank.management_rating <= 2 else 'adequate' if bank.management_rating == 3 else 'insufficient'}
data to support decision-making. Internal audit and compliance functions are {'independent, adequately staffed, and effective' if bank.management_rating <= 2 else 'generally adequate but require enhancement' if bank.management_rating == 3 else 'deficient and require significant improvement'}.

EARNINGS (E) - Rating: {bank.earnings_rating}

The Earnings component measures current period earnings performance, sustainability of earnings, and the adequacy of provisions
and reserves. The Bank's ROA of {bank.roa}% and ROE of {bank.roe}% are {'strong' if bank.earnings_rating <= 2 else 'acceptable' if bank.earnings_rating == 3 else 'weak'}
relative to peers and demonstrate {'solid' if bank.earnings_rating <= 2 else 'acceptable' if bank.earnings_rating == 3 else 'weak'}
earnings capacity to support operations and capital growth.

The Net Interest Margin of {bank.nim}% reflects {'effective' if bank.nim > 3.5 else 'adequate' if bank.nim > 3.0 else 'compressed'}
spread management in the current interest rate environment. Noninterest income sources are {'diverse' if bank.earnings_rating <= 2 else 'limited'},
with {'multiple' if bank.earnings_rating <= 2 else 'few'} fee-generating business lines. The efficiency ratio of {bank.efficiency_ratio}%
indicates {'strong' if bank.efficiency_ratio < 60 else 'acceptable' if bank.efficiency_ratio < 70 else 'weak'} expense control
relative to revenue generation.

Earnings {'consistently exceed' if bank.earnings_rating <= 2 else 'generally meet' if bank.earnings_rating == 3 else 'fall short of'}
the Bank's internal performance targets and strategic objectives. Provision expense is {'appropriate' if bank.earnings_rating <= 2 else 'generally adequate' if bank.earnings_rating == 3 else 'insufficient'}
relative to asset quality trends and portfolio growth. Earnings sustainability is {'strong' if bank.earnings_rating <= 2 else 'moderate' if bank.earnings_rating == 3 else 'uncertain'}
considering competitive pressures, interest rate risks, and the Bank's strategic direction.

LIQUIDITY (L) - Rating: {bank.liquidity_rating}

The Liquidity component reflects the adequacy of the institution's current and prospective sources and uses of funds.
The Bank's loan-to-deposit ratio of {bank.loan_to_deposit}% is {'conservative' if bank.loan_to_deposit < 80 else 'moderate' if bank.loan_to_deposit < 90 else 'aggressive'}
relative to peers and provides {'ample' if bank.loan_to_deposit < 80 else 'adequate' if bank.loan_to_deposit < 90 else 'limited'}
liquidity capacity for balance sheet growth or funding stress.

Liquidity risk management processes are {'comprehensive' if bank.liquidity_rating <= 2 else 'satisfactory' if bank.liquidity_rating == 3 else 'deficient'},
with {'robust' if bank.liquidity_rating <= 2 else 'adequate' if bank.liquidity_rating == 3 else 'weak'} stress testing,
contingency funding planning, and liquidity buffer management. The Bank maintains {'diverse' if bank.liquidity_rating <= 2 else 'adequate' if bank.liquidity_rating == 3 else 'concentrated'}
funding sources through core deposits, wholesale funding, and available borrowing lines.

The liquidity position is {'strong' if bank.liquidity_rating <= 2 else 'satisfactory' if bank.liquidity_rating == 3 else 'tight'},
with {'substantial' if bank.liquidity_rating <= 2 else 'adequate' if bank.liquidity_rating == 3 else 'limited'} unencumbered
liquid assets available to meet cash flow needs. Deposit composition reflects {'stable' if bank.liquidity_rating <= 2 else 'moderate' if bank.liquidity_rating == 3 else 'elevated'}
reliance on rate-sensitive and uninsured deposits, which {'does not present' if bank.liquidity_rating <= 2 else 'moderately increases' if bank.liquidity_rating == 3 else 'significantly increases'}
funding volatility risk.

SENSITIVITY TO MARKET RISK (S) - Rating: {bank.sensitivity_rating}

The Sensitivity component reflects the degree to which changes in interest rates, foreign exchange rates, commodity prices, or
equity prices can adversely affect earnings or capital. Interest rate risk is {'well-managed' if bank.sensitivity_rating <= 2 else 'adequately managed' if bank.sensitivity_rating == 3 else 'poorly managed'},
with {'comprehensive' if bank.sensitivity_rating <= 2 else 'satisfactory' if bank.sensitivity_rating == 3 else 'weak'} measurement
systems and {'effective' if bank.sensitivity_rating <= 2 else 'adequate' if bank.sensitivity_rating == 3 else 'insufficient'}
hedging strategies to mitigate exposure.

Asset-liability management processes {'effectively identify and control' if bank.sensitivity_rating <= 2 else 'adequately monitor' if bank.sensitivity_rating == 3 else 'do not adequately address'}
interest rate risk arising from mismatches in repricing characteristics of assets and liabilities. The Bank's interest rate risk
position is {'conservative' if bank.sensitivity_rating <= 2 else 'moderate' if bank.sensitivity_rating == 3 else 'elevated'},
with earnings and capital {'well-protected' if bank.sensitivity_rating <= 2 else 'moderately exposed' if bank.sensitivity_rating == 3 else 'significantly vulnerable'}
to adverse interest rate movements.

MATTERS REQUIRING ATTENTION

The examination identified {len(examination.findings)} supervisory matter{'s' if len(examination.findings) != 1 else ''}
requiring attention, including {sum(1 for f in examination.findings if f.finding_type == FindingType.MRIA)} matter{'s' if sum(1 for f in examination.findings if f.finding_type == FindingType.MRIA) != 1 else ''}
requiring immediate attention (MRIA) and {sum(1 for f in examination.findings if f.finding_type == FindingType.MRA)} matter{'s' if sum(1 for f in examination.findings if f.finding_type == FindingType.MRA) != 1 else ''}
requiring attention (MRA).

Detailed findings and required corrective actions are provided in the separate supervisory letter dated
{examination.report_date.strftime('%B %d, %Y')}. The Bank must develop and implement comprehensive remediation plans to address
all identified matters within the specified timeframes. The Federal Reserve will conduct follow-up examinations to assess
progress in addressing these supervisory concerns.

CONCLUSION

This CAMELS rating reflects the Bank's financial condition, risk management practices, and compliance with applicable laws and
regulations as of {examination.exam_end_date.strftime('%B %d, %Y')}. The Bank should continue to {'maintain' if bank.composite_rating <= 2 else 'enhance'}
its financial condition and risk management frameworks to ensure safe and sound operations. The Board and management should
address all supervisory matters in a timely and effective manner and should contact the Federal Reserve with any questions
regarding supervisory expectations or examination findings.

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
