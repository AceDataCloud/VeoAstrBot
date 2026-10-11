"""Veo video request and terminal-result boundaries."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from client import VeoClient, VeoError


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.headers = {"x-trace-id": "trace-veo"}

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, *_):
        return json.dumps(self.payload).encode()


@pytest.mark.asyncio
async def test_submit_sends_one_async_video_request():
    calls = []

    def fake_open(request, timeout):
        calls.append((request.full_url, json.loads(request.data), timeout))
        return FakeResponse({"task_id": "task-123"})

    with patch("client.OPENER.open", side_effect=fake_open):
        result = await VeoClient("test-key").submit("A paper kite rises")
    assert calls == [
        (
            "https://api.acedata.cloud/veo/videos",
            {
                "action": "text2video",
                "prompt": "A paper kite rises",
                "model": "veo31-fast",
                "async": True,
            },
            90,
        )
    ]
    assert result["status"] == "submitted"
    assert result["task_id"] == "task-123"
    assert "video_urls" not in result


@pytest.mark.asyncio
async def test_image_request_uses_one_authorized_first_frame():
    with patch(
        "client.OPENER.open", return_value=FakeResponse({"task_id": "task-456"})
    ) as opening:
        await VeoClient("test-key").submit(
            "A kite rises",
            image_url="https://example.org/kite.png",
            aspect_ratio="9:16",
        )
    payload = json.loads(opening.call_args.args[0].data)
    assert payload["action"] == "image2video"
    assert payload["image_urls"] == ["https://example.org/kite.png"]
    assert payload["aspect_ratio"] == "9:16"


@pytest.mark.asyncio
async def test_task_lookup_withholds_preview_until_terminal_success():
    pending = {"id": "task-123", "finished_at": None, "response": None}
    preview = {
        "id": "task-123",
        "finished_at": None,
        "response": {
            "success": True,
            "data": [
                {
                    "state": "succeeded",
                    "video_url": "https://cdn.example.org/preview.mp4",
                }
            ],
        },
    }
    finished = {
        "finished_at": 123.0,
        "response": {
            "success": True,
            "data": [
                {
                    "state": "succeeded",
                    "video_url": "https://cdn.example.org/final.mp4",
                    "supplier": "internal-only",
                }
            ],
            "cost": {
                "amount": 0.648,
                "list_amount": 0.72,
                "currency": "credit",
                "supplier": "internal-only",
            },
        },
    }
    failed = {
        "finished_at": 123.0,
        "response": {
            "success": False,
            "data": [
                {
                    "state": "failed",
                    "video_url": "https://cdn.example.org/preview.mp4",
                }
            ],
        },
    }
    with patch(
        "client.OPENER.open",
        side_effect=[
            FakeResponse(pending),
            FakeResponse(preview),
            FakeResponse(finished),
            FakeResponse(failed),
        ],
    ) as opening:
        first = await VeoClient("test-key").query("task-123")
        second = await VeoClient("test-key").query("task-123")
        last = await VeoClient("test-key").query("task-123")
        unsuccessful = await VeoClient("test-key").query("task-123")
    assert opening.call_count == 4
    assert first["status"] == second["status"] == "pending"
    assert first["video_urls"] == second["video_urls"] == []
    assert last["status"] == "succeeded"
    assert last["video_urls"] == ["https://cdn.example.org/final.mp4"]
    assert last["cost"] == {
        "amount": 0.648,
        "list_amount": 0.72,
        "currency": "credit",
    }
    assert "supplier" not in str(last)
    assert unsuccessful["status"] == "failed"
    assert unsuccessful["video_urls"] == []


@pytest.mark.asyncio
async def test_invalid_inputs_never_submit_a_paid_job():
    client = VeoClient("test-key")
    for kwargs in (
        {"prompt": " "},
        {"prompt": "A kite", "model": "veo31-fast-ingredients"},
        {"prompt": "A kite", "resolution": "720p"},
        {"prompt": "A kite", "image_url": "http://example.org/kite.png"},
        {"prompt": "A kite", "aspect_ratio": "9:16"},
    ):
        with patch("client.OPENER.open") as opening, pytest.raises(VeoError):
            await client.submit(**kwargs)
        assert opening.call_count == 0
