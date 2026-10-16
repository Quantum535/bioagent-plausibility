import os

import google.auth
import google.auth.transport.requests

from providers.openai_p import OpenAICompatProvider

SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]


class VertexGeminiProvider(OpenAICompatProvider):
    """Gemini via Vertex's OpenAI-compatible endpoint, authenticated with ADC (no API key)."""

    def __init__(self, model, system, tools, reasoning_effort=None, max_tokens=8000,
                 project=None, location=None):
        self.project = project or os.environ["GOOGLE_CLOUD_PROJECT"]
        self.location = location or os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
        self.creds, _ = google.auth.default(scopes=SCOPES)
        self._refresh()
        base = (f"https://aiplatform.googleapis.com/v1/projects/{self.project}"
                f"/locations/{self.location}/endpoints/openapi")
        if self.location != "global":
            base = base.replace("https://aiplatform", f"https://{self.location}-aiplatform")
        model = model if model.startswith("google/") else "google/" + model
        super().__init__(model, system, tools, base_url=base, api_key=self.creds.token,
                         reasoning_effort=reasoning_effort, max_tokens=max_tokens, name="gemini")

    def _refresh(self):
        if not self.creds.valid:
            self.creds.refresh(google.auth.transport.requests.Request())

    def complete(self, history, force_no_tools=False):
        self._refresh()
        self.client.api_key = self.creds.token
        return super().complete(history, force_no_tools)
