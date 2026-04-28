import asyncio
from datetime import timedelta
from io import BytesIO

from fastapi import HTTPException

from app.core.config import settings
from app.core.minio_client import minio_client


async def upload_file(file_content: bytes, object_name: str, content_type: str) -> str:
    try:
        data = BytesIO(file_content)
        await asyncio.to_thread(
            minio_client.put_object,
            settings.MINIO_BUCKET,
            object_name,
            data,
            len(file_content),
            content_type=content_type,
        )
        return object_name
    except Exception as exc:
        raise HTTPException(status_code=500, detail="File upload failed") from exc


def get_file_url(object_name: str) -> str:
    return minio_client.presigned_get_object(
        settings.MINIO_BUCKET,
        object_name,
        expires=timedelta(seconds=3600),
    )
