import asyncio
import mimetypes
import os
import tempfile
import traceback
import zipfile
from pathlib import Path
from typing import Any

try:
    import aiofiles
except ImportError:
    aiofiles = None

try:
    from kreuzberg import extract_file
except ImportError:
    extract_file = None

try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None


ParseResult = dict[str, Any]
KREUZBERG_INSTALL_MESSAGE = "kreuzberg is not installed. Run: pip install kreuzberg"
OCR_INSTALL_MESSAGE = "PaddleOCR is not installed. Run: pip install paddleocr paddlepaddle"
OCR_MODEL_DOWNLOAD_FAILURE_MESSAGE = (
    "PaddleOCR model initialization failed. "
    "Please check model files or local OCR configuration."
)
DET_MODEL_DIR = r"D:\learningpass-ai-grading\backend\paddle_models\ch_PP-OCRv4_det_infer"
REC_MODEL_DIR = r"D:\learningpass-ai-grading\backend\paddle_models\ch_PP-OCRv4_rec_infer"
CLS_MODEL_DIR = None
ocr: Any | None = None
CODE_FILE_ENCODINGS = ("utf-8", "utf-8-sig", "gb18030", "latin-1")

DOCUMENT_SUFFIXES = {".doc", ".docx", ".odt", ".rtf", ".pdf"}
CODE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".css",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".json",
    ".kt",
    ".md",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".sql",
    ".ts",
    ".tsx",
    ".txt",
    ".vue",
    ".xml",
    ".yaml",
    ".yml",
}
ARCHIVE_SUFFIXES = {".zip"}

LANGUAGE_BY_SUFFIX = {
    ".c": "c",
    ".cc": "cpp",
    ".cpp": "cpp",
    ".cs": "csharp",
    ".css": "css",
    ".go": "go",
    ".h": "c",
    ".hpp": "cpp",
    ".html": "html",
    ".java": "java",
    ".js": "javascript",
    ".json": "json",
    ".kt": "kotlin",
    ".md": "markdown",
    ".php": "php",
    ".py": "python",
    ".rb": "ruby",
    ".rs": "rust",
    ".sh": "shell",
    ".sql": "sql",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".txt": "text",
    ".vue": "vue",
    ".xml": "xml",
    ".yaml": "yaml",
    ".yml": "yaml",
}


def _build_result(
    extracted_text: str = "",
    extracted_code: str = "",
    language: str = "",
    confidence: float = 0.0,
    warnings: list[str] | None = None,
) -> ParseResult:
    return {
        "extracted_text": extracted_text,
        "extracted_code": extracted_code,
        "language": language,
        "confidence": max(0.0, min(1.0, confidence)),
        "warnings": warnings or [],
    }


def _append_warning(result: ParseResult, message: str) -> ParseResult:
    result.setdefault("warnings", []).append(message)
    return result


def _resolve_file_type(file_path: str, file_type: str) -> str:
    normalized = (file_type or "").strip().lower()
    if normalized:
        return normalized

    guessed_type, _ = mimetypes.guess_type(file_path)
    return (guessed_type or "application/octet-stream").lower()


def _create_ocr(show_log: bool = False) -> Any:
    if PaddleOCR is None:
        raise RuntimeError(OCR_INSTALL_MESSAGE)

    det_model_path = Path(DET_MODEL_DIR)
    rec_model_path = Path(REC_MODEL_DIR)

    if det_model_path.exists() and rec_model_path.exists():
        return PaddleOCR(
            use_angle_cls=False,
            lang="ch",
            det_model_dir=DET_MODEL_DIR,
            rec_model_dir=REC_MODEL_DIR,
            show_log=False,
        )

    print(
        "[OCR] Warning: local PaddleOCR model directories were not found. "
        "Falling back to default PaddleOCR initialization."
    )
    return PaddleOCR(
        use_angle_cls=False,
        lang="ch",
        show_log=show_log,
    )


def _is_missing_model_error(exc: Exception) -> bool:
    if isinstance(exc, FileNotFoundError):
        return True

    error_message = str(exc).lower()
    missing_markers = (
        "notfound",
        "not found",
        "no such file",
        "does not exist",
        "cannot find",
        "model file",
        ".pdmodel",
        ".pdiparams",
    )
    return any(marker in error_message for marker in missing_markers)


