import defusedxml.ElementTree as ET
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional

class NfeLineCandidate(BaseModel):
    raw_code: str
    raw_description: str
    raw_quantity: Decimal
    raw_uom: str
    raw_unit_price: Decimal

class NfeExtractionCandidate(BaseModel):
    supplier_cnpj_candidate: str
    supplier_name_candidate: str
    invoice_number_candidate: str
    issue_date_candidate: datetime
    total_amount_candidate: Decimal
    lines: List[NfeLineCandidate]

class NFeParser:
    """
    Parser for Brazilian NFe XML documents.
    This parses the standard XML format to extract Candidates.
    """
    
    @classmethod
    def parse_xml_string(cls, xml_content: str) -> NfeExtractionCandidate:
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            raise ValueError(f"Invalid XML document: {e}")
            
        if "nfeProc" not in xml_content and "NFe" not in xml_content:
            raise ValueError("Not a valid NFe XML")
            
        # NFe uses namespaces, we need to handle them or strip them.
        # For simplicity in MVP, we can find elements by ignoring namespaces with local-name()
        # or just matching tags ending with the specific name
        
        def find_text(element, tag_name: str) -> Optional[str]:
            for child in element.iter():
                if child.tag.endswith(tag_name):
                    return child.text
            return None
        
        # Header data
        cnpj = find_text(root, "CNPJ")
        if not cnpj:
            raise ValueError("Missing CNPJ")
        
        name = find_text(root, "xNome") or "Unknown Supplier"
        nNF = find_text(root, "nNF")
        if not nNF:
            raise ValueError("Missing nNF")
            
        dhEmi = find_text(root, "dhEmi")
        if dhEmi:
            try:
                # Handle isoformat
                dhEmi_dt = datetime.fromisoformat(dhEmi)
            except ValueError:
                dhEmi_dt = datetime.utcnow()
        else:
            dhEmi_dt = datetime.utcnow()
            
        vNF = find_text(root, "vNF")
        total_amount = Decimal(vNF) if vNF else Decimal("0.0")
        
        lines = []
        for det in root.iter():
            if det.tag.endswith("det"):
                # det contains prod
                prod = next((c for c in det.iter() if c.tag.endswith("prod")), None)
                if prod is not None:
                    cProd = find_text(prod, "cProd") or ""
                    xProd = find_text(prod, "xProd") or ""
                    qCom = find_text(prod, "qCom") or "0.0"
                    uCom = find_text(prod, "uCom") or "UN"
                    vUnCom = find_text(prod, "vUnCom") or "0.0"
                    
                    lines.append(NfeLineCandidate(
                        raw_code=cProd,
                        raw_description=xProd,
                        raw_quantity=Decimal(qCom),
                        raw_uom=uCom,
                        raw_unit_price=Decimal(vUnCom)
                    ))
                    
        return NfeExtractionCandidate(
            supplier_cnpj_candidate=cnpj,
            supplier_name_candidate=name,
            invoice_number_candidate=nNF,
            issue_date_candidate=dhEmi_dt,
            total_amount_candidate=total_amount,
            lines=lines
        )
