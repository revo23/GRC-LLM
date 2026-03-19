from app.models.control import Control, FrameworkDefinition

FRAMEWORK = FrameworkDefinition(
    id="nist_800_53",
    name="NIST SP 800-53",
    version="Rev 5",
    family_weights={
        "Access Control": 1.5,
        "Awareness and Training": 1.0,
        "Audit and Accountability": 1.3,
        "Security Assessment": 1.2,
        "Configuration Management": 1.3,
        "Identification and Authentication": 1.5,
        "Incident Response": 1.3,
        "Risk Assessment": 1.2,
        "System and Communications Protection": 1.4,
        "System and Information Integrity": 1.4,
    },
    controls=[
        # Access Control (AC)
        Control("AC-1", "Access Control Policy and Procedures",
                "The organization develops, documents, and disseminates an access control policy that addresses purpose, scope, roles, responsibilities, and compliance; and procedures to facilitate implementation.",
                "Access Control", 1.2),
        Control("AC-2", "Account Management",
                "The organization manages information system accounts including establishing account types, conditions for group membership, account authorization, and reviews of accounts for compliance.",
                "Access Control", 1.5),
        Control("AC-3", "Access Enforcement",
                "The information system enforces approved authorizations for logical access to information and system resources in accordance with applicable access control policies.",
                "Access Control", 1.5),
        Control("AC-17", "Remote Access",
                "The organization establishes and documents usage restrictions, configuration/connection requirements, and implementation guidance for remote access; authorizes remote access prior to allowing connections.",
                "Access Control", 1.3),

        # Awareness and Training (AT)
        Control("AT-1", "Security Awareness and Training Policy",
                "The organization develops, documents, and disseminates a security awareness and training policy and procedures to facilitate implementation.",
                "Awareness and Training", 1.0),
        Control("AT-2", "Security Awareness Training",
                "The organization provides basic security awareness training as part of initial training for new users and when required by changes; updates awareness training content annually.",
                "Awareness and Training", 1.2),
        Control("AT-3", "Role-Based Security Training",
                "The organization provides role-based security training to personnel with assigned security roles and responsibilities before authorization and when required.",
                "Awareness and Training", 1.0),

        # Audit and Accountability (AU)
        Control("AU-2", "Audit Events",
                "The organization determines that the information system is capable of auditing defined events, coordinates the audit function, and provides rationale for events not deemed auditable.",
                "Audit and Accountability", 1.3),
        Control("AU-9", "Protection of Audit Information",
                "The information system protects audit information and tools from unauthorized access, modification, and deletion through access controls and integrity verification.",
                "Audit and Accountability", 1.3),
        Control("AU-12", "Audit Record Generation",
                "The information system generates audit records for defined auditable events, allows authorized personnel to select auditable events, and generates audit records at defined locations.",
                "Audit and Accountability", 1.2),

        # Security Assessment and Authorization (CA)
        Control("CA-2", "Security Assessments",
                "The organization develops and implements a security assessment plan, assesses security controls at defined frequencies, produces assessment reports, and provides results to authorized officials.",
                "Security Assessment", 1.2),
        Control("CA-7", "Continuous Monitoring",
                "The organization develops a continuous monitoring strategy and implements a program that includes ongoing assessment of security controls, ongoing security status reporting, and configuration management.",
                "Security Assessment", 1.3),

        # Configuration Management (CM)
        Control("CM-2", "Baseline Configuration",
                "The organization develops, documents, and maintains a current baseline configuration of the information system under configuration control; reviews and updates the baseline at defined frequencies.",
                "Configuration Management", 1.3),
        Control("CM-6", "Configuration Settings",
                "The organization establishes and documents configuration settings for information technology products employed within the system that reflect the most restrictive mode consistent with operational requirements.",
                "Configuration Management", 1.2),
        Control("CM-8", "Information System Component Inventory",
                "The organization develops and documents an inventory of information system components that accurately reflects the system, includes defined information, and is consistent with the authorization boundary.",
                "Configuration Management", 1.0),

        # Identification and Authentication (IA)
        Control("IA-2", "Identification and Authentication (Organizational Users)",
                "The information system uniquely identifies and authenticates organizational users including processes acting on behalf of users, and implements multi-factor authentication for network access to privileged accounts.",
                "Identification and Authentication", 1.5),
        Control("IA-5", "Authenticator Management",
                "The organization manages information system authenticators including passwords, tokens, and certificates by verifying identity, establishing initial authenticator content, and enforcing restrictions.",
                "Identification and Authentication", 1.3),
        Control("IA-8", "Identification and Authentication (Non-Organizational Users)",
                "The information system uniquely identifies and authenticates non-organizational users or processes acting on behalf of non-organizational users.",
                "Identification and Authentication", 1.2),

        # Incident Response (IR)
        Control("IR-1", "Incident Response Policy and Procedures",
                "The organization develops, documents, and disseminates an incident response policy and procedures that addresses purpose, scope, roles, responsibilities, and compliance.",
                "Incident Response", 1.2),
        Control("IR-4", "Incident Handling",
                "The organization implements an incident handling capability including preparation, detection, analysis, containment, eradication, and recovery; coordinates with contingency planning activities.",
                "Incident Response", 1.5),
        Control("IR-6", "Incident Reporting",
                "The organization requires personnel to report suspected security incidents to organizational incident response capability and reports incident information to defined authorities.",
                "Incident Response", 1.2),

        # Risk Assessment (RA)
        Control("RA-3", "Risk Assessment",
                "The organization conducts risk assessments that include the likelihood and magnitude of harm from unauthorized access, use, disclosure, disruption, modification, and destruction; documents results; and updates at defined frequencies.",
                "Risk Assessment", 1.3),
        Control("RA-5", "Vulnerability Scanning",
                "The organization scans for vulnerabilities in organizational systems at defined frequencies, employs vulnerability scanning tools, analyzes reports, remediates legitimate vulnerabilities, and shares information.",
                "Risk Assessment", 1.3),

        # System and Communications Protection (SC)
        Control("SC-7", "Boundary Protection",
                "The information system monitors and controls communications at external boundaries and key internal boundaries; implements subnetworks for publicly accessible components; and connects to external networks only through managed interfaces.",
                "System and Communications Protection", 1.5),
        Control("SC-28", "Protection of Information at Rest",
                "The information system protects the confidentiality and integrity of information at rest through encryption and access controls.",
                "System and Communications Protection", 1.4),

        # System and Information Integrity (SI)
        Control("SI-2", "Flaw Remediation",
                "The organization identifies, reports, and corrects information system flaws; tests software updates related to flaw remediation; and incorporates flaw remediation into configuration management.",
                "System and Information Integrity", 1.3),
        Control("SI-3", "Malicious Code Protection",
                "The organization employs malicious code protection mechanisms at entry and exit points to detect and eradicate malicious code, with automated updates and centralized management.",
                "System and Information Integrity", 1.4),
    ],
)