def _get_ocr(force_reinit: bool = False, show_log: bool = False) -> Any:
    global ocr

    if ocr is None or force_reinit:
        ocr = _create_ocr(show_log=show_log)

    return ocr


def _infer_language(file_path: Path) -> str:
    return LANGUAGE_BY_SUFFIX.get(file_path.suffix.lower(), "")


async def parse_file(file_path: str, file_type: str) -> ParseResult:
    resolved_path = Path(file_path)
    resolved_type = _resolve_file_type(file_path, file_type)
    print(
        f"[PARSER] 入口 - 文件路径: {file_path}, 原始类型: {file_type}, 解析后MIME: {resolved_type}"
    )

    if not resolved_path.exists():
        return _build_result(warnings=[f"File not found: {resolved_path}"])

    if not resolved_path.is_file():
        return _build_result(warnings=[f"Path is not a file: {resolved_path}"])

    try:
        if resolved_type.startswith("image/"):
            print("[PARSER] Dispatching to image parser")
            return await _parse_image(resolved_path)

        if resolved_type == "application/pdf":
            print(f"[PARSER] 判定为文档类型，将调用 _parse_document")
            print("[PARSER] Dispatching to document parser for PDF")
            return await _parse_document(resolved_path)

        if (
            "word" in resolved_type
            or "officedocument" in resolved_type
            or resolved_path.suffix.lower() in DOCUMENT_SUFFIXES
        ):
            print(f"[PARSER] 判定为文档类型，将调用 _parse_document")
            print("[PARSER] Dispatching to document parser")
            return await _parse_document(resolved_path)

        if (
            resolved_type in {
                "application/zip",
                "application/x-zip-compressed",
            }
            or resolved_path.suffix.lower() in ARCHIVE_SUFFIXES
        ):
            print("[PARSER] Dispatching to archive parser")
            return await _parse_archive(resolved_path)

        if (
            resolved_type.startswith("text/")
            or resolved_type in {"application/json", "application/xml"}
            or resolved_path.suffix.lower() in CODE_SUFFIXES
        ):
            print("[PARSER] Dispatching to code/text parser")
            return await _parse_code(resolved_path)

        print("[PARSER] Falling back to code/text parser")
        result = await _parse_code(resolved_path)
        return _append_warning(
            result,
            f"Unsupported file type '{resolved_type}', attempted text/code parsing.",
        )
    except Exception as exc:
        print(f"[PARSER] Failed to parse '{resolved_path}': {exc}")
        return _build_result(
            warnings=[f"Failed to parse '{resolved_path.name}': {exc}"],
        )


async def _parse_image(file_path: Path) -> ParseResult:
    if not file_path.exists():
        return _build_result(warnings=[f"File not found: {file_path}"])

    if not file_path.is_file():
        return _build_result(warnings=[f"Path is not a file: {file_path}"])

    print(f"[OCR] Starting OCR for image: {file_path}")

    try:
        ocr_engine = await asyncio.to_thread(_get_ocr)
    except Exception as exc:
        print(f"[OCR] Failed to initialize OCR engine: {exc}")
        return _build_result(warnings=[f"Failed to initialize OCR engine: {exc}"])

    try:
        result = await asyncio.to_thread(ocr_engine.ocr, str(file_path), cls=False)
    except Exception as exc:
        if not _is_missing_model_error(exc):
            print(f"[OCR] OCR execution failed: {exc}")
            return _build_result(warnings=[f"OCR execution failed: {exc}"])

        print(f"[OCR] Retrying OCR engine initialization because models were missing: {exc}")
        try:
            ocr_engine = await asyncio.to_thread(_get_ocr, True, True)
            result = await asyncio.to_thread(ocr_engine.ocr, str(file_path), cls=False)
        except Exception as retry_exc:
            print(f"[OCR] OCR retry failed: {retry_exc}")
            return _build_result(
                warnings=[
                    f"{OCR_MODEL_DOWNLOAD_FAILURE_MESSAGE} Original error: {retry_exc}"
                ]
            )

    print(f"[OCR] Raw OCR result type: {type(result)}")
    print(f"[OCR] Result preview: {str(result)[:200]}")

    texts: list[str] = []
    confidences: list[float] = []
    warnings: list[str] = []

    for block in result or []:
        if not block:
            continue

        for line in block:
            if not isinstance(line, (list, tuple)) or len(line) < 2:
                continue

            content = line[1]
            if not isinstance(content, (list, tuple)) or len(content) < 2:
                continue

            text = str(content[0]).strip()
            if text:
                texts.append(text)

            try:
                confidences.append(float(content[1]))
            except (TypeError, ValueError):
                continue

    if not texts:
        print("[OCR] Warning: no text recognized from image")
        warnings.append("No text was extracted from the image.")

    confidence = sum(confidences) / len(confidences) if confidences else 0.0
    extracted_text = "\n".join(texts)
    print(f"[OCR] Extracted text count: {len(texts)}")
    print(f"[OCR] Average confidence: {confidence}")

    return _build_result(
        extracted_text=extracted_text,
        extracted_code="",
        language="",
        confidence=confidence,
        warnings=warnings,
    )


