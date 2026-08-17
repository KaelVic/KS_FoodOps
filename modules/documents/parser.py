import defusedxml.ElementTree as ET
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import re


NFE_NAMESPACE = "http://www.portalfiscal.inf.br/nfe"


def _strip_namespace(tag: str) -> str:
    """Remove namespace prefix from XML tag."""
    if tag.startswith("{"):
        return tag.split("}", 1)[1]
    return tag


def _find_text(element: ET.Element, ns: str, *paths: str) -> Optional[str]:
    """Try multiple paths with namespace and return first non-None text."""
    for path in paths:
        elem = element.find(f"{ns}{path}")
        if elem is not None and elem.text:
            return elem.text.strip()
    return None


def _parse_datetime(value: str) -> datetime:
    """Parse NFe datetime formats (dhEmi: 2024-01-15T10:30:00-03:00, dEmi: 2024-01-15)."""
    value = value.strip()
    if "T" in value:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def _parse_decimal(value: str) -> str:
    """Normalize decimal string (replace comma with dot)."""
    return value.strip().replace(",", ".")


def parse_nfe_xml(xml_content: str) -> Dict[str, Any]:
    """
    Parse SEFAZ NFe XML v4.00 and extract structured data.
    
    Handles namespaces automatically (with or without http://www.portalfiscal.inf.br/nfe).
    
    Returns dict with:
    - invoice_number (str): from ide/nNF
    - issue_date (datetime): from ide/dhEmi or ide/dEmi
    - total_amount (str): from total/ICMSTot/vNF
    - supplier_cnpj (str): from emit/CNPJ or emit/CPF
    - supplier_name (str): from emit/xNome
    - lines (List[Dict]): list of product lines with raw_code, raw_description, raw_quantity, raw_uom, raw_unit_price
    
    Raises:
        ValueError: If XML is invalid or required fields are missing
    """
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML: {e}")

    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"
    
    def find_with_ns(path: str) -> Optional[ET.Element]:
        return root.find(f".//{ns}{path}") if ns else root.find(f".//{path}")
    
    def find_all_with_ns(path: str) -> List[ET.Element]:
        return root.findall(f".//{ns}{path}") if ns else root.findall(f".//{path}")

    def find_in_elem_ns(elem: ET.Element, path: str) -> Optional[ET.Element]:
        return elem.find(f"{ns}{path}") if ns else elem.find(path)

    def find_all_in_elem_ns(elem: ET.Element, path: str) -> List[ET.Element]:
        return elem.findall(f"{ns}{path}") if ns else elem.findall(path)

    nfe_elem = find_with_ns("NFe")
    nfe = nfe_elem if nfe_elem is not None else root
    inf_nfe_elem = find_with_ns("infNFe")
    inf_nfe = inf_nfe_elem if inf_nfe_elem is not None else nfe
    
    ide = find_in_elem_ns(inf_nfe, "ide")
    if ide is None:
        raise ValueError("Missing required <ide> tag in NFe XML")

    invoice_number = _find_text(ide, ns, "nNF")
    if not invoice_number:
        raise ValueError("Missing invoice number (ide/nNF)")

    issue_date_str = _find_text(ide, ns, "dhEmi", "dEmi")
    if not issue_date_str:
        raise ValueError("Missing issue date (ide/dhEmi or ide/dEmi)")
    issue_date = _parse_datetime(issue_date_str)

    emit = find_in_elem_ns(inf_nfe, "emit")
    if emit is None:
        raise ValueError("Missing required <emit> tag in NFe XML")

    supplier_cnpj = _find_text(emit, ns, "CNPJ", "CPF")
    if not supplier_cnpj:
        raise ValueError("Missing supplier CNPJ/CPF (emit/CNPJ or emit/CPF)")
    supplier_cnpj = re.sub(r"\D", "", supplier_cnpj)

    supplier_name = _find_text(emit, ns, "xNome")
    if not supplier_name:
        raise ValueError("Missing supplier name (emit/xNome)")

    total_elem = find_in_elem_ns(inf_nfe, "total")
    if total_elem is None:
        raise ValueError("Missing required <total> tag in NFe XML")
    
    icms_tot = find_in_elem_ns(total_elem, "ICMSTot")
    if icms_tot is None:
        raise ValueError("Missing <ICMSTot> inside <total>")
    
    total_amount = _find_text(icms_tot, ns, "vNF")
    if not total_amount:
        raise ValueError("Missing total amount (total/ICMSTot/vNF)")
    total_amount = _parse_decimal(total_amount)

    det_elements = find_all_in_elem_ns(inf_nfe, "det")
    if not det_elements:
        raise ValueError("No product lines found (<det> tags)")

    lines = []
    for det in det_elements:
        prod = find_in_elem_ns(det, "prod")
        if prod is None:
            continue

        raw_code = _find_text(prod, ns, "cProd")
        raw_description = _find_text(prod, ns, "xProd")
        raw_quantity = _find_text(prod, ns, "qCom")
        raw_uom = _find_text(prod, ns, "uCom")
        raw_unit_price = _find_text(prod, ns, "vUnCom")

        if not all([raw_code, raw_description, raw_quantity, raw_uom, raw_unit_price]):
            continue

        lines.append({
            "raw_code": raw_code.strip(),
            "raw_description": raw_description.strip(),
            "raw_quantity": _parse_decimal(raw_quantity),
            "raw_uom": raw_uom.strip(),
            "raw_unit_price": _parse_decimal(raw_unit_price),
        })

    if not lines:
        raise ValueError("No valid product lines extracted from <det>/<prod> tags")

    return {
        "invoice_number": invoice_number,
        "issue_date": issue_date,
        "total_amount": total_amount,
        "supplier_cnpj": supplier_cnpj,
        "supplier_name": supplier_name,
        "lines": lines,
    }