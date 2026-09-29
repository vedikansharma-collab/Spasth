import fitz

def create_sample_policy_pdf(filename="data/sample_policies/sample_health_policy.pdf"):
    doc = fitz.open()

    # Page 1: Policy Schedule & Basic Details
    page1 = doc.new_page()
    text1 = """
HDFC ERGO HEALTH INSURANCE POLICY SCHEDULE
Policy No: POL-2026-88492
Insured Name: Rahul Sharma
Sum Insured: INR 5,00,000 (Five Lakh Rupees)
Policy Period: 01-Jan-2026 to 31-Dec-2026
Cumulative Bonus: 10% per claim-free year

SECTION 1: COVERAGE & BENEFIT SUMMARY
1.1 In-patient Hospitalization: Covered up to Sum Insured for stays exceeding 24 hours.
1.2 Room Rent Limit: Capped at 1% of Sum Insured per day (INR 5,000/day) for Standard Single Room.
1.3 ICU Charges: Capped at 2% of Sum Insured per day (INR 10,000/day).
    """
    page1.insert_text((50, 50), text1.strip(), fontsize=11)

    # Page 2: Specific Limits & Sub-limits
    page2 = doc.new_page()
    text2 = """
SECTION 2: CO-PAYMENT & SUB-LIMITS
2.1 Mandatory Co-Payment: A mandatory co-payment of 10% applies to all eligible claims.
2.2 Cataract Surgery Sub-limit: INR 40,000 per eye.
2.3 Appendectomy & Hernia Procedure Cap: INR 90,000 maximum eligible claim.
2.4 Pre-Hospitalization: Covered up to 60 days prior to admission.
2.5 Post-Hospitalization: Covered up to 90 days following discharge.

SECTION 3: WAITING PERIODS
3.1 Initial Waiting Period: 30 days from policy inception (except accidental injuries).
3.2 Named Specific Illnesses: 24 months waiting period for Knee Replacement, Hernia, and Hydrocele.
3.3 Pre-Existing Diseases (PED): 36 months continuous coverage waiting period.
    """
    page2.insert_text((50, 50), text2.strip(), fontsize=11)

    # Page 3: Exclusions & Claim Process
    page3 = doc.new_page()
    text3 = """
SECTION 4: EXCLUSIONS
4.1 Domiciliary hospitalization expenses unless approved in writing by TPA.
4.2 Cosmetic, plastic, or aesthetic procedures.
4.3 Experimental or unproven medical treatments.
4.4 Weight loss or obesity treatment.

SECTION 5: CLAIM PROCEDURE & DOCUMENTS
5.1 Intimation to Insurer/TPA within 24 hours of emergency admission.
5.2 Original discharge summary, itemized final bill, and payment receipts mandatory.
5.3 Cashless facility available at network hospitals upon pre-authorization.
    """
    page3.insert_text((50, 50), text3.strip(), fontsize=11)

    doc.save(filename)
    doc.close()
    print(f"Sample PDF created successfully at {filename}")

if __name__ == "__main__":
    create_sample_policy_pdf()
