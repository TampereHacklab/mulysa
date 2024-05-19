#!/usr/bin/env python3
import requests
import logging
logger = logging.getLogger(__name__)

class MatrixOperations:
	"""
	Various basic single-request Matrix client-server API operations

	For more advanced operations you'll need a bot on Matrix side..
	"""

	def __init__(self, access_token, matrix_server):
		self.access_token = access_token
		self.matrix_server = matrix_server
		self.headers = { 'Authorization' : f'Bearer {self.access_token}', 'Content-Type': 'application/json' }

	def send_message(self, room_id, message):
		api_url=f'{self.matrix_server}_matrix/client/v3/rooms/{room_id}/send/m.room.message'
		payload={ "msgtype": "m.text", "body": message }
		r = requests.post(api_url, headers=self.headers, json = payload)
		if r.status_code == 200:
			logger.debug(f"Sent Matrix message {message} to room {room_id}")
		else:
			logger.warn(f"Sending Matrix message failed:", r.content)


	def invite_user(self, user_id, room_id, reason):
		api_url=f'{self.matrix_server}_matrix/client/v3/rooms/{room_id}/invite'
		payload={ "reason": reason, "user_id": user_id }
		r = requests.post(api_url, headers=self.headers, json = payload)
		if r.status_code == 200:
			logger.debug(f"Invited Matrix user {user_id} to room {room_id} because of {reason}")
		else:
			logger.warn(f"Inviting Matrix user {user_id} failed:", r.content)

	def kick_user(self, user_id, room_id, reason):
		api_url=f'{self.matrix_server}_matrix/client/v3/rooms/{room_id}/kick'
		payload={ "reason": reason, "user_id": user_id }
		r = requests.post(api_url, headers=self.headers, json = payload)
		if r.status_code == 200:
			logger.debug(f"Kicked Matrix user {user_id} from room {room_id} because of {reason}")
		else:
			logger.warn(f"Kicking Matrix user {user_id} failed:", r.content)
