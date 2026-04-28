import shutil
import sys
import tarfile
import tempfile
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

WINDOWS_USERNAME = "\u4e25\u9756\u7428"
PADDLEOCR_ROOT = Path("D:/learningpass-ai-grading/backend/paddle_models")

MODEL_CONFIGS = [
    {
        "name": "det",
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv4/chinese/ch_PP-OCRv4_det_infer.tar",
        "archive_name": "ch_PP-OCRv4_det_infer.tar",
        "extracted_dir": "ch_PP-OCRv4_det_infer",
        "target_dir": PADDLEOCR_ROOT / "ch_PP-OCRv4_det_infer",
    },
    {
        "name": "rec",
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv4/chinese/ch_PP-OCRv4_rec_infer.tar",
        "archive_name": "ch_PP-OCRv4_rec_infer.tar",
        "extracted_dir": "ch_PP-OCRv4_rec_infer",
        "target_dir": PADDLEOCR_ROOT / "ch_PP-OCRv4_rec_infer",
    },
]

CHUNK_SIZE = 1024 * 1024
CONNECT_TIMEOUT = 10
READ_TIMEOUT = 60
RETRY_TOTAL = 5
BACKOFF_FACTOR = 1.5


def create_session() -> requests.Session:
    retry = Retry(
        total=RETRY_TOTAL,
        connect=RETRY_TOTAL,
        read=RETRY_TOTAL,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def format_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{num_bytes} B"


def show_progress(downloaded: int, total: int | None, prefix: str) -> None:
    if total:
        percent = downloaded / total * 100
        message = (
            f"\r{prefix}: {percent:6.2f}% "
            f"({format_size(downloaded)} / {format_size(total)})"
        )
    else:
        message = f"\r{prefix}: {format_size(downloaded)}"
    print(message, end="", flush=True)



def download_file(session: requests.Session, url: str, destination: Path) -> None:
    print(f"Starting download: {url}")
    with session.get(url, stream=True, timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)) as response:
        response.raise_for_status()
        total = int(response.headers.get("Content-Length", 0)) or None
        downloaded = 0

        with destination.open("wb") as file_obj:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if not chunk:
                    continue
                file_obj.write(chunk)
                downloaded += len(chunk)
                show_progress(downloaded, total, f"Downloading {destination.name}")

    print()
    print(f"Download complete: {destination}")



def _is_within_directory(base: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False



def safe_extract(archive_path: Path, extract_root: Path) -> Path:
    print(f"Extracting: {archive_path.name}")
    with tarfile.open(archive_path, mode="r") as tar:
        for member in tar.getmembers():
            member_path = extract_root / member.name
            if not _is_within_directory(extract_root, member_path):
                raise tarfile.TarError(f"Unsafe path detected in archive: {member.name}")
        tar.extractall(path=extract_root)

    extracted_dir = extract_root / archive_path.stem
    if not extracted_dir.exists():
        raise FileNotFoundError(f"Expected extracted directory not found: {extracted_dir}")

    print(f"Extract complete: {extracted_dir}")
    return extracted_dir



def install_model(extracted_dir: Path, target_dir: Path) -> None:
    target_dir.parent.mkdir(parents=True, exist_ok=True)

    if target_dir.exists():
        print(f"Removing existing directory: {target_dir}")
        shutil.rmtree(target_dir)

    print(f"Installing model to: {target_dir}")
    shutil.move(str(extracted_dir), str(target_dir))
    print(f"Install complete: {target_dir}")



def process_model(session: requests.Session, config: dict[str, object], workspace: Path) -> None:
    archive_path = workspace / str(config["archive_name"])
    download_file(session, str(config["url"]), archive_path)
    extracted_dir = safe_extract(archive_path, workspace)
    install_model(extracted_dir, Path(config["target_dir"]))



def main() -> int:
    session = create_session()

    with tempfile.TemporaryDirectory(prefix="paddleocr_models_") as temp_dir:
        workspace = Path(temp_dir)
        print(f"Temporary workspace: {workspace}")

        for config in MODEL_CONFIGS:
            model_name = str(config["name"])
            print(f"\nProcessing model: {model_name}")
            try:
                process_model(session, config, workspace)
            except requests.RequestException as exc:
                print(f"Download failed [{model_name}]: {exc}", file=sys.stderr)
                return 1
            except tarfile.TarError as exc:
                print(f"Extraction failed [{model_name}]: {exc}", file=sys.stderr)
                return 1
            except Exception as exc:
                print(f"Installation failed [{model_name}]: {exc}", file=sys.stderr)
                return 1
            finally:
                archive_path = workspace / str(config["archive_name"])
                extracted_dir = workspace / str(config["extracted_dir"])
                if archive_path.exists():
                    archive_path.unlink(missing_ok=True)
                if extracted_dir.exists():
                    shutil.rmtree(extracted_dir, ignore_errors=True)

    print("\nAll PaddleOCR Chinese models were downloaded and installed successfully.")
    return 0


if __name__ == "__main__":
    start = time.time()
    exit_code = main()
    elapsed = time.time() - start
    print(f"Total elapsed time: {elapsed:.2f} seconds")
    raise SystemExit(exit_code)
