
from flask import abort

def md5_to_id(md5):
	import base64
	return base64.urlsafe_b64encode(md5).decode().strip('=')

def id_to_md5(id):
	from base64_url_repad import base64_url_repad
	import base64
	try:
		md5 = base64.urlsafe_b64decode(
			base64_url_repad(id)
		)
	except ValueError:
		return None

	return md5

def uuid_to_id(uuid):
	import base64
	return base64.urlsafe_b64encode(uuid.bytes).decode().strip('=')

def id_to_uuid(id):
	from base64_url_repad import base64_url_repad
	import base64
	try:
		uuid_bytes = base64.urlsafe_b64decode(
			base64_url_repad(id)
		)
	except ValueError:
		return None

	from uuid import UUID
	try:
		uuid = UUID(bytes=uuid_bytes)
	except ValueError:
		return None

	return uuid

def populate_id(object):
	if hasattr(object, 'uuid'):
		object.id = uuid_to_id(object.uuid)
	if hasattr(object, 'md5'):
		object.id = md5_to_id(object.md5)


class MediaArchive:
	def __init__(self, config, media, accounts, access_log=None):
		self.config = config
		self.media = media
		self.accounts = accounts
		self.access_log = access_log

		# media archive package required groups
		self.accounts.users.populate_groups()
		if 'contributor' not in self.accounts.users.available_groups:
			self.accounts.users.create_group('contributor')
			self.accounts.users.protect_group('contributor')

		if 'contributor' not in self.accounts.users.available_groups:
			self.accounts.users.create_group('taxonomist')
			self.accounts.users.protect_group('taxonomist')

		self.accounts.users.populate_groups()

	def add_log(self, scope, subject_uuid=None, object_uuid=None):
		if not self.access_log:
			return

		params = {}
		if subject_uuid:
			params['subject_uuid'] = subject_uuid
		if object_uuid:
			params['object_uuid'] = object_uuid

		self.access_log.create_log(
			request.remote_addr,
			scope,
			**params
		)

	def get_medium(self, medium_md5):
		medium = self.media.get_medium(medium_md5)
		if medium:
			populate_id(medium)
		return medium

	def search_media(self, filter={}, **kwargs):
		media = self.media.search_media(**kwargs)
		for medium in media:
			populate_id(medium)
		return media

	def require_medium(self, medium_md5):
		medium = self.get_medium(medium_md5)
		if not medium:
			abort(404, {'message': 'medium_not_found'})
		return medium
