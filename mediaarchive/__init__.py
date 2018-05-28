import os

from flask import request, abort, url_for

from media import MediumStatus, MediumProtection, MediumSearchability

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

def create_temp_medium_file(file_contents):
	import uuid
	file_path = os.path.join(__name__, 'tmp', 'temp_medium_' + str(uuid.uuid4()))
	f = open(file_path, 'w+b')
	f.write(file_contents)
	f.close()
	return file_path

def get_file_size(file_path):
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

def rgb_average_from_image(image):
	from PIL import Image

	small_image = image.copy()
	small_image.thumbnail((256, 256), Image.BICUBIC)
	data = list(small_image.getdata())
	total_pixels = len(data)
	r = 0
	g = 0
	b = 0
	for pixel in data:
		#TODO gif breaks this for some reason
		if isinstance(pixel, int):
			return 0, 0, 0
		if 4 == len(pixel):
			pr, pg, pb, pa = pixel
			if 0 == pa:
				total_pixels -= 1
				continue
		elif 3 == len(pixel):
			(pr, pg, pb) = pixel
		else:
			return 0, 0, 0
		r += pr
		g += pg
		b += pb
	r = round(r / total_pixels)
	g = round(g / total_pixels)
	b = round(b / total_pixels)
	return r, g, b

def hsv_average_from_image(image):
	import colorsys
	return colorsys.rgb_to_hsv(*rgb_average_from_image(image))

def hsv_to_int(h, s, v):
	import math

	if isinstance(h, float):
		h = math.floor(h * 255)
	if isinstance(s, float):
		s = math.floor(s * 255)
	if isinstance(v, float):
		v = math.floor(v * 255)

	# store in 3 bytes
	h = h << 16
	s = s << 8

	return (h + s + v)

def int_to_hsv(hsv_int):
	h = hsv_int >> 16
	hsv_int -= h << 16
	s = hsv_int >> 8
	v = hsv_int - (s << 8)
	return h, s, v

def hsv_int_to_rgb(hsv_int):
	import colorsys
	import math

	h, s, v = int_to_hsv(hsv_int)
	r, g, b = colorsys.hsv_to_rgb(h / 255, s / 255, v / 255)

	return math.floor(r * 255), math.floor(g * 255), math.floor(b * 255)

