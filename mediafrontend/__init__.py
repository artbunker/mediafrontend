import time
import os
import re
import hashlib
import uuid
import magic
import math
import urllib
import json
import subprocess

from flask import url_for, escape, Markup
from ipaddress import ip_address
from PIL import Image
import colorsys
import dateutil.parser

from media import Media, MediumStatus, MediumSearchability, MediumProtection
from parse_id import get_id_bytes
from idcollection import IDCollection

categories_to_mimes = {
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
		#TODO markdown gets its own category later maybe?
		'text/markdown',
		'text/x-markdown',
		'text/html',
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
	for category in categories_to_mimes:
		if mime in categories_to_mimes[category]:
			return category

	return 'unknown'

def populate_category(medium):
	if medium:
		medium.category = mime_to_category(medium.mime)

def populate_categories(media):
	for medium in media:
		medium.category = mime_to_category(medium.mime)

def get_file_size(file_path):
	return os.path.getsize(file_path)

def get_file_mime(file_path):
	mime = magic.Magic(mime=True)
	return mime.from_file(file_path)

def get_file_id(file_path):
	chunk_size = 4096
	hash_algo = hashlib.md5()

	with open(file_path, 'rb') as f:
		for chunk in iter(lambda: f.read(chunk_size), b''):
			hash_algo.update(chunk)
	return hash_algo.digest()

def rgb_average_from_image(image):
	small_image = image.copy()
	small_image.thumbnail((256, 256), Image.BICUBIC)
	data = list(small_image.getdata())
	total_pixels = len(data)
	r = 0
	g = 0
	b = 0
	for pixel in data:
		#TODO does gif still break this for some reason
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
	return colorsys.rgb_to_hsv(*rgb_average_from_image(image))

def hsv_to_int(h, s, v):
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

class MediaFrontend(Media):
	def __init__(self, config, accounts, access_log, engine, install=False):
		super().__init__(engine, config['db_prefix'], install)

		self.config = config
		self.accounts = accounts
		self.access_log = access_log

		self.accounts.populate_groups()
		if 'contributor' not in self.accounts.available_groups:
			self.accounts.create_group('contributor')
		self.accounts.populate_groups()

		self.config['maximum_tag_length'] = min(
			self.tag_length,
			self.config['maximum_tag_length'],
		)

		self.external_uris = False

		self.callbacks = {}

	def add_callback(self, name, f):
		if name not in self.callbacks:
			self.callbacks[name] = []
		self.callbacks[name].append(f)

	# cooldowns
	def upload_cooldown(self, remote_origin=None):
		return self.access_log.cooldown(
			'upload_medium',
			self.config['upload_cooldown_amount'],
			self.config['upload_cooldown_period'],
			remote_origin=remote_origin,
		)

	def per_medium_like_cooldown(self, medium_id, user_id):
		period_start_time = (
			time.time()
			- self.config['per_medium_like_cooldown_period']
		)
		like_count = self.count_likes(
			filter={
				'medium_ids': medium_id,
				'user_ids': user_id,
				'created_after': period_start_time,
			}
		)
		if like_count >= self.config['per_medium_like_cooldown_amount']:
			return True
		return False

	# require object or raise
	def require_medium(self, id):
		medium = self.get_medium(id)
		if not medium:
			raise ValueError('Medium not found')
		return medium

	# extend media methods
	def get_medium(self, medium_id):
		medium = super().get_medium(medium_id)
		if medium:
			self.populate_media_tags(medium)
			self.populate_medium_properties(medium)
		return medium

	def search_media(self, **kwargs):
		media = super().search_media(**kwargs)
		self.populate_media_tags(media)
		for medium in media.values():
			self.populate_medium_properties(medium)
		return media

	def create_medium(self, **kwargs):
		medium = super().create_medium(**kwargs)
		subject_id = ''
		if self.accounts.current_user:
			subject_id = self.accounts.current_user.id_bytes
		self.populate_medium_properties(medium)
		return medium

	def update_medium(self, medium_id, **kwargs):
		# uploader remote origin and uploader id can't be changed after upload
		if 'uploader_remote_origin' in kwargs:
			del kwargs['uploader_remote_origin']
		if 'uploader_id' in kwargs:
			del kwargs['uploader_id']
		# only managers can change media status
		if (
				not self.accounts.current_user
				or not self.accounts.current_user.has_permission(
					group_names='manager'
				)
			):
			if 'status' in kwargs:
				del kwargs['status']
		super().update_medium(medium_id, **kwargs)
		# fetch medium after updates
		medium = self.get_medium(medium_id)
		if not medium:
			return
		self.place_medium_file(medium)
		self.place_medium_summaries(medium)

	def remove_medium(self, medium):
		self.delete_medium_file(medium)
		self.delete_medium_summaries(medium)
		super().delete_medium(medium.id_bytes)
		subject_id = ''
		if self.accounts.current_user:
			subject_id = self.accounts.current_user.id_bytes
		self.access_log.create_log(
			scope='remove_medium',
			subject_id=subject_id,
			object_id=medium.id_bytes,
		)

	#additional media methods
	def tag_string_to_list(self, tag_string):
		return tag_string.split('#')

	def parse_search_tags(self, tags=[], management_mode=False):
		# replace canonical search tags
		for tag in tags:
			if tag in self.config['canonical_search_tags']:
				tags.append(self.config['canonical_search_tags'][tag])
				tags.remove(tag)
				
		escape = lambda value: (
			value
				.replace('\\', '\\\\')
				.replace('_', '\_')
				.replace('%', '\%')
				.replace('-', '\-')
		)

		groups = []
		without_groups = []
		with_mimes = []
		without_mimes = []
		time_limiters = {}
		for time_limiter in ['uploaded', 'created', 'touched']:
			time_limiters[time_limiter + '_afters'] = []
			time_limiters[time_limiter + '_befores'] = []
		filter = {}
		for tag in tags:
			if not tag or ('-' == tag[0] and 2 > len(tag)):
				continue

			# pagination
			if 'sort:' == tag[:5]:
				sort = tag[5:]
				if 'creation' == sort:
					sort = 'creation_time'
				elif 'upload' == sort:
					sort = 'upload_time'
				elif 'modify' == sort:
					sort = 'touch_time'
				elif 'color' == sort:
					sort = 'data3'
				filter['sort'] = sort
			elif 'order:' == tag[:6]:
				if 'desc' != tag[6:]:
					filter['order'] = 'asc'
			elif 'perpage:' == tag[:8]:
				perpage = tag[8:]
				try:
					filter['perpage'] = int(perpage)
				except ValueError:
					pass
				else:
					filter['perpage'] = min(
						filter['perpage'],
						self.config['maximum_search_perpage'],
					)
			# properties
			elif 'group:' == tag[:6]:
				groups.append(tag[6:])
			elif '-group:' == tag[:7]:
				without_groups.append(tag[7:])
			elif 'uploaded after:' == tag[:15]:
				try:
					uploaded_after = dateutil.parser.parse(tag[15:]).timestamp()
				except ValueError:
					pass
				else:
					time_limiters['uploaded_afters'].append(uploaded_after)
			elif 'uploaded before:' == tag[:16]:
				try:
					uploaded_before = dateutil.parser.parse(tag[16:]).timestamp()
				except ValueError:
					pass
				else:
					time_limiters['uploaded_befores'].append(uploaded_before)
			elif 'created after:' == tag[:14]:
				try:
					created_after = dateutil.parser.parse(tag[14:]).timestamp()
				except ValueError:
					pass
				else:
					time_limiters['created_afters'].append(created_after)
			elif 'created before:' == tag[:15]:
				try:
					created_before = dateutil.parser.parse(tag[15:]).timestamp()
				except ValueError:
					pass
				else:
					time_limiters['created_befores'].append(created_before)
			elif 'modified after:' == tag[:15]:
				try:
					modified_after = dateutil.parser.parse(tag[15:]).timestamp()
				except ValueError:
					pass
				else:
					time_limiters['touched_afters'].append(modified_after)
			elif 'modified before:' == tag[:16]:
				try:
					modified_before = dateutil.parser.parse(tag[16:]).timestamp()
				except ValueError:
					pass
				else:
					time_limiters['touched_befores'].append(modified_before)
			elif 'category:' == tag[:9]:
				category = tag[9:]
				if category in categories_to_mimes:
					for mime in categories_to_mimes[category]:
						with_mimes.append(mime)
			elif '-category:' == tag[:10]:
				category = tag[10:]
				if category in categories_to_mimes:
					for mime in categories_to_mimes[category]:
						without_mimes.append(mime)
			elif 'mimetype:' == tag[:9]:
				with_mimes.append(tag[9:])
			elif '-mimetype:' == tag[:10]:
				without_mimes.append(tag[10:])

			elif 'orientation:portrait' == tag:
				filter['portrait'] = True
			elif '-orientation:portrait' == tag:
				filter['portrait'] = False
			elif 'orientation:landscape' == tag:
				filter['landscape'] = True
			elif '-orientation:landscape' == tag:
				filter['landscape'] = False
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
			elif 'protection:' == tag[:11]:
				if 'with_protections' not in filter:
					filter['with_protections'] = []
				filter['with_protections'].append(tag[11:].upper())
			elif '-protection:' == tag[:12]:
				if 'without_protections' not in filter:
					filter['without_protections'] = []
				filter['without_protections'].append(tag[12:].upper())
			elif 'searchability:' == tag[:14]:
				if 'with_searchabilities' not in filter:
					filter['with_searchabilities'] = []
				filter['with_searchabilities'].append(tag[14:].upper())
			elif '-searchability:' == tag[:15]:
				if 'without_searchabilities' not in filter:
					filter['without_searchabilities'] = []
				filter['without_searchabilities'].append(tag[15:].upper())

			# management tags
			elif 'id:' == tag[:3] and management_mode:
				if 'md5s' not in filter:
					filter['md5s'] = []
				filter['md5s'].append(id_to_md5(tag[3:]))
			elif 'origin:' == tag[:7] and management_mode:
				if 'uploader_remote_origins' not in filter:
					filter['uploader_remote_origins'] = []
				filter['uploader_remote_origins'].append(tag[7:])
			elif 'uploader:' == tag[:9] and management_mode:
				if not 'uploader_uuids' in filter:
					filter['uploader_uuids'] = []
				filter['uploader_uuids'].append(id_to_uuid(tag[9:]))
			elif 'owner:' == tag[:6] and management_mode:
				if not 'owner_uuids' in filter:
					filter['owner_uuids'] = []
				filter['owner_uuids'].append(id_to_uuid(tag[6:]))
			elif 'status:' == tag[:7] and management_mode:
				if 'with_statuses' not in filter:
					filter['with_statuses'] = []
				filter['with_statuses'].append(tag[7:].upper())
			elif '-status:' == tag[:8] and management_mode:
				if 'without_statuses' not in filter:
					filter['without_statuses'] = []
				filter['without_statuses'].append(tag[8:].upper())
			elif 'liked by:' == tag[:9] and management_mode:
				filter['liked_by_user'] = tag[9:]
			elif '-~' == tag[:2] and 2 < len(tag):
				if 'without_tags_like' not in filter:
					filter['without_tags_like'] = []
				filter['without_tags_like'].append('%' + escape(tag[2:]) + '%')
			elif '-' == tag[:1]:
				if 'without_tags' not in filter:
					filter['without_tags'] = []
				filter['without_tags'].append(tag[1:])
			elif '~' == tag[:1] and 1 < len(tag):
				if 'with_tags_like' not in filter:
					filter['with_tags_like'] = []
				filter['with_tags_like'].append('%' + escape(tag[1:]) + '%')
			else:
				if 'with_tags' not in filter:
					filter['with_tags'] = []
				filter['with_tags'].append(tag)

		if groups:
			filter['with_group_bits'] = self.accounts.combine_groups(names=groups)
		if without_groups:
			filter['without_group_bits'] = self.accounts.combine_groups(
				names=without_groups,
			)
		if with_mimes:
			filter['with_mimes'] = with_mimes
		if without_mimes:
			filter['without_mimes'] = without_mimes
		for time_limiter in ['uploaded', 'created', 'touched']:
			if time_limiters[time_limiter + '_afters']:
				filter[time_limiter + '_after'] = max(
					time_limiters[time_limiter + '_afters']
				)
			if time_limiters[time_limiter + '_befores']:
				filter[time_limiter + '_before'] = min(
					time_limiters[time_limiter + '_befores']
				)

		return filter

	def populate_medium_uris(self, medium):
		if (
				MediumProtection.NONE != medium.protection
				or MediumStatus.ALLOWED != medium.status
			):
			protection_path = 'protected'
			media_uri = url_for(
				'media_api.api_fetch_medium',
				medium_filename='MEDIUM_FILENAME',
				_external=self.external_uris,
			).replace('MEDIUM_FILENAME', '{}')
			summaries_uri = url_for(
				'media_api.api_fetch_summary',
				summary_filename='SUMMARY_FILENAME',
				_external=self.external_uris,
			).replace('SUMMARY_FILENAME', '{}')
		else:
			protection_path = 'nonprotected'
			media_uri = self.config['medium_file_uri']
			summaries_uri = self.config['summary_file_uri']

		medium.uris = {
			'original': '',
			'static': {},
			'fallback': {},
			'reencoded': {},
		}

		medium_file = medium.id + '.' + mime_to_extension(medium.mime)
		if os.path.exists(
				os.path.join(
					self.config['media_path'],
					protection_path,
					medium_file,
				)
			):
			medium.uris['original'] = media_uri.format(medium_file)

		summary_path = os.path.join(
			self.config['summaries_path'],
			protection_path,
		)
		for edge in self.config['summary_edges']:
			summary_file = medium.id + '.' + str(edge)
			if 'image' == medium.category:
				if os.path.exists(
						os.path.join(summary_path, summary_file + '.webp')
					):
					medium.uris['static'][edge] = summaries_uri.format(
						summary_file + '.webp'
					)
				if os.path.exists(
						os.path.join(summary_path, summary_file + '.png')
					):
					medium.uris['fallback'][edge] = summaries_uri.format(
						summary_file + '.png'
					)
				if (
						'image/gif' == medium.mime
						and 1 < medium.data4
						and os.path.exists(
							os.path.join(summary_path, summary_file + '.gif')
						)
					):
					medium.uris['reencoded'][edge] = summaries_uri.format(
						summary_file + '.gif'
					)
			elif 'video' == medium.category:
				if os.path.exists(
						os.path.join(summary_path, summary_file + '.webp')
					):
					medium.uris['static'][edge] = summaries_uri.format(
						summary_file + '.webp'
					)
				if os.path.exists(
						os.path.join(summary_path, summary_file + '.png')
					):
					medium.uris['fallback'][edge] = summaries_uri.format(
						summary_file + '.png'
					)

			elif medium.category in ['audio', 'archive']:
				if os.path.exists(
						os.path.join(summary_path, summary_file + '.webp')
					):
					medium.uris['static'][edge] = summaries_uri.format(
						summary_file + '.webp'
					)
				if os.path.exists(
						os.path.join(summary_path, summary_file + '.png')
					):
					medium.uris['fallback'][edge] = summaries_uri.format(
						summary_file + '.png'
					)
		if 'video' == medium.category:
			if os.path.exists(
					os.path.join(summary_path,  medium.id + '.clip.webm')
				):
				medium.uris['reencoded']['clip'] = summaries_uri.format(
					medium.id + '.clip.webm'
				)
			if os.path.exists(
					os.path.join(summary_path,  medium.id + '.slideshow.webp')
				):
				medium.uris['static']['slideshow'] = summaries_uri.format(
					medium.id + '.slideshow.webp'
				)
			if os.path.exists(
					os.path.join(summary_path,  medium.id + '.slideshow.png')
				):
				medium.uris['fallback']['slideshow'] = summaries_uri.format(
					medium.id + '.slideshow.png'
				)
			if (
					not is_websafe_video(medium.mime)
					and os.path.exists(
						os.path.join(summary_path, medium.id + '.reencoded.webm')
					)
				):
				medium.uris['reencoded']['original'] = summaries_uri.format(
					medium.id + '.reencoded.webm'
				)

	def populate_medium_groups(self, medium):
		medium.groups = []
		for group in self.config['requirable_groups']:
			group_bit = self.accounts.group_name_to_bit(group)
			if not int.from_bytes(group_bit, 'big'):
				continue
			if self.accounts.contains_all_bits(medium.group_bits, group_bit):
				medium.groups.append(group)

	def populate_medium_semantic_tags(self, medium):
		medium.semantic_tags = {}
		for tag in medium.tags:
			if 'prev:' == tag[:5]:
				medium.semantic_tags['prev'] = tag[5:]
			elif 'next:' == tag[:5]:
				medium.semantic_tags['next'] = tag[5:]
			elif 'inferior of:' == tag[:12]:
				medium.semantic_tags['inferior of'] = tag[12:]
			elif 'superior of:' == tag[:12]:
				medium.semantic_tags['superior of'] = tag[12:]
			elif 'mirror:' == tag[:7]:
				medium.semantic_tags['mirror'] = tag[7:]
			elif 'title:' == tag[:6]:
				medium.semantic_tags['title'] = tag[6:]
			elif 'author:' == tag[:7]:
				medium.semantic_tags['author'] = tag[7:]
			elif 'cover:' == tag[:6]:
				medium.semantic_tags['cover'] = tag[6:]
			elif 'set:' == tag[:4]:
				if 'sets' not in medium.semantic_tags:
					medium.semantic_tags['sets'] = []
				set_name = tag[4:]
				weight_colon_pos = set_name.find(':')
				if -1 < weight_colon_pos:
					set_name = set_name[:weight_colon_pos]
				medium.semantic_tags['sets'].append(set_name)
			elif 'text:' == tag[:5]:
				medium.semantic_tags['text'] = tag[5:]
			elif 'blurb:' == tag[:6]:
				medium.semantic_tags['blurb'] = tag[6:]
			elif 'embed:' == tag[:6]:
				medium.semantic_tags['embed'] = tag[6:]

	def current_user_medium_response_code(self, medium):
		if self.accounts.current_user:
			if self.accounts.current_user.has_permission(
					group_names='manager'
				):
				return 200
			if MediumStatus.FORBIDDEN == medium.status:
				return 404
			if MediumStatus.COPYRIGHT == medium.status:
				return 451
			if MediumProtection.NONE == medium.protection:
				return 200
			if self.accounts.current_user.id == medium.owner_id:
				return 200
			if MediumProtection.PRIVATE == medium.protection:
				return 404
			if (
					0 == int.from_bytes(medium.group_bits, 'big')
					or self.accounts.current_user.has_permission(
						group_bits=medium.group_bits,
					)
				):
				return 200
		if MediumStatus.FORBIDDEN == medium.status:
			return 404
		if MediumStatus.COPYRIGHT == medium.status:
			return 451
		if MediumProtection.NONE == medium.protection:
			return 200
		if MediumProtection.PRIVATE == medium.protection:
			return 404
		for group in medium.groups:
			if group in self.config['premium_groups']:
				return 402
		return 403

	def populate_medium_properties(self, medium):
		populate_category(medium)
		self.populate_medium_uris(medium)
		self.populate_medium_groups(medium)
		self.populate_medium_semantic_tags(medium)
		medium.current_user_response_code = self.current_user_medium_response_code(medium)
		if medium.category in ['image', 'video'] and medium.data3:
			r, g, b = hsv_int_to_rgb(medium.data3)
			medium.rgb = {
				'r': r,
				'g': g,
				'b': b,
			}

	def populate_medium_like_data(self, medium):
		medium.current_user_like_count = 0
		medium.likeable = False
		if not self.accounts.current_user:
			return
		medium.current_user_like_count = self.count_likes(
			filter={
				'medium_ids': medium.id_bytes,
				'user_ids': self.accounts.current_user.id_bytes,
			},
		)
		if not medium.current_user_like_count:
			medium.likeable = True
			return

		cooldown_period_start = int(
			time.time() - self.config['per_medium_like_cooldown_period']
		)
		most_recent_likes = self.search_likes(
			filter={
				'medium_ids': medium.id_bytes,
				'user_ids': self.accounts.current_user.id_bytes,
				'created_after': cooldown_period_start,
			},
			perpage=(self.config['per_medium_like_cooldown_amount'] + 1),
		)
		if len(most_recent_likes.values()) < self.config['per_medium_like_cooldown_amount']:
			medium.likeable = True

	def populate_media_users(self, media):
		if IDCollection == type(media):
			media = list(media.values())
		if list != type(media):
			media = [media]
		user_ids = []
		for medium in media:
			user_ids.append(medium.uploader_id)
			user_ids.append(medium.owner_id)
		users = self.accounts.search_users(filter={'ids': user_ids})
		for medium in media:
			medium.uploader = users.get(medium.uploader_id)
			medium.owner = users.get(medium.owner_id)

	def populate_media_covers(self, media):
		if IDCollection == type(media):
			media = list(media.values())
		if list != type(media):
			media = [media]
		cover_medium_ids = []
		media_with_covers = []
		for medium in media:
			medium.cover = None
			if 'cover' in medium.semantic_tags:
				medium.cover_id = medium.semantic_tags['cover']
				cover_medium_ids.append(medium.cover_id)
				media_with_covers.append(medium)

		if not cover_medium_ids:
			return

		cover_media = self.search_media(filter={'ids': cover_medium_ids})
		for medium in media_with_covers:
			medium.cover = cover_media.get(medium.cover_id)

	def populate_medium_contents(self, medium):
		medium.contents = ''
		if 'text' != medium.category:
			return
		if (
				MediumStatus.ALLOWED != medium.status
				or MediumProtection.NONE != medium.protection
			):
			protection_path = 'protected'
		else:
			protection_path = 'nonprotected'
		medium_path = os.path.join(
			self.config['media_path'],
			protection_path,
			medium.id + '.' + mime_to_extension(medium.mime),
		)
		contents = ''
		try:
			f = open(medium_path, 'r')
		except FileNotFoundError:
			return
		else:
			contents = f.read()
		if not contents:
			return
		if 'text:html fragment' in medium.tags:
			medium.contents = contents
		#TODO render markdown contents as html
		#elif 'text:markdown' in medium.tags:
		#	pass
		else:
			contents = escape(contents).replace(
				'\n\r',
				'\n',
			).replace(
				'\r',
				'',
			).replace(
				'\n',
				Markup('&#10;'),
			).replace(
				'\t',
				Markup('&#9;'),
			)
			medium.contents = Markup('<pre>') + contents + Markup('</pre>')

	def populate_medium_sets(self, medium):
		default_filter = {}
		if (
				not self.accounts.current_user
				or not self.accounts.current_user.has_permission(
					group_names='manager'
				)
			):
			# only include allowed and non-private media in sets for non-managers
			default_filter = {
				'with_statuses': MediumStatus.ALLOWED,
				'without_protections': MediumProtection.PRIVATE,
			}
		escape = lambda value: (
			value
				.replace('\\', '\\\\')
				.replace('_', '\_')
				.replace('%', '\%')
				.replace('-', '\-')
		)
		medium.sets = {}
		set_media = []
		if 'sets' in medium.semantic_tags:
			for set in medium.semantic_tags['sets']:
				filter = default_filter.copy()
				filter['with_tags_like'] = escape('set:' + set) + '%'
				# get all media in set
				medium.sets[set] = self.search_media(filter=filter)
				for set_medium in medium.sets[set].values():
					if set_medium not in set_media:
						# add to all collected set media
						set_media.append(set_medium)
		self.populate_media_covers(set_media)
		set_medium_ids_to_media = {}
		for set_medium in set_media:
			set_medium_ids_to_media[set_medium.id] = set_medium
		for set in medium.sets:
			weighted_set_medium_ids = {}
			set_medium_ids = []
			for set_medium in medium.sets[set].values():
				weighted = False
				for tag in set_medium.tags:
					weight_start_pos = len(set) + 5
					if 'set:' + set + ':' == tag[:weight_start_pos]:
						weight = int(tag[weight_start_pos:])
						while weight in weighted_set_medium_ids:
							weight = weight + 1
						weighted_set_medium_ids[weight] = set_medium.id
				if not weighted:
					set_medium_ids.append(set_medium.id)
			ordered_set_medium_ids = []
			sorted_keys = sorted(weighted_set_medium_ids.keys())
			for key in sorted_keys:
				ordered_set_medium_ids.append(weighted_set_medium_ids[key])
			ordered_set_medium_ids += set_medium_ids
			medium.sets[set] = []
			for set_medium_id in ordered_set_medium_ids:
				set_medium = set_medium_ids_to_media[set_medium_id]
				if set_medium not in medium.sets[set]:
					medium.sets[set].append(set_medium_ids_to_media[set_medium_id])

	def get_contributors(self):
		contributors = []
		contributor_bit = self.accounts.group_name_to_bit('contributor')
		permissions = self.accounts.search_permissions(filter={
			'permissions': {
				'global': contributor_bit,
				'media': contributor_bit,
			}
		})
		for permission in permissions.values():
			contributors.append(permission.user)
		return contributors

	def build_tag_suggestions(self):
		suggestions = {
			'search_signed_out': [
				'protection:none',
				'protection:groups',
				'searchability:public',
				'searchability:groups',
				'sort:creation',
				'sort:upload',
				'sort:color',
				'sort:size',
				'sort:likes',
				'sort:random',
				'orientation:landscape',
				'orientation:portrait',
			],
			'search_manage': [
				'sort:touch',
				'protection:private',
				'status:allowed',
				'status:copyright',
				'status:forbidden',
				'searchability:hidden',
			],
			'signed_out': [],
			'signed_in': [],
			'manage': [
				'text:html fragment',
				#'text:markdown',
			],
			'clutter': [],
		}

		def filter_tags(tags, remove_clutter=False, remove_nonclutter=False):
			filtered_tags = []
			for tag in tags:
				clutter_tag = False
				for clutter_tag_prefix in self.config['clutter_tag_prefixes']:
					if clutter_tag_prefix == tag[:len(clutter_tag_prefix)]:
						clutter_tag = True
						break
				if clutter_tag:
					if remove_clutter:
						continue
				elif remove_nonclutter:
					continue
				filtered_tags.append(tag)
			return filtered_tags

		def get_nonclutter_tags(tags):
			return filter_tags(tags, remove_clutter=True)

		def get_clutter_tags(tags):
			return filter_tags(tags, remove_nonclutter=True)

		# signed out
		for category in categories_to_mimes:
			suggestions['search_signed_out'].append('category:' + category)
		mimes = self.get_mimes()
		for mime in mimes:
			suggestions['search_signed_out'].append('mimetype:' + mime)
		for group in self.config['requirable_groups']:
			suggestions['search_signed_out'].append('group:' + group)
		allowed_public_none_tags = self.search_tag_counts(
			filter={
				'with_statuses': MediumStatus.ALLOWED,
				'with_searchabilities': MediumSearchability.PUBLIC,
				'with_protections': MediumProtection.NONE,
			},
		)
		signed_out_tags = []
		for tag in allowed_public_none_tags:
			signed_out_tags.append(tag['tag'])
		suggestions['signed_out'] += get_nonclutter_tags(signed_out_tags)

		# signed in
		public_groups_tags = self.search_tag_counts(
			filter={
				'with_statuses': MediumStatus.ALLOWED,
				'with_searchabilities': MediumSearchability.PUBLIC,
				'with_protections': MediumProtection.GROUPS,
			},
		)
		group_groups_tags = self.search_tag_counts(
			filter={
				'with_statuses': MediumStatus.ALLOWED,
				'with_searchabilities': MediumSearchability.PUBLIC,
				'with_protections': MediumProtection.GROUPS,
			},
		)
		signed_in_tags = []
		for tag in public_groups_tags:
			signed_in_tags.append(tag['tag'])
		for tag in group_groups_tags:
			signed_in_tags.append(tag['tag'])
		suggestions['signed_in'] += get_nonclutter_tags(signed_in_tags)

		# clutter
		allowed_none_tags = self.search_tag_counts(
			filter={'with_statuses': MediumStatus.ALLOWED},
		)
		clutter_tags = []
		for tag in allowed_none_tags:
			clutter_tags.append(tag['tag'])
		suggestions['clutter'] += get_clutter_tags(clutter_tags)

		# manager
		#TODO uploader:{each unique uploader id}?
		#TODO owner:{each unique owner id}?
		# for now no suggestions for tags on private/copyright/forbidden media

		#TODO remove tags already in signed_out from signed_in/manage?

		for list_name, tags_list in suggestions.items():
			f = open(
				os.path.join(self.config['tags_path'], list_name + '.json'),
				'w',
			)
			f.write(json.dumps(tags_list))
			f.close()

	def get_tag_suggestion_lists(self, management_mode=False, search=False):
		tag_files = ['signed_out']
		protected_tag_files = []
		if search:
			tag_files.append('search_signed_out')
		if self.accounts.current_user:
			protected_tag_files.append('signed_in')
			if management_mode:
				protected_tag_files.append('manage')
				if search:
					protected_tag_files.append('search_manage')
					tag_files.append('clutter')
		tags_file_uri = self.config['tags_file_uri']
		protected_tags_file_uri = self.config['protected_tags_file_uri']
		tag_suggestion_lists = []
		for tag_file in tag_files:
			tag_suggestion_lists.append(tags_file_uri.format(tag_file + '.json'))
		for protected_tag_file in protected_tag_files:
			tag_suggestion_lists.append(
				protected_tags_file_uri.format(protected_tag_file + '.json')
			)
		return tag_suggestion_lists

	def create_temp_medium_file(self, file_contents):
		file_path = os.path.join(self.config['temp_path'], 'temp_medium_' + str(uuid.uuid4()))
		f = open(file_path, 'w+b')
		f.write(file_contents)
		f.close()
		return file_path

	def place_medium_file(self, medium, source_file_path=None):
		medium_file = medium.id + '.' + mime_to_extension(medium.mime)

		protected_path = os.path.join(self.config['media_path'], 'protected')
		nonprotected_path = os.path.join(self.config['media_path'], 'nonprotected')

		if (
				MediumProtection.NONE != medium.protection
				or MediumStatus.ALLOWED != medium.status
			):
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

	def delete_medium_file(self, medium):
		medium_file = medium.id + '.' + mime_to_extension(medium.mime)

		for protection_path in ['protected', 'nonprotected']:
			file_path = os.path.join(
				self.config['media_path'],
				protection_path,
				medium_file,
			)
			if os.path.exists(file_path):
				os.remove(file_path)
		subject_id = ''
		if self.accounts.current_user:
			subject_id = self.accounts.current_user.id_bytes
		self.access_log.create_log(
			scope='delete_medium_file',
			subject_id=subject_id,
			object_id=medium.id_bytes,
		)

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
				# clip
				extensions.append('clip.webm')
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
		nonprotected_path = os.path.join(
			self.config['summaries_path'],
			'nonprotected',
		)
		if (
				MediumProtection.NONE != medium.protection
				or MediumStatus.ALLOWED != medium.status
			):
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

	def delete_medium_summaries(self, medium):
		self.iterate_medium_summaries(
			medium,
			lambda summary_path, summary_file: (
				os.remove(os.path.join(summary_path, summary_file))
			)
		)
		subject_id = ''
		if self.accounts.current_user:
			subject_id = self.accounts.current_user.id_bytes
		self.access_log.create_log(
			scope='delete_medium_summaries',
			subject_id=subject_id,
			object_id=medium.id_bytes,
		)

	def summaries_from_image(self, image, summary_path):
		full_width, full_height = image.size
		for edge in self.config['summary_edges']:
			thumbnail_edge = edge
			# for non-square images ensure shortest edge dimension is thumbnail edge
			# which means feeding .thumbnail() a calculated longest edge dimension
			# which will scale the shortest edge to the desired value
			if full_width < full_height:
				thumbnail_edge = full_height * (edge / full_width)
			elif full_width > full_height:
				thumbnail_edge = full_width * (edge / full_height)
			thumbnail = image.copy()
			#TODO maybe allow config to switch between
			#TODO NEAREST/BILINEAR/BICUBIC/LANCZOS for thumbnail resample?
			thumbnail.thumbnail((thumbnail_edge, thumbnail_edge), Image.BICUBIC)

			# static
			thumbnail_path = summary_path.format(str(edge) + '.webp')
			thumbnail.save(thumbnail_path, 'WebP', lossless=True)

			# fallback
			thumbnail_path = summary_path.format(str(edge) + '.png')
			thumbnail.save(thumbnail_path, 'PNG', optimize=True)

	def generate_video_snapshots(self, file_path, duration_s):
		# space the snapshot intervals out with the intention to skip first and last
		interval_s = math.floor(duration_s) / (self.config['video_snapshots'] + 2)

		snapshots = []
		for i in range(1, self.config['video_snapshots']):
			snapshot_path = os.path.join(
				self.config['temp_path'],
				'temp_snapshot_' + str(uuid.uuid4()) + '.png',
			)

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

			snapshot = Image.open(snapshot_path)
			snapshots.append((snapshot_path, snapshot))

			if 1 == i:
				#TODO for now only generate the one static summary
				#TODO maybe do slideshow later
				break
		return snapshots

	def reencode_video(
			self,
			file_path,
			output_path,
			width,
			height,
			edge,
			start_ms=0,
			end_ms=0,
			muted=False
		):
		if (
				0 > edge
				or not width
				or not height
			):
			return

		# using libvpx instead of libx264, so maybe the divisible by 2 requirement isn't needed?
		if width < height:
			resize_width = -1
			resize_height = edge
		else:
			resize_width = edge
			resize_height = -1

		ffmpeg_call = [
			self.config['ffmpeg_path'],
		]
		if (
				0 < end_ms
				and start_ms < end_ms
			):
			start_s = start_ms / 1000
			end_s = end_ms / 1000
			ffmpeg_call += [
				'-ss',
				str(start_s),
				'-i',
				file_path,
				'-t',
				str(end_s - start_s)
				#'-ss',
				#str(end_s),
			]
		else:
			ffmpeg_call += [
				'-i',
				file_path,
			]
		ffmpeg_call += [
			'-vcodec',
			'libvpx',
			'-quality',
			'good',
			'-cpu-used',
			'5',
			'-vf',
			'scale=' + str(resize_width) + ':' + str(resize_height),
			'-y',
		]
		if muted:
			ffmpeg_call += [
				'-an'
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
			output_path,
		]
		subprocess.run(ffmpeg_call)

	def get_video_info(self, file_path):
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

		return width, height, duration_s, audio_codec, video_codec

	def generate_medium_summaries(self, medium):
		self.delete_medium_summaries(medium)

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
			raise ValueError('Original file not found')

		updates = {}
		if 'image' == medium.category:
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
				width, height, duration_s, audio_codec, video_codec = self.get_video_info(file_path)

				if duration_s:
					# duration ms
					duration_ms = int(math.floor(duration_s * 1000))
					updates['data5'] = duration_ms

					snapshots = self.generate_video_snapshots(file_path, duration_s)

					# use snapshot dimensions if dimensions are missing
					first_snapshot_path, first_snapshot = snapshots[0]
					if not width:
						width = first_snapshot.width
					if not height:
						height = first_snapshot.height

					# static summaries from first snapshot
					self.summaries_from_image(first_snapshot, summary_path)
					updates['data3'] = hsv_to_int(*hsv_average_from_image(first_snapshot))

					#TODO create slideshow strip from snapshots
					#for path, snapshot in snapshots
						#snapshot.thumbnail(self.config['video_slideshow_edge'])
					#TODO save slideshow strip with .slideshow.webp and .slideshow.png
					#TODO remove snapshots
					for snapshot_path, snapshot in snapshots:
						snapshot.close()
						os.remove(snapshot_path)

					if 0 < self.config['video_clip_duration_ms']:
						if duration_ms <= self.config['video_clip_duration_ms']:
							start_ms = 0
							end_ms = duration_ms
						else:
							midpoint_ms = duration_ms / 2
							half_video_clip_duration_ms = self.config['video_clip_duration_ms'] / 2
							start_ms = midpoint_ms - half_video_clip_duration_ms
							end_ms = start_ms + self.config['video_clip_duration_ms']
						self.reencode_video(
							file_path,
							summary_path.format('clip.webm'),
							width,
							height,
							self.config['video_clip_edge'],
							start_ms=start_ms,
							end_ms=end_ms,
							muted=True
						)
				# reencode non-websafe video for the view page
				if not is_websafe_video(medium.mime):
					self.reencode_video(
						file_path,
						summary_path.format('reencoded.webm'),
						width,
						height,
						self.config['video_reencode_edge']
					)
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
					#img = Image.open(cover_path)
					#self.summaries_from_image(img)
					#os.remove(cover_path)
					pass
			else:
				#TODO nothing for other audio types yet
				pass
		elif 'application':
			if 'application/x-shockwave-flash' == medium.mime:
				#TODO parse flash headers
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
			pass
		if 0 < len(updates):
			self.update_medium(medium.id_bytes, **updates)
		subject_id = ''
		if self.accounts.current_user:
			subject_id = self.accounts.current_user.id_bytes
		self.access_log.create_log(
			scope='generate_medium_summaries',
			subject_id=subject_id,
			object_id=medium.id_bytes,
		)

	def upload(
			self,
			uploader_remote_origin,
			uploader_id,
			file_uri='',
			file_upload='',
		):
		errors = []
		file_contents = None
		filename = ''
		if file_uri:
			try:
				response = urllib.request.urlopen(file_uri)
			except urllib.error.HTTPError as e:
				errors.append('HTTP error from remote file request')
			except urllib.error.URLError as e:
				errors.append('URL error from remote file request')
			else:
				if not response:
					errors.append('Empty response from remote file request')
				else:
					file_contents = response.read()
					filename = file_uri.replace('\\', '/').split('/').pop()
		elif file_upload:
			try:
				file_contents = file_upload.stream.read()
			except ValueError as e:
				errors.append('Problem uploading file')
			else:
				filename = file_upload.filename
		else:
			errors.append('Missing medium file')

		if errors:
			return errors, filename, None

		file_path = self.create_temp_medium_file(file_contents)
		size = get_file_size(file_path)
		mime = get_file_mime(file_path)

		if self.config['maximum_upload_filesize'] < size:
			errors.append('File greater than maximum upload filesize')
		if mime in self.config['disallowed_mimetypes']:
			errors.append('Mimetype not allowed')

		if errors:
			if os.path.exists(file_path):
				os.remove(file_path)
			return errors, filename, None

		id = get_file_id(file_path)

		try:
			medium = self.create_medium(
				id=id,
				mime=mime,
				size=size,
				uploader_remote_origin=uploader_remote_origin,
				uploader_id=uploader_id,
			)
		except ValueError as e:
			if os.path.exists(file_path):
				os.remove(file_path)
			medium = self.collision_medium
			#TODO populate medium details?
			# copyright restricted
			if MediumStatus.COPYRIGHT == medium.status:
				errors.append('Medium copyright restricted')
				#TODO log copyright restricted attempt?
			# forbidden content
			elif MediumStatus.FORBIDDEN == medium.status:
				errors.append('Medium forbidden for content')
				#TODO log forbidden content attempt?
			# duplicate
			else:
				errors.append('Medium already exists')
				#TODO log duplicate?
			return errors, filename, medium

		self.place_medium_file(medium, file_path)
		return errors, filename, medium
