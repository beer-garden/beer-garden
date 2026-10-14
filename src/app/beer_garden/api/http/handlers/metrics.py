from prometheus_client import generate_latest

from beer_garden.api.http.base_handler import BaseHandler


class MetricsHandler(BaseHandler):
    async def get(self):
        self.set_header("Content-Type", "text/plain; version=0.0.4; charset=UTF-8")
        self.write(generate_latest())
