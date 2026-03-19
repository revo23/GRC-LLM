from app.models.control import Control, FrameworkDefinition

FRAMEWORK = FrameworkDefinition(
    id="iso_27001",
    name="ISO/IEC 27001",
    version="2022",
    family_weights={
        "Information Security Policies": 1.2,
        "Organization of Information Security": 1.1,
        "Human Resource Security": 1.0,
        "Asset Management": 1.2,
        "Access Control": 1.5,
        "Cryptography": 1.3,
        "Physical and Environmental Security": 1.2,
        "Operations Security": 1.3,
        "Communications Security": 1.3,
        "Supplier Relationships": 1.0,
        "Information Security Incident Management": 1.3,
        "Business Continuity Management": 1.2,
        "Compliance": 1.1,
    },
    controls=[
        # A.5 Information Security Policies
        Control("A.5.1", "Policies for Information Security",
                "A set of policies for information security shall be defined, approved by management, published and communicated to employees and relevant external parties.",
                "Information Security Policies", 1.2),

        # A.6 Organization of Information Security
        Control("A.6.1", "Internal Organization",
                "All information security responsibilities shall be defined and allocated. Segregation of duties shall be implemented where appropriate. Contact with authorities and special interest groups shall be maintained.",
                "Organization of Information Security", 1.1),
        Control("A.6.2", "Mobile Devices and Teleworking",
                "A policy and supporting security measures shall be adopted to manage risks introduced by using mobile devices and teleworking.",
                "Organization of Information Security", 1.0),

        # A.7 Human Resource Security
        Control("A.7.1", "Prior to Employment",
                "Background verification checks on all candidates for employment shall be carried out in accordance with relevant laws, regulations and ethics.",
                "Human Resource Security", 1.0),
        Control("A.7.2", "During Employment",
                "Management shall require all employees and contractors to apply information security in accordance with the established policies and procedures.",
                "Human Resource Security", 1.0),
        Control("A.7.3", "Termination and Change of Employment",
                "Information security responsibilities and duties that remain valid after termination or change of employment shall be defined, communicated and enforced.",
                "Human Resource Security", 1.0),

        # A.8 Asset Management
        Control("A.8.1", "Responsibility for Assets",
                "Assets associated with information and information processing facilities shall be identified and an inventory of these assets shall be drawn up and maintained.",
                "Asset Management", 1.2),
        Control("A.8.2", "Information Classification",
                "Information shall be classified in terms of legal requirements, value, criticality and sensitivity to unauthorised disclosure or modification.",
                "Asset Management", 1.2),
        Control("A.8.3", "Media Handling",
                "Procedures for the management of removable media shall be implemented in accordance with the classification scheme adopted by the organization.",
                "Asset Management", 1.0),

        # A.9 Access Control
        Control("A.9.1", "Business Requirements of Access Control",
                "An access control policy shall be established, documented and reviewed based on business and information security requirements.",
                "Access Control", 1.5),
        Control("A.9.2", "User Access Management",
                "A formal user registration and de-registration process shall be implemented to enable assignment of access rights. Privileged access rights shall be restricted and controlled.",
                "Access Control", 1.5),
        Control("A.9.4", "System and Application Access Control",
                "Access to systems and applications shall be controlled by a secure log-on procedure. Password management systems shall be interactive and shall ensure quality passwords.",
                "Access Control", 1.3),

        # A.10 Cryptography
        Control("A.10.1", "Cryptographic Controls",
                "A policy on the use of cryptographic controls for protection of information shall be developed and implemented. A policy on the use, protection and lifetime of cryptographic keys shall be developed.",
                "Cryptography", 1.3),

        # A.11 Physical and Environmental Security
        Control("A.11.1", "Secure Areas",
                "Security perimeters shall be defined and used to protect areas that contain either sensitive or critical information and information processing facilities.",
                "Physical and Environmental Security", 1.2),
        Control("A.11.2", "Equipment Security",
                "Equipment shall be sited and protected to reduce the risks from environmental threats and hazards, and opportunities for unauthorized access.",
                "Physical and Environmental Security", 1.1),

        # A.12 Operations Security
        Control("A.12.1", "Operational Procedures and Responsibilities",
                "Operating procedures shall be documented and made available to all users who need them. Changes to systems shall be controlled.",
                "Operations Security", 1.2),
        Control("A.12.6", "Technical Vulnerability Management",
                "Information about technical vulnerabilities of information systems being used shall be obtained in a timely fashion, the organization's exposure to such vulnerabilities evaluated and appropriate measures taken.",
                "Operations Security", 1.3),

        # A.13 Communications Security
        Control("A.13.1", "Network Security Management",
                "Networks shall be managed and controlled to protect information in systems and applications. Security mechanisms, service levels and management requirements shall be identified.",
                "Communications Security", 1.3),
        Control("A.13.2", "Information Transfer",
                "Formal transfer policies, procedures and controls shall be in place to protect the transfer of information through the use of all types of communication facilities.",
                "Communications Security", 1.2),

        # A.15 Supplier Relationships
        Control("A.15.1", "Information Security in Supplier Relationships",
                "Information security requirements for mitigating risks associated with supplier's access to the organization's assets shall be agreed with the supplier and documented.",
                "Supplier Relationships", 1.0),

        # A.16 Incident Management
        Control("A.16.1", "Management of Information Security Incidents",
                "Responsibilities and procedures shall be established to ensure a quick, effective and orderly response to information security incidents.",
                "Information Security Incident Management", 1.3),

        # A.17 Business Continuity
        Control("A.17.1", "Information Security Continuity",
                "The organization shall determine its requirements for information security and the continuity of information security management in adverse situations.",
                "Business Continuity Management", 1.2),

        # A.18 Compliance
        Control("A.18.1", "Compliance with Legal and Contractual Requirements",
                "All relevant legislative, regulatory and contractual requirements and the organization's approach to meet these requirements shall be explicitly identified, documented and kept up to date.",
                "Compliance", 1.1),
        Control("A.18.2", "Information Security Reviews",
                "The organization's approach to managing information security and its implementation shall be reviewed independently at planned intervals.",
                "Compliance", 1.1),
    ],
)
