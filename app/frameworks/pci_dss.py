from app.models.control import Control, FrameworkDefinition

FRAMEWORK = FrameworkDefinition(
    id="pci_dss",
    name="PCI DSS",
    version="4.0",
    family_weights={
        "Network Security": 1.5,
        "Cardholder Data Protection": 1.5,
        "Vulnerability Management": 1.3,
        "Access Control": 1.4,
        "Monitoring and Testing": 1.3,
        "Information Security Policy": 1.2,
    },
    controls=[
        # Requirement 1: Network Security Controls
        Control("PCI-1.1", "Network Security Controls: Processes and Mechanisms",
                "Processes and mechanisms for installing and maintaining network security controls are defined and understood. Network security control configurations are reviewed at least once every 12 months.",
                "Network Security", 1.5),
        Control("PCI-1.2", "Network Security Controls Configuration",
                "Network security controls are configured and maintained to restrict inbound and outbound traffic to only that which is necessary. All other traffic is denied.",
                "Network Security", 1.5),
        Control("PCI-1.3", "Network Access to the Cardholder Data Environment",
                "Network access to and from the cardholder data environment is restricted. Direct public access between the internet and any component in the cardholder data environment is prohibited.",
                "Network Security", 1.5),

        # Requirement 2: Secure Configurations
        Control("PCI-2.1", "Default Passwords and Security Parameters",
                "Processes and mechanisms for applying secure configurations are defined and understood. All vendor-supplied defaults are changed. Unnecessary default accounts are removed or disabled.",
                "Network Security", 1.4),
        Control("PCI-2.2", "System Components Configured and Managed Securely",
                "System components are configured and managed securely. Configuration standards are developed and implemented for all system components.",
                "Network Security", 1.3),

        # Requirement 3: Protect Stored Account Data
        Control("PCI-3.1", "Stored Account Data is Kept to Minimum",
                "Processes and mechanisms for protecting stored account data are defined and understood. Policies for retention of cardholder data are implemented.",
                "Cardholder Data Protection", 1.5),
        Control("PCI-3.4", "Access to Cardholder Data is Restricted",
                "Access to stored account data is restricted based on business need to know. Primary account numbers (PAN) are rendered unreadable anywhere they are stored.",
                "Cardholder Data Protection", 1.5),
        Control("PCI-3.5", "Primary Account Number (PAN) Security",
                "The primary account number (PAN) is secured wherever it is stored. Strong cryptography is used to render the PAN unreadable.",
                "Cardholder Data Protection", 1.5),

        # Requirement 4: Protect Cardholder Data with Strong Cryptography
        Control("PCI-4.1", "Strong Cryptography During Transmission",
                "Processes and mechanisms for protecting cardholder data with strong cryptography during transmission over open, public networks are defined and understood.",
                "Cardholder Data Protection", 1.5),
        Control("PCI-4.2", "PAN Secured During Transmission",
                "PANs are protected with strong cryptography during transmission. Only trusted keys/certificates are accepted. The protocol in use only supports secure versions and configurations.",
                "Cardholder Data Protection", 1.4),

        # Requirement 5: Protect All Systems Against Malware
        Control("PCI-5.1", "Anti-malware Processes",
                "Processes and mechanisms to protect all systems against malware are defined and understood. An anti-malware solution is deployed on all components except those documented as not at risk.",
                "Vulnerability Management", 1.3),
        Control("PCI-5.3", "Anti-malware Mechanisms Active and Maintained",
                "Anti-malware mechanisms and processes are active, maintained, and monitored. Anti-malware solutions are updated regularly and scans are performed.",
                "Vulnerability Management", 1.3),

        # Requirement 6: Develop and Maintain Secure Systems
        Control("PCI-6.2", "Bespoke and Custom Software Developed Securely",
                "Bespoke and custom software are developed securely. Software development practices follow secure coding guidelines addressing OWASP Top 10 vulnerabilities.",
                "Vulnerability Management", 1.3),
        Control("PCI-6.3", "Security Vulnerabilities Identified and Addressed",
                "Security vulnerabilities are identified and addressed. Vulnerability management processes are defined. Critical patches are installed within 30 days.",
                "Vulnerability Management", 1.4),

        # Requirement 7: Restrict Access by Business Need
        Control("PCI-7.1", "Access Control Processes",
                "Processes and mechanisms for restricting access to system components and cardholder data by business need to know are defined and understood.",
                "Access Control", 1.4),
        Control("PCI-7.2", "Access to System Components and Data",
                "Access to system components and data is appropriately defined and assigned. All access must be authorized and based on least-privilege principles.",
                "Access Control", 1.4),

        # Requirement 8: Identify Users and Authenticate Access
        Control("PCI-8.2", "User Identification and Authentication",
                "User identification and related accounts for users and administrators are strictly managed throughout an account's lifecycle. Unique IDs are assigned to all users.",
                "Access Control", 1.5),
        Control("PCI-8.4", "Multi-Factor Authentication (MFA)",
                "Multi-factor authentication (MFA) is implemented to secure access into the cardholder data environment for all non-console administrative access and all remote network access.",
                "Access Control", 1.5),

        # Requirement 10: Log and Monitor All Access
        Control("PCI-10.2", "Audit Logs Capture User Activities",
                "Audit logs are implemented to support the detection of anomalies and suspicious activity, and the forensic analysis of events. All individual user access to cardholder data is logged.",
                "Monitoring and Testing", 1.4),
        Control("PCI-10.6", "Time Synchronization Mechanisms",
                "Time synchronization technology is in use and current. Systems use consistent and correct time. Time data is protected to prevent unauthorized modification.",
                "Monitoring and Testing", 1.2),
        Control("PCI-10.7", "Failures Detected and Reported",
                "Failures of critical security controls are detected, reported, and responded to promptly. Log management tools are used to facilitate log reviews.",
                "Monitoring and Testing", 1.3),

        # Requirement 12: Support Information Security with Organizational Policies
        Control("PCI-12.1", "Comprehensive Information Security Policy",
                "A comprehensive information security policy is known and current. The information security policy is reviewed at least once every 12 months and updated as needed.",
                "Information Security Policy", 1.2),
        Control("PCI-12.3", "Risks Identified, Evaluated, and Managed",
                "Risks to the cardholder data environment are identified, evaluated, and managed. Formal risk assessment processes are documented and performed at least annually.",
                "Information Security Policy", 1.3),
    ],
)
