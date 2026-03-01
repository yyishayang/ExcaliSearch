# SPDX-FileCopyrightText: 2026 @albabsuarez
# SPDX-FileCopyrightText: 2026 @aslangallery
# SPDX-FileCopyrightText: 2026 @david598Uni
# SPDX-FileCopyrightText: 2026 @yyishayang
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import os
import uuid
from pathlib import Path
from fastapi import UploadFile

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
STORAGE_DIR = BASE_DIR / "storage"
DATA_DIR = BASE_DIR / "data"
INDEX_DIR = BASE_DIR / "whoosh_index"

ALLOWED_EXTENSIONS = {"pdf", "txt", "docx", "xlsx", "csv"}


def ensure_dirs():
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)


def get_file_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def is_allowed_file(filename: str) -> bool:
    return get_file_extension(filename) in ALLOWED_EXTENSIONS


async def save_upload(file: UploadFile) -> tuple[str, bytes]:
    ensure_dirs()
    ext = get_file_extension(file.filename)
    unique_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"

    file_path = STORAGE_DIR / unique_name
    content = await file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    return unique_name, content


def get_file_path(stored_filename: str) -> Path:
    return STORAGE_DIR / stored_filename


def delete_file(stored_filename: str) -> bool:
    path = STORAGE_DIR / stored_filename
    if path.exists():
        path.unlink()
        return True
    return False


def get_file_size_str(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"
