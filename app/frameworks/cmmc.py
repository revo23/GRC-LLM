from app.models.control import Control, FrameworkDefinition

FRAMEWORK = FrameworkDefinition(
    id="cmmc",
    name="Cybersecurity Maturity Model Certification",
    version="2.0",
    family_weights={
        "Access Control": 1.5,
        "Awareness and Training": 1.0,
        "Audit and Accountability": 1.2,
        "Configuration Management": 1.3,
        "Identification and Authentication": 1.5,
        "Incident Response": 1.3,
        "Maintenance": 1.0,
        "Media Protection": 1.1,
        "Personnel Security": 1.0,
        "Physical Protection": 1.1,
        "Risk Assessment": 1.2,
        "Security Assessment": 1.1,
        "System and Communications Protection": 1.4,
        "System and Information Integrity": 1.4,
    },
    controls=[
        # Access Control
        Control("AC.L1-3.1.1", "Authorized Access Control",
                "Limit information system access to authorized users, processes acting on behalf of authorized users, or devices (including other information systems) and to the types of transactions and functions that authorized users are permitted to exercise.",
                "Access Control", 1.5),
        Control("AC.L2-3.1.3", "Control CUI Flow",
                "Control the flow of CUI in accordance with approved authorizations. Enforce information flow control using security policy filters and protected processing domains.",
                "Access Control", 1.3),
        Control("AC.L2-3.1.5", "Least Privilege",
                "Employ the principle of least privilege, including for specific security functions and privileged accounts. Authorize access only to privileged accounts and roles required to accomplish assigned duties.",
                "Access Control", 1.4),
        Control("AC.L2-3.1.12", "Control Remote Access",
                "Monitor and control remote access sessions. Employ cryptographic mechanisms to protect the confidentiality of remote access sessions.",
                "Access Control", 1.3),

        # Audit and Accountability
        Control("AU.L2-3.3.1", "System Auditing",
                "Create and retain system audit logs and records to the extent needed to enable the monitoring, analysis, investigation, and reporting of unlawful or unauthorized system activity.",
                "Audit and Accountability", 1.2),
        Control("AU.L2-3.3.2", "User Accountability",
                "Ensure that the actions of individual system users can be traced to those users so they can be held accountable for their actions.",
                "Audit and Accountability", 1.2),

        # Configuration Management
        Control("CM.L2-3.4.1", "System Baselining",
                "Establish and maintain baseline configurations and inventories of organizational systems (including hardware, software, firmware, and documentation) throughout the respective system development life cycles.",
                "Configuration Management", 1.3),
        Control("CM.L2-3.4.2", "Security Configuration Enforcement",
                "Establish and enforce security configuration settings for information technology products employed in organizational systems.",
                "Configuration Management", 1.3),

        # Identification and Authentication
        Control("IA.L1-3.5.1", "Identification",
                "Identify information system users, processes acting on behalf of users, or devices. Maintain user identification information and use it for authentication.",
                "Identification and Authentication", 1.4),
        Control("IA.L2-3.5.3", "Multifactor Authentication",
                "Use multifactor authentication for local and network access to privileged accounts and for network access to non-privileged accounts.",
                "Identification and Authentication", 1.5),
        Control("IA.L2-3.5.7", "Password Complexity",
                "Enforce a minimum password complexity and change of characters when new passwords are created. Employ automated tools to ensure password strength.",
                "Identification and Authentication", 1.2),

        # Incident Response
        Control("IR.L2-3.6.1", "Incident Handling",
                "Establish an operational incident-handling capability for organizational systems that includes preparation, detection, analysis, containment, recovery, and user response activities.",
                "Incident Response", 1.3),
        Control("IR.L2-3.6.2", "Incident Reporting",
                "Track, document, and report incidents to designated officials and/or authorities both internal and external to the organization.",
                "Incident Response", 1.2),

        # Risk Assessment
        Control("RA.L2-3.11.1", "Risk Assessments",
                "Periodically assess the risk to organizational operations, assets, and individuals resulting from the operation of organizational systems and the associated processing, storage, or transmission of CUI.",
                "Risk Assessment", 1.2),
        Control("RA.L2-3.11.2", "Vulnerability Scan",
                "Scan for vulnerabilities in organizational systems and applications periodically and when new vulnerabilities affecting those systems are identified.",
                "Risk Assessment", 1.3),

        # System and Communications Protection
        Control("SC.L1-3.13.1", "Boundary Protection",
                "Monitor, control, and protect organizational communications (i.e., information transmitted or received by organizational systems) at the external boundaries and key internal boundaries.",
                "System and Communications Protection", 1.4),
        Control("SC.L2-3.13.10", "Cryptographic Key Management",
                "Establish and manage cryptographic keys for required cryptography employed in organizational systems. Protect cryptographic keys at all times.",
                "System and Communications Protection", 1.3),

        # System and Information Integrity
        Control("SI.L1-3.14.1", "Flaw Remediation",
                "Identify, report, and correct information and information system flaws in a timely manner. Test software and firmware updates related to flaw remediation for effectiveness.",
                "System and Information Integrity", 1.3),
        Control("SI.L1-3.14.2", "Malicious Code Protection",
                "Provide protection from malicious code at appropriate locations within organizational information systems. Update malicious code protection mechanisms when new releases are available.",
                "System and Information Integrity", 1.4),
        Control("SI.L2-3.14.6", "Security Alert Monitoring",
                "Monitor organizational systems, including inbound and outbound communications traffic, to detect attacks and indicators of potential attacks.",
                "System and Information Integrity", 1.3),
    ],
)
