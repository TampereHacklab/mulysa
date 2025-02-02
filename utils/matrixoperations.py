#!/usr/bin/env python3
from nio import AsyncClient
import requests
import logging
import asyncio

logger = logging.getLogger(__name__)


class MatrixOperations:
    """
    Various basic single-request Matrix client-server API operations

    For more advanced operations you'll need a bot on Matrix side..
    """

    def __init__(self, access_token, matrix_server):
        self.access_token = access_token
        self.matrix_server = matrix_server
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        self.client = AsyncClient(matrix_server)
        self.client.access_token = access_token

    def send_message(self, room_id, message):
        api_url = (
            f"{self.matrix_server}_matrix/client/v3/rooms/{room_id}/send/m.room.message"
        )
        payload = {"msgtype": "m.text", "body": message}
        r = requests.post(api_url, headers=self.headers, json=payload)
        if r.status_code == 200:
            logger.debug(f"Sent Matrix message {message} to room {room_id}")
        else:
            logger.warn(f"Sending Matrix message failed: {r.content}")

    # Currently only used and tested function
    def invite_user(self, user_id, room_id, reason):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.client.room_invite(room_id, user_id))
        loop.run_until_complete(self.client.close())
        loop.close()

    def kick_user(self, user_id, room_id, reason):
        api_url = f"{self.matrix_server}_matrix/client/v3/rooms/{room_id}/kick"
        payload = {"reason": reason, "user_id": user_id}
        r = requests.post(api_url, headers=self.headers, json=payload)
        if r.status_code == 200:
            logger.debug(
                f"Kicked Matrix user {user_id} from room {room_id} because of {reason}"
            )
        else:
            logger.warn(f"Kicking Matrix user {user_id} failed:", r.content)