def is_websafe_video(mime):
	if (
			'video/mp4' == mime
			or 'video/mpeg' == mime
			or 'video/webm' == mime
			or 'application/ogg' == mime
			or 'video/ogg' == mime
		):
		return True
	return False

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

	def populate_uris(self, medium):
		if self.config['api_uri']:
			fetch_uri = self.config['api_uri'].format('fetch/{}')
		else:
			fetch_uri = url_for(
				'media_archive.protected_medium_file',
				medium_filename='MEDIUM_FILENAME').replace('MEDIUM_FILENAME', '{}'
			)

		if not self.config['medium_file_uri']:
			self.config['medium_file_uri'] = url_for(
				'media_archive.medium_file',
				medium_filename='MEDIUM_FILENAME').replace('MEDIUM_FILENAME', '{}'
			)

		if MediumProtection.NONE != medium.protection:
			protection_path = 'protected'
			media_uri = fetch_uri
		else:
			protection_path = 'nonprotected'
			media_uri = self.config['medium_file_uri']

		medium.uris = {
			'original': '',
			'static': {},
			'fallback': {},
			'reencoded': {},
		}

		medium_file = medium.id + '.' + mime_to_extension(medium.mime)
		if os.path.exists(os.path.join(self.config['media_path'], protection_path, medium_file)):
			medium.uris['original'] = media_uri.format(medium_file)

		summary_path = os.path.join(self.config['summaries_path'], protection_path)
		for edge in self.config['summary_edges']:
			summary_file = medium.id + '.' + str(edge)
			if 'image' == medium.category:
				if os.path.exists(os.path.join(summary_path, summary_file + '.webp')):
					medium.uris['static'][edge] = media_uri.format(summary_file + '.webp')
				if os.path.exists(os.path.join(summary_path, summary_file + '.png')):
					medium.uris['fallback'][edge] = media_uri.format(summary_file + '.png')
				if (
						'image/gif' == medium.mime
						and 1 < medium.data4
						and os.path.exists(os.path.join(summary_path, summary_file + '.gif'))
					):
					medium.uris['reencoded'][edge] = media_uri.format(summary_file + '.gif')
			elif 'video' == medium.category:
				if os.path.exists(os.path.join(summary_path, summary_file + '.png')):
					medium.uris['static'][edge] = media_uri.format(summary_file + '.png')
				if os.path.exists(os.path.join(summary_path, summary_file + '.png')):
					medium.uris['fallback'][edge] = media_uri.format(summary_file + '.webp')

			elif medium.category in ['audio', 'archive']:
				if os.path.exists(os.path.join(summary_path, summary_file + '.webp')):
					medium.uris['static'][edge] = media_uri.format(summary_file + '.webp')
				if os.path.exists(os.path.join(summary_path, summary_file + '.png')):
					medium.uris['fallback'][edge] = media_uri.format(summary_file + '.png')
		if 'video' == medium.category:
			if os.path.exists(os.path.join(summary_path,  medium.id + '.slideshow.webp')):
				medium.uris['static']['slideshow'] = media_uri.format(medium.id + '.slideshow.webp')
			if os.path.exists(os.path.join(summary_path,  medium.id + '.slideshow.png')):
				medium.uris['fallback']['slideshow'] = media_uri.format(medium.id + '.slideshow.png')
			if (
					not is_websafe_video(medium.mime)
					and os.path.exists(os.path.join(summary_path, medium.id + '.reencoded.webm'))
				):
				medium.uris['reencoded']['original'] = media_uri.format(medium.id + '.reencoded.webm')

	def populate_medium_properties(self, medium):
		populate_id(medium)
		populate_category(medium)
		self.populate_uris(medium)
		medium.uploader_id = uuid_to_id(medium.uploader_uuid)
		medium.owner_id = uuid_to_id(medium.owner_uuid)
		if medium.category in ['image', 'video'] and medium.data3:
			r, g, b = hsv_int_to_rgb(medium.data3)
			medium.rgb = {
				'r': r,
				'g': g,
				'b': b,
			}

	def get_medium(self, medium_md5):
		medium = self.media.get_medium(medium_md5)
		if medium:
			self.populate_medium_properties(medium)
			self.media.populate_medium_tags(medium)
		return medium

	def search_media(self, **kwargs):
		media = self.media.search_media(**kwargs)
		for medium in media:
			self.populate_medium_properties(medium)
		self.media.populate_media_tags(self.media.media_dictionary(media))
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
		medium_file = medium.id + '.' + mime_to_extension(medium.mime)

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
			source = os.path.join(source_path, medium_file)

		if os.path.exists(source):
			os.rename(
				source,
				os.path.join(destination_path, medium_file)
			)

	def remove_medium_file(self, medium):
		medium_file = medium.id + '.' + mime_to_extension(medium.mime)

		for protection_path in ['protected', 'nonprotected']:
			file_path = os.path.join(self.config['media_path'], protection_path, medium_file)
			if os.path.exists(file_path):
				os.remove(file_path)

	def iterate_medium_summaries(self, medium, cb):
		for protection_path in ['protected', 'nonprotected']:
			for edge in self.config['summary_edges']:
				summary_path = os.path.join(
					self.config['summaries_path'],
					protection_path
				)
				summary_file_template = medium.id + '.' + str(edge) + '.'

				extensions = []
				if 'image' == medium.category:
					# static, fallback, reencode
					extensions = ['webp', 'png', 'gif']
				elif 'video' == medium.category:
					# static, fallback
					extensions = ['webp', 'png']
				elif medium.category in ['audio', 'archive']:
					# static, fallback
					extensions = ['webp', 'png']
					
				for extension in extensions:
					summary_file =  summary_file_template + extension
					if os.path.exists(os.path.join(summary_path, summary_file)):
						cb(summary_path, summary_file)
			if 'video' == medium.category:
				# slideshow strips
				extensions = ['slideshow.webp', 'slideshow.png']
				# reencode
				if not is_websafe_video(medium.mime):
					extensions.append('reencoded.webm')
				for extension in extensions:
					summary_file = medium.id + '.' + extension
					if os.path.exists(os.path.join(summary_path, summary_file)):
						cb(summary_path, summary_file)

	def place_medium_summaries(self, medium):
		protected_path = os.path.join(self.config['summaries_path'], 'protected')
		nonprotected_path = os.path.join(self.config['summaries_path'], 'nonprotected')

		if MediumProtection.NONE != medium.protection:
			source_path = nonprotected_path
			destination_path = protected_path
		else:
			source_path = protected_path
			destination_path = nonprotected_path

		self.iterate_medium_summaries(
			medium,
			lambda summary_path, summary_file: (
				os.rename(
					os.path.join(summary_path, summary_file),
					os.path.join(destination_path, summary_file)
				)
			)
		)

	def remove_medium_summaries(self, medium):
		self.iterate_medium_summaries(
			medium,
			lambda summary_path, summary_file: (
				os.remove(os.path.join(summary_path, summary_file))
			)
		)

	def summaries_from_image(self, image, summary_path):
		from PIL import Image

		for edge in self.config['summary_edges']:
			thumbnail = image.copy()
			thumbnail.thumbnail((edge, edge), Image.BICUBIC)

			# static
			thumbnail_path = summary_path.format(str(edge) + '.webp')
			thumbnail.save(thumbnail_path, 'WebP', lossless=True)

			# fallback
			thumbnail_path = summary_path.format(str(edge) + '.png')
			thumbnail.save(thumbnail_path, 'PNG', optimize=True)

	def generate_medium_summaries(self, medium):
		self.remove_medium_summaries(medium)

		protection_path = 'nonprotected'
		if MediumProtection.NONE != medium.protection:
			protection_path = 'protected'

		file_path = os.path.join(
			self.config['media_path'],
			protection_path,
			medium.id + '.' + mime_to_extension(medium.mime)
		)
		summary_path = os.path.join(
			self.config['summaries_path'],
			protection_path,
			medium.id + '.{}'
		)

		if not os.path.exists(file_path):
			abort(500, {'message': 'original_file_not_found'})

		updates = {}
		if 'image' == medium.category:
			from PIL import Image

			img = Image.open(file_path)
			self.summaries_from_image(img, summary_path)

			updates['data1'] = img.width
			updates['data2'] = img.height
			updates['data3'] = hsv_to_int(*hsv_average_from_image(img))

			if 'image/gif' == medium.mime:
				frames = 1
				try:
					while True:
						img.seek(img.tell() + 1)
						frames += 1
				except EOFError:
					pass
				if 1 < frames:
					updates['data4'] = frames
					if self.config['ffmpeg_path']:
						import subprocess

						portrait = (img.width < img.height)
						for edge in self.config['summary_edges']:
							if portrait:
								width = -1
								height = min(edge, img.height)
							else:
								width = min(edge, img.width)
								height = -1

							ffmpeg_call = [
								self.config['ffmpeg_path'],
								'-i',
								file_path,
								'-vf',
								'scale=' + str(width) + ':' + str(height),
							]
							if (
									self.config['ffmpeg_thread_limit']
									and isinstance(self.config['ffmpeg_thread_limit'], int)
									and 0 < self.config['ffmpeg_thread_limit']
								):
								ffmpeg_call += [
									'-threads',
									str(self.config['ffmpeg_thread_limit']),
								]
							ffmpeg_call += [
								summary_path.format(str(edge) + '.gif'),
							]
							subprocess.run(ffmpeg_call)
		elif 'video' == medium.category:
			if self.config['ffprobe_path'] and self.config['ffmpeg_path']:
				import subprocess
				import json

				width = 0
				height = 0
				duration_s = 0
				audio_codec = ''
				video_codec = ''

				probe_json = subprocess.getoutput([
					self.config['ffprobe_path'],
					'-v',
					'quiet',
					'-print_format',
					'json',
					'-show_streams',
					'-i',
					file_path,
				])
				probe = json.loads(probe_json)

				if 'streams' in probe:
					for stream in probe['streams']:
						for key, value in stream.items():
							if 'width' == key or 'coded_width' == key:
								width = int(value)
							elif 'height' == key or 'coded_height' == key:
								height = int(value)
							elif 'duration' == key:
								duration_s = float(value)
					if (
							'codec_type' in stream
							and 'codec_name' in stream
						):
						codec_name = stream['codec_name']
						if 'audio' == stream['codec_type']:
							audio_codec = codec_name
						elif 'video' == stream['codec_type']:
							video_codec = codec_name

				# missing duration after streams probe, do packets probe
				if not duration_s:
					probe_json = subprocess.getoutput([
						self.config['ffprobe_path'],
						'-v',
						'quiet',
						'-print_format',
						'json',
						'-show_packets',
						'-i',
						file_path,
					])
					probe = json.loads(probe_json)

					last_frame = probe['packets'].pop()
					if 'dts_time' in last_frame:
						duration_s = float(last_frame['dts_time'])
					elif 'pts_time' in last_frame:
						duration_s = float(last_frame['pts_time'])

				# still missing duration after packets probe
				if not duration_s:
					#TODO attempt to estimate duration by seeking last keyframe from end
					# and doing some math based on frame length
					#try:
					#	fh = fopen(file_path, 'rb')
					#	fseek(fh, -4, SEEK_END)
					#	r = unpack('N', fread(fh, 4))
					#	last_tag_offset = r[1]
					#	fseek(fh, -(last_tag_offset + 4), SEEK_END)
					#	fseek(fh, 4, SEEK_CUR)
					#	t0 = fread(fh, 3)
					#	t1 = fread(fh, 1)
					#	r = unpack('N', t1 . t0)
					#	duration_ms = r[1]
					#	duration_s = duration_ms / 1000
					pass

				if duration_s:
					import uuid
					import math

					from PIL import Image

					# duration ms
					updates['data5'] = int(math.floor(duration_s * 1000))

					# space the snapshot intervals out with the intention to skip first and last
					interval_s = math.floor(duration_s) / (self.config['video_snapshots'] + 2)

					snapshots = []
					for i in range(1, self.config['video_snapshots']):
						snapshot_path = os.path.join(__name__, 'tmp', 'temp_snapshot_' + str(uuid.uuid4()) + '.png')

						ffmpeg_call = [
							self.config['ffmpeg_path'],
							'-i',
							file_path,
							'-ss',
							str(i * interval_s),
							'-frames:v',
							'1',
						]
						if (
								self.config['ffmpeg_thread_limit']
								and isinstance(self.config['ffmpeg_thread_limit'], int)
								and 0 < self.config['ffmpeg_thread_limit']
							):
							ffmpeg_call += [
								'-threads',
								str(self.config['ffmpeg_thread_limit']),
							]
						ffmpeg_call += [
							snapshot_path,
						]
						subprocess.run(ffmpeg_call)

						img = Image.open(snapshot_path)

						if 1 == i:
							# use snapshot dimensions if dimensions are missing
							if not width:
								width = img.width
							if not height:
								height = img.height

							self.summaries_from_image(img, summary_path)
							updates['data3'] = hsv_to_int(*hsv_average_from_image(img))
							#TODO for now only generate the one static summary, do slideshow later
							os.remove(snapshot_path)
							break

						os.remove(snapshot_path)
						#img.thumbnail(self.config['video_slideshow_edge'])
						#snapshots.append(img)
					#TODO create slideshow strip from snapshots
					#TODO save slidedown with .slideshow.webp and .slideshow.png
					pass
				# reencode non-websafe video for the view page
				if (
						0 != self.config['video_reencode_edge']
						and width
						and height
						and not is_websafe_video(medium.mime)
					):
					# using libvpx instead of libx264, so maybe the divisible by 2 requirement isn't needed?
					#if 0 != self.config['video_reencode_edge'] % 2:
						# libx264 requires sizes divisble by 2
						#abort(500, 'invalid_video_reencode_edge')
					if width < height:
						resize_width = -1
						#resize_width = 'trunc(oh*a/2)*2'
						resize_height = self.config['video_reencode_edge']
					else:
						resize_width = self.config['video_reencode_edge']
						resize_height = -1
						#resize_height = 'trunc(ow/a/2)*2'

					ffmpeg_call = [
						self.config['ffmpeg_path'],
						'-i',
						file_path,
						'-vcodec',
						'libvpx',
						'-quality',
						'good',
						'-cpu-used',
						'5',
						'-vf',
						'scale=' + str(resize_width) + ':' + str(resize_height),
					]
					if (
							self.config['ffmpeg_thread_limit']
							and isinstance(self.config['ffmpeg_thread_limit'], int)
							and 0 < self.config['ffmpeg_thread_limit']
						):
						ffmpeg_call += [
							'-threads',
							str(self.config['ffmpeg_thread_limit']),
						]
					ffmpeg_call += [
						summary_path.format('reencoded.webm'),
					]
					subprocess.run(ffmpeg_call)
				if width:
					updates['data1'] = width
				if height:
					updates['data2'] = height
				tags = []
				if audio_codec:
					tags.append('audio codec:' + audio_codec)
				if video_codec:
					tags.append('video codec:' + video_codec)
				if 0 < len(tags):
					#TODO auto-add tags
					pass

		elif 'audio':
			if 'audio/mpeg' == medium.mime:
				#TODO get id3 info for mp3
				#TODO add #title:, #tracknum:, #album:, and #author: based on id3?

				#TODO if id3 cover image is present then get image resource from it
				if False:
					from PIL import Image

					#img = Image.open(cover_path)
					#self.summaries_from_image(img)
					#os.remove(cover_path)
					pass
			else:
				#TODO nothing for other audio types yet
				pass
		elif 'application':
			if 'application/x-shockwave-flash' == medium.mime:
				#TODO parse flash headers, maybe hexagonit-swfheader, or implementing from scratch
				if False:
					header = {
						'width': 0,
						'height': 0,
						'frames': 0,
						'fps': 0,
						'version': 0,
					}
					updates['data1'] = header['width']
					updates['data2'] = header['height']
					updates['data4'] = header['frames']
					updates['data5'] = header['fps']
					updates['data6'] = header['version']
		elif 'archive':
			#TODO no archive summary yet
			#TODO check for cbr/cbz and get cover summary
			#TODO check for smgez and get cover summary
			pass
		if 0 < len(updates):
			self.media.update_medium(medium, **updates)

	def multiupload(self):
		#TODO do groups/properties/tag processing once
		#TODO loop through uploads and apply processed groups/properties/tags to each
		pass

	def tag_string_to_list(self, tag_string):
		return tag_string.split('#')

	def parse_search_tags(self, tags=[]):
		groups = []
		without_groups = []
		filter = {}
		for tag in tags:
			if not tag or ('-' == tag[0] and 2 > len(tag)):
				continue

			# pagination tags
			if 'sort:' == tag[:5]:
				sort = tag[5:]
				if 'color' == sort:
					sort = 'data3'
				elif 'creation' == sort:
					sort = 'creation_time'
				elif 'upload' == sort:
					sort = 'upload_time'
				filter['sort'] = tag[5:]
			elif 'order:' == tag[:6]:
				if 'desc' != tag[6:]:
					filter['order'] = 'asc'
			elif 'perpage:' == tag[:8]:
				perpage = tag[8:]
				try:
					filter['perpage'] = int(perpage)
				except ValueError:
					pass
			# search tags
			elif 'md5:' == tag[:4]:
				if 'md5s' not in filter:
					filter['md5s'] = []
				filter['md5s'].append(id_to_md5(tag[4:]))
			elif 'origin:' == tag[:7]:
				if 'uploader_remote_origins' not in filter:
					filter['uploader_remote_origins'] = []
				filter['uploader_remote_origins'].append(tag[7:])
			elif 'uploaded after:' == tag[:15]:
				import dateutil.parser
				try:
					uploaded_after = dateutil.parser.parse(tag[15:]).timestamp()
				except ValueError:
					pass
				else:
					if 'uploaded_afters' not in filter:
						filter['uploaded_afters'] = []
					filter['uploaded_befores'].append(uploaded_before)
			elif 'uploaded before:' == tag[:16]:
				import dateutil.parser
				try:
					uploaded_before = dateutil.parser.parse(tag[16:]).timestamp()
				except ValueError:
					pass
				else:
					if 'uploaded_befores' not in filter:
						filter['uploaded_befores'] = []
					filter['uploaded_befores'].append(uploaded_before)
			elif 'created after:' == tag[:14]:
				import dateutil.parser
				try:
					created_after = dateutil.parser.parse(tag[14:]).timestamp()
				except ValueError:
					pass
				else:
					if 'created_afters' not in filter:
						filter['created_afters'] = []
					filter['created_afters'].append(created_after)
			elif 'created before:' == tag[:15]:
				import dateutil.parser
				try:
					created_before = dateutil.parser.parse(tag[15:]).timestamp()
				except ValueError:
					pass
				else:
					if 'created_befores' not in filter:
						filter['created_befores'] = []
					filter['created_befores'].append(created_before)
			elif 'uploader:' == tag[:9]:
				if not 'uploader_uuids' in filter:
					filter['uploader_uuids'] = []
				filter['uploader_uuids'].append(id_to_uuid(tag[9:]))
			elif 'owner:' == tag[:6]:
				if not 'owner_uuids' in filter:
					filter['owner_uuids'] = []
				filter['owner_uuids'].append(id_to_uuid(tag[6:]))
			elif 'status:' == tag[:7]:
				filter['status'] = tag[7:].upper()
			elif '-status:' == tag[:8]:
				if 'without_statuses' not in filter:
					filter['without_statuses'] = []
				filter['without_statuses'].append(tag[8:].upper())
			elif 'protection:' == tag[:11]:
				filter['protection'] = tag[11:].upper()
			elif '-protection:' == tag[:12]:
				if 'without_protections' not in filter:
					filter['without_protections'] = []
				filter['without_protections'].append(tag[12:].upper())
			elif 'searchability:' == tag[:14]:
				filter['searchability'] = tag[14:].upper()
			elif '-searchability:' == tag[:15]:
				if 'without_searchabilities' not in filter:
					filter['without_searchabilities'] = []
				filter['without_searchabilities'].append(tag[15:].upper())
			elif 'group:' == tag[:6]:
				groups.append(tag[6:])
			elif '-group:' == tag[:7]:
				without_groups.append(tag[7:])
			elif 'mimetype:' == tag[:9]:
				filter['mime'] = tag[9:]
			elif '-mimetype:' == tag[:10]:
				if 'without_mimes' not in filter:
					filter['without_mimes'] = []
				filter['without_mimes'].append(tag[10:])
			elif 'smaller than:' == tag[:13]:
				filter['smaller_than'] = tag[13:]
			elif 'larger than:' == tag[:12]:
				filter['larger_than'] = tag[12:]
			elif 'data' == tag[:4]:
				for i in range(1, 7):
					data = 'data' + str(i)
					if data + ' less than:' == tag[:16]:
						filter[data + '_less_than'] = tag[:16]
					if data + ' more than:' == tag[:16]:
						filter[data + '_more_than'] = tag[:16]
			#TODO without tags like escaping
			#elif '-~' == tag[:2] and 2 < len(tag):
			#	if 'without_tags_like' not in filter:
			#		filter['without_tags_like'] = []
			#	filter['without_tags_like'].append(tag[2:])
			elif '-' == tag[:1]:
				if 'without_tags' not in filter:
					filter['without_tags'] = []
				filter['without_tags'].append(tag[1:])
			#TODO with tags like escaping
			#elif '~' == tag[:1] and 1 < len(tag):
			#	if 'with_tags_like' not in filter:
			#		filter['with_tags_like'] = []
			#	filter['with_tags_like'].append(tag[1:])
			else:
				if 'with_tags' not in filter:
					filter['with_tags'] = []
				filter['with_tags'].append(tag)

		if groups:
			print('combining with groups:')
			print(groups)
			filter['with_group_bits'] = self.accounts.users.combine_groups(names=groups)
			print('group bits:')
			print(filter['with_group_bits'])
		if without_groups:
			filter['without_group_bits'] = self.accounts.users.combine_groups(names=without_groups)

		return filter

	def remove_medium(self, medium):
		self.remove_medium_file(medium)
		self.remove_medium_summaries(medium)
		self.media.remove_tags(medium)
		self.media.remove_medium(medium)

	def require_access(self, medium):
		signed_in = False
		owner = False
		manager = False

		if self.accounts.current_user:
			signed_in = True
			if medium.owner_uuid == self.accounts.current_user.uuid:
				owner = True
			if self.accounts.current_user_has_global_group('manager'):
				manager = True

		if not manager:
			if MediumStatus.ALLOWED != medium.status:
				abort(451, {'message': 'unavailable'})
			if not owner:
				if MediumProtection.PRIVATE == medium.protection:
					abort(404, {'message': 'medium_not_found'})
				if MediumProtection.NONE == medium.protection:
					return
				if not signed_in:
					abort(401, {'message': 'medium_protected'})
				if MediumProtection.GROUPS == medium.protection:
					if not self.accounts.current_user_has_permissions(
							'global',
							medium.group_bits
						):
						for premium_group in self.config['premium_groups']:
							premium_group_bit = self.accounts.users.group_name_to_bit(premium_group)
							if self.accounts.users.contains_all_group_bits(
									medium.group_bits,
									premium_group_bit
								):
								if not self.accounts.has_global_group(
										self.accounts.current_user,
										premium_group
									):
									abort(402, {'message': 'premium_medium', 'group': premium_group})
						abort(403, {'message': 'protected_medium'})

	def upload_from_request(self):
		errors = []
		file_contents = None
		filename = ''
		if 'file_uri' in request.form and request.form['file_uri']:
			import urllib
			try:
				response = urllib.request.urlopen(request.form['file_uri'])
			except urllib.error.HTTPError as e:
				errors.append('remote_file_request_http_error')
			except urllib.error.URLError as e:
				errors.append('remote_file_request_url_error')
			else:
				if not response:
					errors.append('remote_file_request_empty_response')
				else:
					file_contents = response.read()
					filename = request.form['file_uri'].replace('\\', '/').split('/').pop()
		elif 'file_upload' in request.files:
			try:
				file_contents = request.files['file_upload'].stream.read()
			except ValueError as e:
				errors.append('problem_uploading_file')
			else:
				filename = request.files['file_upload'].filename
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

		if self.config['maximum_upload_filesize'] < size:
			errors.append('greater_than_maximum_upload_filesize')
		if mime in self.config['disallowed_mimes']:
			errors.append('mimetype_not_allowed')

		if 0 < len(errors):
			if os.path.exists(file_path):
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
			medium = self.media.create_medium(md5, uploader_remote_origin, uploader_uuid, owner_uuid, mime, size)
		except ValueError as e:
			if os.path.exists(file_path):
				os.remove(file_path)

			medium = e.args[0]
			populate_id(medium)
			if MediumStatus.COPYRIGHT == medium.status:
				errors.append('medium_copyright')
			elif MediumStatus.FORBIDDEN == medium.status:
				errors.append('medium_forbidden')
			else:
				errors.append('medium_already_exists')
			return errors, medium

		updates = {}
			
		if 'searchability' in request.form:
			#TODO add exception handling here for ValueErrors
			updates['searchability'] = request.form['searchability'].upper()

		if 'protection' in request.form:
			#TODO add exception handling here for ValueErrors
			updates['protection'] = request.form['protection'].upper()

		if 'creation_date' in request.form:
			import dateutil.parser
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
				tags.append('author:' + self.accounts.current_user.display)

		if 'filename_tag' in request.form and filename:
			tags.append('filename:' + filename)

		if 'tags' in request.form:
			tags += self.tag_string_to_list(request.form['tags'])

		if 0 < len(tags):
			self.media.add_tags(medium, tags)

		# update medium from db after alterations
		medium = self.get_medium(medium.md5)

		if 0 < len(errors):
			if os.path.exists(file_path):
				os.remove(file_path)
			return errors, medium

		self.place_medium_file(medium, file_path)
		if 'generate_summaries' in request.form:
			self.generate_medium_summaries(medium)

		return errors, medium
