"""Veo video tools for AstrBot through Ace Data Cloud."""

from __future__ import annotations

import json

from astrbot.api import AstrBotConfig
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .client import VeoClient, VeoError


class VeoPlugin(Star):
    """Expose one video submission and one existing-task lookup tool."""

    def __init__(self, context: Context, config: AstrBotConfig) -> None:
        super().__init__(context)
        self.config = config

    @filter.llm_tool(name="veo_generate_video")
    async def veo_generate_video(
        self,
        event: AstrMessageEvent,
        prompt: str,
        model: str = "veo31-fast",
        image_url: str = "",
        aspect_ratio: str = "16:9",
        resolution: str = "",
    ) -> str:
        """Submit one billable Veo text or image video job.

        Args:
            prompt(string): Description of the desired video.
            model(string): veo3, veo3-fast, veo31, or veo31-fast.
            image_url(string): Optional authorized HTTPS first-frame image.
            aspect_ratio(string): 16:9 or 9:16 for image-to-video.
            resolution(string): Optional 1080p, 4k, or gif; empty uses API default.

        Returns:
            JSON submission status and task ID, never a finished-video claim.
        """
        try:
            result = await VeoClient(self.config.get("api_key", "")).submit(
                prompt, model, image_url, aspect_ratio, resolution
            )
        except VeoError as exc:
            result = {"status": "error", "message": str(exc)}
        return json.dumps(result, ensure_ascii=False)

    @filter.llm_tool(name="veo_get_task")
    async def veo_get_task(self, event: AstrMessageEvent, task_id: str) -> str:
        """Query an existing Veo task without generating another video.

        Args:
            task_id(string): Exact task ID returned by veo_generate_video.

        Returns:
            JSON task status and final video URLs only after terminal success.
        """
        try:
            result = await VeoClient(self.config.get("api_key", "")).query(task_id)
        except VeoError as exc:
            result = {"status": "error", "message": str(exc), "task_id": task_id}
        return json.dumps(result, ensure_ascii=False)
