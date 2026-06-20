import re
import unicodedata
from datetime import datetime
from pathlib import Path

import pdfplumber
from loguru import logger


NOTES_DIR = Path(__file__).resolve().parent.parent / "notes"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def extract_text_from_pdf(filepath: Path) -> str:
    pages = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
    return "\n\n".join(pages)


MONTHS_SP = r"(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)"

INVALID_AUTHOR_TERMS = (
    "apuntes",
    "inteligencia artificial",
    "inteligencia artifical",
    "ic-6200",
    "ic6200",
    "instituto",
    "escuela",
    "tecnol",
    "cartago",
    "costa rica",
    "profesor",
    "curso",
    "fecha",
    "resumen",
    "abstract",
    "clase",
    "male female",
)


def _is_valid_author(name: str) -> bool:
    cleaned = name.strip()
    if len(cleaned) < 5 or len(cleaned.split()) < 2:
        return False
    lower = cleaned.lower()
    if any(term in lower for term in INVALID_AUTHOR_TERMS):
        return False
    if re.fullmatch(r"semana\s+\d+", lower):
        return False
    if re.search(r"\d{5,}", cleaned):
        return False
    return True


def _extract_author(text: str) -> str:
    header = unicodedata.normalize("NFC", text[:2500]).replace("´", "")
    patterns = [
        r"\b(?:1st|2nd|3rd)\b\s+"
        r"([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+){1,4})"
        r"(?:\s+Profesor|\s+Escuela|\s+Instituto|\s+Curso|\s+IC-|\n|$)",
        r"[Ss]emana\s+\d+\s+"
        r"([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+){1,4})\s*[-–—]",
        r"([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+){1,4})\s*[-–—]{1,2}\s*\d{7,10}",
        r"([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+){1,3})\s+[a-z0-9]+@estudiantec\.cr",
    ]
    for pattern in patterns:
        match = re.search(pattern, header)
        if match and _is_valid_author(match.group(1)):
            return match.group(1).strip()
    return ""


def extract_semana_from_query(text: str) -> str | None:
    match = re.search(r"(?:semana|week)\s*#?\s*(\d{1,2})\b", text, re.IGNORECASE)
    if match:
        return f"Semana {int(match.group(1))}"
    return None


def _parse_header(text: str) -> dict:
    info = {"autor": "", "profesor": "", "fecha_texto": "", "carnet": "", "curso": ""}

    m = re.search(r"Profesor(?:a)?:\s*(.+?)(?:\n|$)", text)
    if m:
        info["profesor"] = m.group(1).strip()

    m = re.search(r"Curso:\s*(.+?)(?:\n|$)", text)
    if m:
        info["curso"] = m.group(1).strip()

    m = re.search(r"Fecha:\s*(.+?)(?:\n|$)", text)
    if m:
        info["fecha_texto"] = m.group(1).strip()
    else:
        m = re.search(r"(?:Clase\s+)?del?\s+(\d{1,2})\s+de\s+(" + MONTHS_SP + r")\s+de\s+(\d{4})", text, re.IGNORECASE)
        if m:
            info["fecha_texto"] = f"{m.group(1)} de {m.group(2)} de {m.group(3)}"

    m = re.search(r"Carn(?:é|e):?\s*(\d+)", text)
    if m:
        info["carnet"] = m.group(1).strip()

    info["autor"] = _extract_author(text)

    return info


