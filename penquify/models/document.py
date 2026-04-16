"""Document data models — header + body for each logistics document type."""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import date


@dataclass
class DocItem:
    """Single line item in a logistics document."""
    pos: int
    code: str
    description: str
    qty: float
    unit: str
    unit_price: float = 0
    total: float = 0
    batch: str = ""
    # OC/SAP reference (for cross-document linking)
    sap_material: str = ""
    sap_qty: float = 0
    sap_unit: str = ""


@dataclass
class DocHeader:
    """Common header fields for any logistics document."""
    doc_type: str  # guia_despacho, factura, purchase_order, bill_of_lading
    doc_number: str
    date: str  # YYYY-MM-DD or DD/MM/YYYY for display

    # Emitter
    emitter_name: str = ""
    emitter_rut: str = ""
    emitter_giro: str = ""
    emitter_address: str = ""
    emitter_phone: str = ""
    emitter_email: str = ""

    # Receiver
    receiver_name: str = ""
    receiver_rut: str = ""
    receiver_giro: str = ""
    receiver_address: str = ""
    receiver_contact: str = ""

    # References
    oc_number: str = ""
    oc_date: str = ""
    payment_terms: str = ""
    solpe_number: str = ""

    # Dispatch (guia specific)
    dispatch_date: str = ""
    vehicle_plate: str = ""
    driver_name: str = ""
    driver_rut: str = ""
    transport_type: str = "Venta"
    temperature: str = ""

    # SII (Chile tax authority)
    sii_office: str = ""
    sii_resolution: str = ""

    # Receiver sign-off
    received_by: str = ""
    received_rut: str = ""
    received_date: str = ""


@dataclass
class Document:
    """Complete document = header + items + computed totals."""
    header: DocHeader
    items: List[DocItem] = field(default_factory=list)

    # Observations (handwritten notes, simulated)
    observations: str = ""

    @property
    def subtotal(self) -> float:
        return sum(it.total or (it.qty * it.unit_price) for it in self.items)

    @property
    def iva(self) -> float:
        return round(self.subtotal * 0.19)

    @property
    def total(self) -> float:
        return self.subtotal + self.iva

    def to_dict(self):
        """Serialize for template rendering."""
        return {
            "header": self.header.__dict__,
            "items": [it.__dict__ for it in self.items],
            "observations": self.observations,
            "subtotal": self.subtotal,
            "iva": self.iva,
            "total": self.total,
        }
