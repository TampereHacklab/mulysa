#!/usr/bin/env python3
import requests

class MatrixOperations:
	def __init__(self, access_token, matrix_server):
		self.access_token = access_token
		self.matrix_server = matrix_server
		self.headers = { 'Authorization' : f'Bearer {self.access_token}', 'Content-Type': 'application/json' }

	def send_message(self, room_id, message):
		api_url=f'{self.matrix_server}_matrix/client/v3/rooms/{room_id}/send/m.room.message'
		payload={ "msgtype": "m.text", "body": message }
		r = requests.post(api_url, headers=self.headers, json = payload)
		print(r)
		print(r.content)

	def invite_user(self, user_id, room_id, reason):
		api_url=f'{self.matrix_server}_matrix/client/v3/rooms/{room_id}/invite'
		payload={ "reason": reason, "user_id": user_id }
		r = requests.post(api_url, headers=self.headers, json = payload)
		print(r)
		print(r.content)

	def kick_user(self, user_id, room_id, reason):
		api_url=f'{self.matrix_server}_matrix/client/v3/rooms/{room_id}/kick'
		payload={ "reason": reason, "user_id": user_id }
		r = requests.post(api_url, headers=self.headers, json = payload)
		print(r)
		print(r.content)

