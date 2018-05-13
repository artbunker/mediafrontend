
from flask import request, abort

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

def populate_uri(medium, media_uri, media_api_uri):
	filename = mime.id + '.' + mime_to_extension(medium.mime)
	from media import MediumProtection
	if MediumProtection.NONE != medium.protection:
		medium.uri = api_uri.format('fetch/' + filename)
		return
	medium.uri = media_uri.format(filename)

def create_temp_medium_file(file_contents):
	import os
	import uuid
	file_path = os.path.join(__name__, 'tmp', 'temp_medium_' + str(uuid.uuid4()))
	f = open(file_path, 'w+b')
	f.write(file_contents)
	f.close()
	return file_path

def get_file_size(file_path):
	import os
	return os.path.getsize(file_path)

def get_file_mime(file_path):
	import magic
	mime = magic.Magic(mime=True)
	return mime.from_file(file_path)

def get_file_md5(file_path):
	chunk_size = 4096

	import hashlib
	hash_algo = hashlib.md5()

	with open(file_path, 'rb') as f:
		for chunk in iter(lambda: f.read(chunk_size), b''):
			hash_algo.update(chunk)
	return hash_algo.digest()

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
			populate_uri(medium, self.config['media_uri'], self.config['api_uri'])
			populate_category(medium)
		return medium

	def search_media(self, **kwargs):
		media = self.media.search_media(**kwargs)
		for medium in media:
			populate_id(medium)
			populate_uri(medium, self.config['media_uri'], self.config['api_uri'])
			populate_category(medium)
		return media

	def require_medium(self, medium_md5):
		medium = self.get_medium(medium_md5)
		if not medium:
			abort(404, {'message': 'medium_not_found'})
		return medium

	def encode_tag(self, tag):
		for needle, replacement in self.config['tag_encode_replacements']:
			tag = tag.replace(needle, replacement)

		return tag

	def place_medium_file(self, medium, source_file_path=None):
		import os

		from media import MediumProtection

		filename = medium.id + '.' + mime_to_extension(medium.mime)

		protected_path = os.path.join(self.config['media_path'], 'protected')
		nonprotected_path = os.path.join(self.config['media_path'], 'nonprotected')

		if MediumProtection.NONE != medium.protection:
			source_path = nonprotected_path
			destination_path = protected_path
		else:
			source_path = protected_path
			destination_path = nonprotected_path

		if source_file_path:
			source = source_file_path
		else:
			source = os.path.join(source_path, filename)

		#TODO eat exceptions?
		#try:
		os.rename(source, os.path.join(destination_path, filename))
		#except Exception:
		#	pass

	def place_medium_summaries(self, medium):
		import os

		from media import MediumProtection

		protected_path = os.path.join(self.config['summaries_path'], 'protected')
		nonprotected_path = os.path.join(self.config['summaries_path'], 'nonprotected')

		if MediumProtection.NONE != medium.protection:
			source_path = nonprotected_path
			destination_path = protected_path
		else:
			source_path = protected_path
			destination_path = nonprotected_path

		for extension in summary_extensions:
			for size in self.config['summary_widths']:
				filename = medium.id + '.' + size + '.' + extension

				#TODO eat exceptions?
				#try:
				os.rename(os.path.join(source_path, filename), os.path.join(destination_path, filename))
				#except Exception:
				#	pass
				pass

	def remove_medium_file(self, medium):
		filename = medium.id + '.' + mime_to_extension(medium.mime)
		os.remove(os.path.join(self.config['media_path'], 'protected', filename))
		os.remove(os.path.join(self.config['media_path'], 'nonprotected', filename))

	def remove_medium_summaries(self, medium):
		for extension in summary_extensions:
			for size in self.config['summary_widths']:
				filename = medium.id + '.' + size + '.' + extension
				os.remove(os.path.join(self.config['summaries_path'], 'protected', filename))
				os.remove(os.path.join(self.config['summaries_path'], 'nonprotected', filename))

	def generate_medium_summaries(self, medium):
		self.remove_medium_summaries(medium)

		#TODO specific summary generation based on mimetypes
		updates = {}
		# image
		if 'image' == medium.category:
			#TODO get image resource
			if 'image/png' == medium.mime:
				pass
			elif 'image/webp' == medium.mime:
				pass
			elif 'image/jpeg' == medium.mime:
				pass
			elif 'image/gif' == medium.mime:
				#TODO check for multiple frames
					#TODO save resized gif summaries of all summary widths greater than actual width
					#TODO updates['data4'] = frames
				pass
			#TODO get width and height
			#TODO create thumbnails from copy of original resource
			#TODO calculate hsv average
			updates['data1'] = width
			updates['data2'] = height
			updates['data3'] = hsv_average
		elif 'video' == medium.category:
			#TODO get duration
			#TODO get self.config['video_snapshots'] at even intervals throughout the video
			#TODO create thumbnails from copy of first snapshot resource
			#TODO create slideshow preview from snapshot resources at self.config['video_slideshow_width']
			#TODO calculate hsv average of first snapshot resource
			updates['data1'] = width
			updates['data2'] = height
			updates['data3'] = hsv_average
			updates['data4'] = frames
			updates['data5'] = duration_ms
		elif 'audio':
			if 'audio/mpeg' == medium.mime:
				#TODO get id3 info for mp3
				#TODO add #title:, #tracknum:, #album:, and #author: based on id3?
				#TODO if id3 cover image is present then generate summaries from it
				pass
			else:
				#TODO nothing for other audio types yet
				pass
		elif 'application':
			if 'application/x-shockwave-flash' == medium.mime:
				width = 0
				height = 0
				#TODO get swf width and height
				#TODO frames?
				#TODO fps?
				#TODO flash version?
				#TODO pull frame of flash video and create summaries?
			pass
		elif 'archive':
			#TODO no archive summary yet
			pass
		elif 'text':
			#TODO no text summary
			pass
		if 0 < len(updates):
			self.media.update_medium(medium, **updates)

	def multiupload(self):
		#TODO do groups/properties/tag processing once
		#TODO loop through uploads and apply processed groups/properties/tags to each
		pass

	def upload_from_request(self):
		errors = []
		file_contents = None
		if 'upload_uri' in request.form and request.form['upload_uri']:
			import urllib
			try:
				response = urllib.request.urlopen(request.form['upload_uri'])
			except urllib.error.HTTPError as e:
				errors.append('remote_file_request_http_error')
			except urllib.error.URLError as e:
				errors.append('remote_file_request_url_error')
			else:
				if not response:
					errors.append('remote_file_request_empty_response')
				else:
					file_contents = response.read()
		elif 'upload_file' in request.files:
			try:
				file_contents = request.files['upload_file'].stream.read()
			except ValueError as e:
				errors.append('problem_uploading_file')
		elif 'local' in request.form:
			#TODO local file
			#request.form['local']
			pass
		else:
			errors.append('missing_file')

		if 0 < len(errors):
			return errors, None

		file_path = create_temp_medium_file(file_contents)
		size = get_file_size(file_path)
		mime = get_file_mime(file_path)

		if self.config['maximum_size'] < size:
			errors.append('greater_than_maximum_size')
		if mime in self.config['disallowed_mimes']:
			errors.append('mimetype_not_allowed')

		if 0 < len(errors):
			import os
			os.remove(file_path)
			return errors, None

		md5 = get_file_md5(file_path)
		uploader_remote_origin = request.remote_addr
		uploader_uuid = self.accounts.current_user.uuid
		owner_uuid = self.accounts.current_user.uuid
		# manager can set medium owner directly
		if self.accounts.has_global_group(self.accounts.current_user, 'manager'):
			if 'owner_id' in request.form:
				owner = self.accounts.get_user(id_to_uuid(request.form['owner_id']))
				if not owner:
					errors.append('owner_not_found')
					return errors, None
				#TODO only allow contributors to be assigned as owner?
				#self.accounts.users.populate_user_permissions(owner)
				#if not self.accounts.users.has_global_group(owner, 'contributor'):
					#TODO warning for owner not set
				#else:
				owner_uuid = owner.uuid

		try:
			medium = self.media.create_medium(md5, uploader_remote_origin, uploader_uuid, owner_uuid)
		except ValueError:
			if MediumStatus.COPYRIGHT == medium.status:
				errors.append('medium_copyright')
			elif MediumStatus.FORBIDDEN == medium.status:
				errors.append('medium_forbidden')
			else:
				errors.append('medium_already_exists')
			return errors, medium

		updates = {}
			
		if 'searchability' in request.form:
			updates['searchability'] = request.form['searchability']

		if 'protection' in request.form:
			updates['protection'] = request.form['protection']

		if 'creation_date' in request.form:
			import dateutil
			try:
				updates['creation_time'] = dateutil.parser.parse(request.form['creation_date']).timestamp()
			except ValueError:
				#TODO warning for creation time not set
				pass

		groups = []
		for group in self.accounts.users.available_groups:
			field = 'groups[' + group + ']'
			if field in request.form:
				groups.append(group)
		if 0 < len(groups):
			updates['group_bits'] = int.from_bytes(
				self.accounts.users.combine_groups(names=groups),
				'big'
			)

		if 0 < len(updates):
			self.media.update_medium(medium, **updates)

		tags = []
		if 'author_tag' in request.form:
			if self.accounts.current_user.display:
				tags.append('#author:' + self.accounts.current_user.display)

		if 'filename_tag' in request.form:
			tags.append('#filename:' + filename)

		if 'tags' in request.form:
			tags += self.tag_string_to_list(request.form['tags'])

		if 0 < len(tags):
			self.media.add_tags(medium, tags)

		# update medium from db after alterations
		medium = self.get_medium(medium.md5)

		if 0 < len(errors):
			self.place_medium_file(medium)

			if 'generate_summaries' in request.form:
				self.generate_medium_summaries(medium)

		return errors, medium
