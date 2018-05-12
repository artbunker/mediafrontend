
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

def mime_to_extension(mime):
	mimes_to_extensions = {
		# application
		'application/x-dosexec': 'exe',
		'application/x-shockwave-flash': 'swf',
		'application/pdf': 'pdf',
		# application special mimetype?
		'application/x-msdownload': 'exe',

		# audio
		'audio/mpeg': 'mp3',
		'audio/x-wav': 'wav',
		'audio/x-flac': 'flac',
		'audio/midi': 'mid',
		'audio/x-mod': 'mod',
		# audio special mimetype?
		'audio/mp3': 'mp3',
		'audio/x-ms-wma': 'wma',
		'audio/ogg': 'oga',
		'audio/webm': 'weba',
		'audio/3gpp': '3gp',
		'audio/3gpp2': '3g2',
		'audio/aac': 'aac',
		'audio/ac3': 'ac3',
		'audio/x-aiff': 'aif',
		'audio/aiff': 'aif',

		# archive
		'application/zip': 'zip',
		'application/x-gzip': 'gz',
		'application/x-tar': 'tar',
		'application/x-7z-compressed': '7z',
		'application/x-rar': 'rar',
		'application/x-bzip': 'bz',
		'application/x-bzip2': 'bz2',
		# archive special mimetype?
		'application/x-rar-compressed': 'rar',
		'application/gzip': 'gz',
		'application/x-zip': 'zip',
		'application/x-zip-compressed': 'zip',
		'application/s-compressed': 'zip',
		'multipart/x-zip': 'zip',
		'application/x-gtar': 'gtar',
		'application/x-gzip-compressed': 'tgz',

		# image
		'image/png': 'png',
		'image/jpeg': 'jpg',
		'image/gif': 'gif',
		'image/svg+xml': 'svg',
		# image special mimetype?
		'image/webp': 'webp',

		# text
		'text/plain': 'txt',
		'text/x-c++': 'txt',
		# text special mimetype?
		'text/srt': 'srt',
		'text/vtt': 'vtt',

		# video
		'video/mp4': 'mp4',
		'application/ogg': 'ogg',
		'video/x-ms-asf': 'wmv',
		'video/x-flv': 'flv',
		'video/x-msvideo': 'avi',
		'video/webm': 'webm',
		'video/quicktime': 'mov',
		'video/3gpp': '3gp',
		# video special mimetype?
		'video/3gpp2': '3g2',
		'video/ogg': 'ogv',
		'video/x-matroska': 'mkv',
		'video/x-ms-wmv': 'wmv',
		'video/avi': 'avi',
		'application/x-troff-msvideo': 'avi',
		'video/mpeg': 'mpg',
	}

	if mime not in mimes_to_extensions:
		return 'unknown'

	return mimes_to_extensions[mime]

def mime_to_category(mime):
	mimes_to_categories = {
		'application':	[
			'application/x-dosexec',
			'application/x-shockwave-flash',
			'application/pdf',
			# application special mimetype?
			'application/x-msdownload',
		],
		'audio':	[
			'audio/mpeg',
			'audio/x-wav',
			'audio/x-flac',
			'audio/midi',
			'audio/x-mod',
			# audio special mimetype?
			'audio/mp3',
			'audio/x-ms-wma',
			'audio/ogg',
			'audio/webm',
			'audio/3gpp',
			'audio/3gpp2',
			'audio/aac',
			'audio/ac3',
			'audio/x-aiff',
			'audio/aiff',
		],
		'archive':	[
			'application/zip',
			'application/x-gzip',
			'application/x-tar',
			'application/x-7z-compressed',
			'application/x-rar',
			'application/x-bzip',
			'application/x-bzip2',
			# archive special mimetype?
			'application/x-rar-compressed',
			'application/gzip',
			'application/x-zip',
			'application/x-zip-compressed',
			'application/s-compressed',
			'multipart/x-zip',
			'application/x-gtar',
			'application/x-gzip-compressed',
		],
		'image': [
			'image/png',
			'image/jpeg',
			'image/gif',
			'image/svg+xml',
			# image special mimetype?
			'image/webp',
		],
		'text':	[
			'text/plain',
			'text/x-c++',
			# text special mimetype?
			'text/srt',
			'text/vtt',
		],
		'video':	[
			'video/webm',
			'video/mp4',
			'application/ogg',
			'video/x-ms-asf',
			'video/x-flv',
			'video/x-msvideo',
			'video/quicktime',
			'video/3gpp',
			# video special mimetype?
			'video/ogg',
			'video/mpeg',
			'video/3gpp2',
			'video/x-matroska',
			'video/x-ms-wmv',
			'video/avi',
			'application/x-troff-msvideo',
		],
	}

	for category in mimes_to_categories:
		if mime in mimes_to_categories[category]:
			return category

	return 'unknown'

def populate_category(medium):
	if medium:
		medium.category = mime_to_category(medium.mime)

def populate_categories(media):
	for medium in media:
		medium.category = mime_to_category(medium.mime)

def get_file_mime(file_path):
	import magic
	mime = magic.Magic(mime=True)
	return mime.from_file(file_path)

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
			populate_category(medium)
		return medium

	def search_media(self, **kwargs):
		media = self.media.search_media(**kwargs)
		for medium in media:
			populate_id(medium)
			populate_category(medium)
		return media

	def require_medium(self, medium_md5):
		medium = self.get_medium(medium_md5)
		if not medium:
			abort(404, {'message': 'medium_not_found'})
		return medium
