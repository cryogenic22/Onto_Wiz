# Regulatory Boundary Notes

These notes explain why the reference architecture has explicit market, audience, evidence, risk, and human-review boundaries. They are not a replacement for applicable law, regulation, industry codes, current product labeling, client policy, or authorized legal/medical/regulatory review.

## United States architecture implications

FDA's Office of Prescription Drug Promotion states that its mission includes helping ensure prescription drug promotion is truthful, balanced, and accurately communicated. FDA's Bad Ad materials identify issues such as omitted or downplayed risk, overstated benefit, missing fair balance or material facts, unsupported claims, misrepresented study data, and misleading comparisons.

Architecture consequences:

- Benefit claims remain coupled to current risk and qualification artifacts.
- Claims resolve to evidence and current label versions.
- Comparative or superiority language is a named high-risk transformation.
- Extracted text cannot close questions of visual prominence or overall impression.
- Automated preflight never records an approval decision.

Primary sources:

- [FDA Office of Prescription Drug Promotion](https://www.fda.gov/about-fda/cder-offices-and-divisions/office-prescription-drug-promotion-opdp)
- [FDA Bad Ad Program](https://www.fda.gov/drugs/prescription-drug-advertising-and-promotional-labeling/bad-ad-program)
- [FDA OPDP Frequently Asked Questions](https://www.fda.gov/about-fda/center-drug-evaluation-and-research-cder/opdp-frequently-asked-questions-faqs)

## Great Britain architecture implications

MHRA guidance states that prescription-only medicines cannot be advertised to the general public, while promotion to healthcare professionals and others who can prescribe or supply is addressed separately. The 2024 ABPI Code covers promotion to health professionals and other relevant decision makers and also sets standards for information about prescription-only medicines supplied to the public and patients.

Architecture consequences:

- Market and audience are mandatory applicability dimensions.
- A US HCP artifact cannot silently fall back for a GB public request.
- Promotional, disease-awareness, medical-information, and scientific-exchange purposes remain separate operating lanes.
- Market policy is a versioned source overlay, not prompt text or a global boolean.

Primary sources:

- [MHRA: Advertise your medicines](https://www.gov.uk/guidance/advertise-your-medicines)
- [MHRA Blue Guide](https://www.gov.uk/government/uploads/system/uploads/attachment_data/file/376398/Blue_Guide.pdf)
- [ABPI Code of Practice for the Pharmaceutical Industry 2024](https://www.abpi.org.uk/publications/code-of-practice-for-the-pharmaceutical-industry-2024/)

## Client implementation requirement

The synthetic market-policy records in this fixture are deliberately not presented as executable real-world rules. A client implementation must ingest the current governing sources, client SOPs, product labeling, approval records, roles, and escalation routes; identify the responsible human authorities; and run jurisdiction-specific validation before production release.

