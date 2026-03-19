from app.frameworks.nist_csf import FRAMEWORK as NIST_CSF
from app.frameworks.nist_800_53 import FRAMEWORK as NIST_800_53
from app.frameworks.iso_27001 import FRAMEWORK as ISO_27001
from app.frameworks.cis_csc import FRAMEWORK as CIS_CSC
from app.frameworks.cmmc import FRAMEWORK as CMMC
from app.frameworks.hipaa import FRAMEWORK as HIPAA
from app.frameworks.pci_dss import FRAMEWORK as PCI_DSS
from app.frameworks.csa_ccm import FRAMEWORK as CSA_CCM
from app.frameworks.ftc_safeguards import FRAMEWORK as FTC_SAFEGUARDS

FRAMEWORK_REGISTRY: dict = {
    NIST_CSF.id: NIST_CSF,
    NIST_800_53.id: NIST_800_53,
    ISO_27001.id: ISO_27001,
    CIS_CSC.id: CIS_CSC,
    CMMC.id: CMMC,
    HIPAA.id: HIPAA,
    PCI_DSS.id: PCI_DSS,
    CSA_CCM.id: CSA_CCM,
    FTC_SAFEGUARDS.id: FTC_SAFEGUARDS,
}

__all__ = ["FRAMEWORK_REGISTRY"]