async def _parse_code(file_path: Path) -> ParseResult:
    print(f"[CODE] Parsing code/text file: {file_path}")

    if not file_path.exists():
        return _build_result(warnings=[f"File not found: {file_path}"])

    if not file_path.is_file():
        return _build_result(warnings=[f"Path is not a file: {file_path}"])

    async def _read_with_aiofiles(encoding: str) -> str:
        assert aiofiles is not None
        async with aiofiles.open(file_path, mode="r", encoding=encoding) as file_obj:
            return await file_obj.read()

    def _read_with_pathlib(encoding: str) -> str:
        return file_path.read_text(encoding=encoding)

    extracted_code = ""
    warnings: list[str] = []
    used_encoding: str | None = None
    last_error: Exception | None = None

    try:
        for encoding in CODE_FILE_ENCODINGS:
            try:
                if aiofiles is not None:
                    extracted_code = await _read_with_aiofiles(encoding)
                else:
                    extracted_code = await asyncio.to_thread(_read_with_pathlib, encoding)
                used_encoding = encoding
                break
            except UnicodeDecodeError as exc:
                last_error = exc
                continue
            except OSError as exc:
                last_error = exc
                continue
    except Exception as exc:
        print(f"[CODE] Failed to read code file '{file_path}': {exc}")
        return _build_result(warnings=[f"Failed to read file: {exc}"])

    if used_encoding is None:
        error_message = (
            f"Failed to decode file with supported encodings: {last_error}"
            if last_error
            else "Failed to decode file content."
        )
        print(f"[CODE] {error_message}")
        return _build_result(warnings=[error_message])

    if not extracted_code.strip():
        warnings.append("No code content was extracted from the file.")

    if aiofiles is None:
        warnings.append("aiofiles is not installed, used synchronous file reading fallback.")

    if used_encoding != "utf-8":
        warnings.append(f"Read file using fallback encoding '{used_encoding}'.")

    language = _infer_language(file_path)
    print(f"[CODE] Parsed language: {language or 'unknown'}")

    return _build_result(
        extracted_text="",
        extracted_code=extracted_code,
        language=language,
        confidence=1.0,
        warnings=warnings,
    )


async def _parse_document(file_path: Path) -> ParseResult:
    print(f"[DOC] Parsing document: {file_path}")
    print(f"[DOC] Received file path: {file_path}")

    if not file_path.exists():
        return _build_result(warnings=[f"File not found: {file_path}"])

    if not file_path.is_file():
        return _build_result(warnings=[f"Path is not a file: {file_path}"])

    try:
        file_size = os.path.getsize(file_path)
        print(f"[DOC] File size: {file_size} bytes")
    except OSError as exc:
        print(f"[DOC] Failed to get file size for '{file_path}': {exc}")

    if extract_file is None:
        print("[DOC] Kreuzberg is not available")
        return _build_result(warnings=[KREUZBERG_INSTALL_MESSAGE])

    try:
        print(f"[DOC] Calling kreuzberg.extract_file for: {file_path}")
        result = await extract_file(str(file_path))
        print(f"[DOC] extract_file raw result preview: {str(result)[:200]}")
        extracted_text = str(getattr(result, "content", "") or "")
        warnings: list[str] = []
        if not extracted_text.strip():
            warnings.append("No text content was extracted from the document.")

        print(f"[DOC] Extracted document text length: {len(extracted_text)}")
        print(f"[DOC] Final document confidence: 0.8")
        return _build_result(
            extracted_text=extracted_text,
            extracted_code="",
            language="",
            confidence=0.8,
            warnings=warnings,
        )
    except Exception as exc:
        print(f"[DOC] Failed to parse document '{file_path}': {exc}")
        traceback.print_exc()
        raise


