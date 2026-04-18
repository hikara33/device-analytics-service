import random
import string

from locust import HttpUser, between, task


def _rand_device_id() -> str:
    return "dev-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))


class DeviceAnalyticsUser(HttpUser):
    wait_time = between(0.05, 0.3)

    def on_start(self) -> None:
        self.device_id = _rand_device_id()
        self.client.post(
            f"/api/v1/devices/{self.device_id}/samples",
            json={"x": 0.0, "y": 0.0, "z": 0.0},
        )

    @task(5)
    def post_sample(self) -> None:
        self.client.post(
            f"/api/v1/devices/{self.device_id}/samples",
            json={"x": random.uniform(-10, 10), "y": random.uniform(-10, 10), "z": random.uniform(-10, 10)},
        )

    @task(2)
    def get_stats(self) -> None:
        self.client.get(f"/api/v1/devices/{self.device_id}/stats")

    @task(1)
    def health(self) -> None:
        self.client.get("/health")
