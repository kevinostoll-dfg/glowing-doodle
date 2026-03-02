"""Task modules for the Call Intelligence Platform workers."""

from app.tasks import analysis, notifications, transcription

__all__ = [
    "analysis",
    "notifications",
    "transcription",
]