def _parse_filename(filepath: Path) -> dict:
    stem = filepath.stem
    stem = re.sub(r"\.pdf$", "", stem, flags=re.IGNORECASE)
    parts = stem.split("_")
    result = {"semana": "", "fecha_elaboracion": "", "seccion": ""}

    week_num = ""
    date_str = ""
    doc_num = ""

    for i, part in enumerate(parts):
        upper = part.upper()
        if upper == "SEMANA" and i > 0 and parts[i - 1].isdigit():
            week_num = parts[i - 1]
        elif re.match(r"^(19|20)\d{6}$", part):
            date_str = part

    numeric_tokens = [p for p in parts if p.isdigit() and len(p) <= 3]
    if numeric_tokens:
        candidate = numeric_tokens[-1]
        if candidate != week_num and candidate != date_str:
            doc_num = candidate

    if week_num:
        result["semana"] = f"Semana {week_num}"
    if date_str:
        try:
            dt = datetime.strptime(date_str, "%Y%m%d")
            result["fecha_elaboracion"] = dt.date().isoformat()
        except ValueError:
            result["fecha_elaboracion"] = date_str
    if doc_num:
        result["seccion"] = f"Parte {doc_num}"

    return result


def extract_metadata(filepath: Path, text: str | None = None) -> dict:
    metadata = {
        "file_name": filepath.name,
        "semana": "",
        "fecha_elaboracion": "",
        "autor": "",
        "profesor": "",
        "tema_principal": "Inteligencia Artificial",
        "seccion": "",
        "source": "apuntes_curso_ai",
    }

    parsed = _parse_filename(filepath)
    metadata["semana"] = parsed["semana"]
    metadata["fecha_elaboracion"] = parsed["fecha_elaboracion"]
    metadata["seccion"] = parsed["seccion"]

    if text:
        header = _parse_header(text)
        if header["autor"]:
            metadata["autor"] = header["autor"]
        if header["profesor"]:
            metadata["profesor"] = header["profesor"]
        if header["fecha_texto"] and not metadata["fecha_elaboracion"]:
            metadata["fecha_elaboracion"] = header["fecha_texto"]
        if header["carnet"]:
            metadata["carnet"] = header["carnet"]

    return metadata


