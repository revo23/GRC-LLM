from app.models.control import Control, FrameworkDefinition

FRAMEWORK = FrameworkDefinition(
    id="ftc_safeguards",
    name="FTC Safeguards Rule",
    version="2023",
    family_weights={
        "Information Security Program": 1.4,
        "Risk Assessment": 1.3,
        "Safeguards Implementation": 1.4,
        "Vendor Oversight": 1.1,
        "Incident Response": 1.3,
    },
    controls=[
        # Element 1: Designate a Qualified Individual
        Control("FTC-1", "Qualified Individual",
                "Designate a qualified individual responsible for overseeing, implementing, and enforcing the organization's information security program. This person must have sufficient authority, resources, and expertise.",
                "Information Security Program", 1.3),

        # Element 2: Conduct a Risk Assessment
        Control("FTC-2", "Risk Assessment",
                "Based on the Risk Assessment, design and implement safeguards to control the risks identified. Include employee training and management, information systems (including storage, access, transport), and detecting and responding to attacks.",
                "Risk Assessment", 1.4),

        # Element 3: Design and Implement Safeguards
        Control("FTC-3.1", "Access Controls",
                "Limit who can access customer information and control access through physical and technical means. Implement role-based access controls and least-privilege principles.",
                "Safeguards Implementation", 1.5),
        Control("FTC-3.2", "Inventory and Classification",
                "Maintain a complete and accurate inventory of where customer information is stored, transmitted, or processed. Classify data based on sensitivity.",
                "Safeguards Implementation", 1.3),
        Control("FTC-3.3", "Encryption",
                "Encrypt customer information held or transmitted by your business. Use industry-standard encryption for data at rest and in transit. Establish a key management process.",
                "Safeguards Implementation", 1.4),
        Control("FTC-3.4", "Secure Development Practices",
                "Adopt secure development practices for in-house developed applications. Address security vulnerabilities on an ongoing basis. Conduct security testing of applications.",
                "Safeguards Implementation", 1.2),
        Control("FTC-3.5", "Multifactor Authentication",
                "Use multifactor authentication for any individual accessing any information system with customer information, unless your qualified individual has approved reasonably equivalent or stronger controls in writing.",
                "Safeguards Implementation", 1.5),
        Control("FTC-3.6", "Secure Disposal of Data",
                "Dispose of customer information securely. Develop and implement policies for the secure disposal of customer information in any format when no longer needed.",
                "Safeguards Implementation", 1.2),
        Control("FTC-3.7", "Change Management",
                "Anticipate and evaluate changes to your information system or network that may create new risks to customer information. Conduct a thorough review before implementation.",
                "Safeguards Implementation", 1.2),
        Control("FTC-3.8", "Monitoring and Testing",
                "Regularly monitor the effectiveness of your safeguards. Conduct continuous monitoring or annual penetration testing and biannual vulnerability assessments.",
                "Safeguards Implementation", 1.3),

        # Element 4: Regularly Monitor and Test Safeguards
        Control("FTC-4", "Employee Training",
                "Train staff to implement your information security program. Provide security awareness training to all personnel who handle customer information. Update training regularly.",
                "Information Security Program", 1.2),

        # Element 5: Oversee Service Providers
        Control("FTC-5", "Service Provider Oversight",
                "Select and retain service providers that maintain appropriate safeguards for customer information. Require service providers by contract to implement and maintain such safeguards. Periodically monitor providers.",
                "Vendor Oversight", 1.2),

        # Element 6: Keep the Information Security Program Current
        Control("FTC-6", "Program Updates",
                "Evaluate and adjust your information security program in light of the results of testing and monitoring, relevant changes to your operations or business arrangements, or any other circumstances that may have a material impact.",
                "Information Security Program", 1.1),

        # Element 7: Create a Written Incident Response Plan
        Control("FTC-7", "Incident Response Plan",
                "Establish a written incident response plan for responding to a security event. Include goals, roles and responsibilities, internal processes, communication strategies, and remediation and documentation practices.",
                "Incident Response", 1.4),

        # Element 8: Require Your Qualified Individual to Report
        Control("FTC-8", "Board Reporting",
                "Require the Qualified Individual to report to the board of directors or equivalent governing body on the overall status of the information security program and material matters at least annually.",
                "Information Security Program", 1.1),

        # Element 9: Safeguards for Customer Information
        Control("FTC-9", "Customer Information Safeguards",
                "Develop, implement, and maintain comprehensive safeguards to protect customer information throughout its lifecycle including collection, storage, use, transmission, and disposal.",
                "Safeguards Implementation", 1.3),
    ],
)
