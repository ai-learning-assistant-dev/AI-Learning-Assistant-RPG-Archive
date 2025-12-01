import asyncio
import os
from pathlib import Path

import aiohttp
from fastapi import APIRouter

from app.models.schemas import CardImportRequest, KeyError, standard_response
from app.services.store_service import store_service
from app.utils.http_client import get_http_client
from config.settings import settings

router = APIRouter()


@router.post("/card/import")
@standard_response()
async def import_card(param: CardImportRequest):
    """转调导入角色卡接口"""
    # Implementation for importing a card goes here
    res = await store_service.get_cards_by_session(param.session_id)
    if res is None:
        raise KeyError(data=f"session_id not exist {param.session_id}")

    hash = res.get("hash", None)
    if hash is None:
        raise KeyError(data=f"file not exist for session_id {param.session_id}")

    file = os.path.join(settings.card_folder, hash + ".json")
    content = await asyncio.to_thread(Path(file).read_bytes)

    form = aiohttp.FormData()
    form.add_field(
        "avatar",
        content,
        filename=hash + ".json",
        content_type="application/json",
    )
    form.add_field("file_type", "json")
    async with get_http_client().post(
        url=f"http://{settings.sillytavern_host}/api/card/import",
        data=form,
    ) as response:
        result = await response.json()
        return result