def clean_problematic_chars(text: str) -> str:
    replacements = {
        "\u0000": "",
        "\ufffd": "",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "--",
        "\u2026": "...",
        "\u2022": "*",
        "\u00b7": "*",
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    return text


def remove_noise(text: str) -> str:
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^\d{1,3}\s*$", stripped):
            continue
        if len(stripped) < 2:
            continue
        if re.match(r"^[\s\-_=*·•]+$", stripped):
            continue
        if re.match(r"^[IVXLCDM]+\.?\s*$", stripped):
            continue
        if re.match(r"^[A-Z]\-[A-Z]\.\s*$", stripped):
            continue
        cleaned.append(stripped)

    text = "\n".join(cleaned)
    text = re.sub(r"(\n)\1{3,}", r"\1\1", text)
    text = re.sub(r"[\-_=]{4,}", "", text)
    text = re.sub(r"(?i)p[aá]g\.?\s*\d+", "", text)
    text = re.sub(r"\f", "", text)
    text = re.sub(r"(?i)tecnol[oó]gico de costa rica", "", text)
    text = re.sub(r"(?i)escuela de ingenier[ií]a en computaci[oó]n", "", text)

    return text.strip()


def preprocess_text(text: str) -> str:
    text = clean_problematic_chars(text)
    text = normalize_text(text)
    text = remove_noise(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def segment_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    sections = re.split(r"\n(?=(?:I{1,3}|IV|V|VI{0,3}|X{1,3})\b\.?\s)", text)
    if len(sections) < 2:
        sections = [text]

    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        sentences = re.split(r"(?<=[.!?])\s+", section)
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            sentence_words = len(sentence.split())
            if sentence_words > chunk_size:
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    chunks.append({"text": chunk_text, "token_estimate": len(chunk_text.split())})
                    current_chunk = []
                    current_length = 0
                words = sentence.split()
                for i in range(0, len(words), chunk_size - overlap):
                    sub_chunk = words[i : i + chunk_size]
                    sub_text = " ".join(sub_chunk)
                    chunks.append({"text": sub_text, "token_estimate": len(sub_text.split())})
            elif current_length + sentence_words > chunk_size:
                chunk_text = " ".join(current_chunk)
                chunks.append({"text": chunk_text, "token_estimate": len(chunk_text.split())})
                if overlap > 0:
                    # El overlap es en PALABRAS, no en oraciones: current_chunk es una
                    # lista de oraciones, así que para tomar las últimas `overlap`
                    # palabras hay que aplanar el chunk recién cerrado a nivel de palabra
                    # (no rebanar current_chunk directamente, que rebanaría oraciones).
                    chunk_words = chunk_text.split()
                    overlap_words = chunk_words[-overlap:] if overlap < len(chunk_words) else chunk_words
                    overlap_text = " ".join(overlap_words)
                    current_chunk = [overlap_text, sentence] if overlap_text else [sentence]
                    current_length = len(overlap_words) + sentence_words
                else:
                    current_chunk = [sentence]
                    current_length = sentence_words
            else:
                current_chunk.append(sentence)
                current_length += sentence_words

        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({"text": chunk_text, "token_estimate": len(chunk_text.split())})

    return chunks


def segment_text_fixed_size(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """Segunda estrategia de segmentación: corte duro cada `chunk_size` palabras
    sobre el texto completo, sin respetar límites de oración ni de sección
    romana (a diferencia de segment_text()). Mismo chunk_size/overlap que la
    estrategia por oraciones para que la única variable sea el criterio de corte.
    """
    words = text.split()
    if not words:
        return []

    step = chunk_size - overlap if chunk_size > overlap else chunk_size
    chunks = []

    for i in range(0, len(words), step):
        chunk_words = words[i : i + chunk_size]
        if not chunk_words:
            break
        chunk_text = " ".join(chunk_words)
        chunks.append({"text": chunk_text, "token_estimate": len(chunk_words)})
        if i + chunk_size >= len(words):
            break

    return chunks


SEGMENTATION_STRATEGIES = {
    "sentences": segment_text,
    "fixed_size": segment_text_fixed_size,
}


def process_document(filepath: Path, strategy: str = "sentences") -> list[dict]:
    logger.info(f"Processing: {filepath.name} (strategy={strategy})")

    raw_text = extract_text_from_pdf(filepath)
    logger.info(f"  Extracted {len(raw_text)} chars")

    metadata = extract_metadata(filepath, raw_text)

    cleaned_text = preprocess_text(raw_text)
    logger.info(f"  After preprocessing: {len(cleaned_text)} chars")

    segmenter = SEGMENTATION_STRATEGIES[strategy]
    segments = segmenter(cleaned_text)
    logger.info(f"  Segmented into {len(segments)} chunks")

    documents = []
    for idx, segment in enumerate(segments):
        doc = {
            "id": f"{filepath.stem}_{strategy}_chunk_{idx:04d}",
            "text": segment["text"],
            "token_estimate": segment["token_estimate"],
            "metadata": {
                **metadata,
                "chunk_index": idx,
                "total_chunks": len(segments),
                "chunk_strategy": strategy,
            },
        }
        documents.append(doc)

    return documents


def process_all_documents(notes_dir: Path | None = None, strategy: str = "sentences") -> list[dict]:
    if notes_dir is None:
        notes_dir = NOTES_DIR

    pdf_files = sorted(notes_dir.glob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files in {notes_dir}")

    all_documents = []
    for pdf_path in pdf_files:
        try:
            docs = process_document(pdf_path, strategy=strategy)
            all_documents.extend(docs)
        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {e}")

    logger.info(f"Total documents generated: {len(all_documents)}")
    return all_documents


if __name__ == "__main__":
    documents = process_all_documents()
    print(f"\nGenerated {len(documents)} document chunks")
    if documents:
        print(f"\nSample document:")
        import json
        sample = dict(documents[0])
        sample["text"] = sample["text"][:300] + "..."
        print(json.dumps(sample, indent=2, ensure_ascii=False))
