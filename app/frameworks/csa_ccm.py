from app.models.control import Control, FrameworkDefinition

FRAMEWORK = FrameworkDefinition(
    id="csa_ccm",
    name="CSA Cloud Controls Matrix",
    version="4.0",
    family_weights={
        "Application and Interface Security": 1.3,
        "Business Continuity Management": 1.2,
        "Change Control and Configuration Management": 1.2,
        "Cryptography, Encryption and Key Management": 1.4,
        "Governance, Risk and Compliance": 1.3,
        "Human Resources": 1.0,
        "Identity and Access Management": 1.5,
        "Interoperability and Portability": 1.0,
        "Logging and Monitoring": 1.3,
        "Security Incident Management": 1.3,
        "Threat and Vulnerability Management": 1.4,
    },
    controls=[
        # AIS - Application and Interface Security
        Control("AIS-01", "Application and Interface Security Policy",
                "Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for application security to provide guidance for the appropriate planning, delivery and support of the organization's application security capabilities.",
                "Application and Interface Security", 1.2),
        Control("AIS-02", "Application Security Baseline Requirements",
                "Establish, document, and maintain baseline requirements for securing different categories of applications. Address the OWASP Top 10 vulnerabilities at minimum.",
                "Application and Interface Security", 1.3),
        Control("AIS-04", "Application Security Metrics",
                "Define and implement a process to remediate application security vulnerabilities, automating remediation when possible. Establish application security metrics and SLAs.",
                "Application and Interface Security", 1.2),

        # BCR - Business Continuity Management and Operational Resilience
        Control("BCR-01", "Business Continuity Management Policy",
                "Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for business continuity planning. Implement testing of BCM plans at least annually.",
                "Business Continuity Management", 1.2),
        Control("BCR-03", "Business Continuity Testing",
                "Establish testing procedures for business continuity and disaster recovery plans. Conduct tests at planned intervals and update plans based on test results.",
                "Business Continuity Management", 1.2),

        # CCC - Change Control and Configuration Management
        Control("CCC-01", "Change Management Policy",
                "Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for managing the risks associated with applying changes to organization assets, including application, systems, infrastructure, configuration, etc.",
                "Change Control and Configuration Management", 1.2),
        Control("CCC-04", "Unauthorized Change Protection",
                "Restrict the unauthorized addition, removal, update, and management of organization assets. Implement controls to detect and prevent unauthorized changes.",
                "Change Control and Configuration Management", 1.3),

        # CEK - Cryptography, Encryption and Key Management
        Control("CEK-01", "Encryption and Key Management Policy",
                "Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for encryption and key management. Protect encryption keys against disclosure and misuse.",
                "Cryptography, Encryption and Key Management", 1.4),
        Control("CEK-03", "Data Encryption",
                "Implement data encryption practices for data at rest, in transit, and in use. Use industry-standard encryption algorithms and key lengths.",
                "Cryptography, Encryption and Key Management", 1.4),
        Control("CEK-04", "Encryption Algorithm",
                "Use industry-accepted encryption algorithms to protect data in storage and in transit. Align with FIPS 140-2/3 standards where applicable.",
                "Cryptography, Encryption and Key Management", 1.3),

        # GRC - Governance, Risk and Compliance
        Control("GRC-01", "Governance Program",
                "Establish and maintain a governance program with policies, processes, and controls to provide assurance that the organization's information security strategies are aligned with and support business objectives.",
                "Governance, Risk and Compliance", 1.3),
        Control("GRC-03", "Cybersecurity Training",
                "Implement a security awareness training program. Ensure all personnel receive training on their security responsibilities. Track completion and update training content regularly.",
                "Governance, Risk and Compliance", 1.1),
        Control("GRC-05", "Intellectual Property",
                "Establish policies and procedures to protect intellectual property rights and ensure proper licensing of software and services used within the organization.",
                "Governance, Risk and Compliance", 1.0),

        # IAM - Identity and Access Management
        Control("IAM-01", "Identity and Access Management Policy",
                "Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for identity and access management. Enforce least-privilege access principles.",
                "Identity and Access Management", 1.4),
        Control("IAM-02", "Strong Authentication",
                "Implement strong authentication mechanisms for all user access, especially privileged access. Enforce multi-factor authentication for cloud service access.",
                "Identity and Access Management", 1.5),
        Control("IAM-05", "Least Privilege",
                "Employ the least privilege principle when implementing information system access controls. Review access rights regularly and revoke unnecessary permissions.",
                "Identity and Access Management", 1.4),
        Control("IAM-08", "User Access Provisioning",
                "Define and implement a user access provisioning process which authorizes, records, and communicates access changes to data and organizationally owned or managed information assets.",
                "Identity and Access Management", 1.3),

        # LOG - Logging and Monitoring
        Control("LOG-01", "Logging and Monitoring Policy",
                "Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for logging and monitoring. Define what events are logged and how logs are managed.",
                "Logging and Monitoring", 1.2),
        Control("LOG-05", "Audit Log Monitoring",
                "Monitor security audit logs to detect activity outside of typical or expected patterns. Establish alerts for suspicious activity and ensure timely response.",
                "Logging and Monitoring", 1.3),
        Control("LOG-08", "Auditability",
                "Identify and document compliance requirements for audit log retention. Ensure audit logs are retained for the required period and protected from unauthorized access.",
                "Logging and Monitoring", 1.2),

        # SEF - Security Incident Management
        Control("SEF-01", "Incident Management Policy",
                "Establish, document, approve, communicate, apply, evaluate and maintain policies and procedures for security incident management. Define roles and responsibilities for incident response.",
                "Security Incident Management", 1.3),
        Control("SEF-03", "Incident Reporting",
                "Establish and follow a defined security incident response plan with appropriate communications to stakeholders and regulatory bodies within required timeframes.",
                "Security Incident Management", 1.3),

        # TVM - Threat and Vulnerability Management
        Control("TVM-01", "Antivirus and Anti-malware",
                "Configure and use antivirus and anti-malware technologies to prevent and detect malware on organizational assets. Keep definitions current and perform regular scans.",
                "Threat and Vulnerability Management", 1.3),
        Control("TVM-02", "Vulnerability Management",
                "Establish and maintain a vulnerability management program to identify, track, and remediate vulnerabilities in organizational systems and applications.",
                "Threat and Vulnerability Management", 1.4),
        Control("TVM-03", "Vulnerability Remediation",
                "Establish and maintain a process for identifying and remediating vulnerabilities based on severity. Patch critical vulnerabilities within defined SLAs.",
                "Threat and Vulnerability Management", 1.4),
    ],
)