async def _parse_archive(file_path: Path) -> ParseResult:
    print(f"[ARCHIVE] Parsing archive: {file_path}")

    if not file_path.exists():
        return _build_result(warnings=[f"File not found: {file_path}"])

    if not file_path.is_file():
        return _build_result(warnings=[f"Path is not a file: {file_path}"])

    if file_path.suffix.lower() != ".zip":
        warning = (
            f"Unsupported archive format '{file_path.suffix or 'unknown'}'. "
            "Only .zip is supported."
        )
        print(f"[ARCHIVE] {warning}")
        return _build_result(warnings=[warning])

    try:
        with tempfile.TemporaryDirectory(prefix="parsed_archive_") as temp_dir:
            temp_path = Path(temp_dir)
            await asyncio.to_thread(_extract_zip_archive, file_path, temp_path)

            extracted_files = sorted(path for path in temp_path.rglob("*") if path.is_file())
            if not extracted_files:
                return _build_result(warnings=["No files were extracted from the archive."])

            tree_summary = ", ".join(
                extracted_file.relative_to(temp_path).as_posix()
                for extracted_file in extracted_files
            )
            warnings = [f"Archive contents: {tree_summary}"]
            merged_parts: list[str] = []
            confidences: list[float] = []

            for extracted_file in extracted_files:
                relative_name = extracted_file.relative_to(temp_path).as_posix()
                print(f"[ARCHIVE] Parsing inner file: {relative_name}")
                inner_result = await parse_file(
                    str(extracted_file),
                    _resolve_file_type(str(extracted_file), ""),
                )

                inner_text = str(inner_result.get("extracted_text", "") or "")
                inner_code = str(inner_result.get("extracted_code", "") or "")
                inner_language = str(inner_result.get("language", "") or "")

                section_parts = [f"===== {relative_name} ====="]
                if inner_text:
                    section_parts.append(inner_text)
                if inner_code:
                    code_header = (
                        f"[code:{inner_language}]" if inner_language else "[code]"
                    )
                    section_parts.append(code_header)
                    section_parts.append(inner_code)

                merged_parts.append("\n".join(section_parts).rstrip())
                confidences.append(float(inner_result.get("confidence", 0.0) or 0.0))

                for warning in inner_result.get("warnings", []):
                    warnings.append(f"{relative_name}: {warning}")

            average_confidence = (
                sum(confidences) / len(confidences) if confidences else 0.0
            )
            merged_text = "\n\n".join(part for part in merged_parts if part.strip())

            if not merged_text.strip():
                warnings.append("No text content was extracted from files in the archive.")

            print(f"[ARCHIVE] Parsed {len(extracted_files)} files from archive")
            print(f"[ARCHIVE] Average confidence: {average_confidence}")
            return _build_result(
                extracted_text=merged_text,
                extracted_code="",
                language="",
                confidence=average_confidence,
                warnings=warnings,
            )
    except zipfile.BadZipFile as exc:
        print(f"[ARCHIVE] Invalid ZIP archive '{file_path}': {exc}")
        return _build_result(
            warnings=[f"Invalid ZIP archive '{file_path.name}': {exc}"]
        )
    except Exception as exc:
        print(f"[ARCHIVE] Failed to parse archive '{file_path}': {exc}")
        return _build_result(
            warnings=[f"Failed to parse archive '{file_path.name}': {exc}"]
        )


def _extract_zip_archive(file_path: Path, target_dir: Path) -> None:
    with zipfile.ZipFile(file_path) as archive:
        archive.extractall(target_dir)
