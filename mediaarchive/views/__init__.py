from flask import Blueprint, render_template, abort, request, redirect, url_for, g

from .. import populate_id, id_to_uuid, id_to_md5
from pagination_from_request import pagination_from_request
from regex_converter import RegexConverter
from media import MediumStatus, MediumSearchability, MediumProtection

media_archive = Blueprint(
	'media_archive',
	__name__,
	template_folder='templates',
	static_folder='static',
	static_url_path='/media'
)

@media_archive.route('/upload', methods=['GET', 'POST'])
def upload():
	g.media_archive.accounts.require_global_group('contributor')

	manager = False
	contributors = []
	if g.media_archive.accounts.has_global_group(g.media_archive.accounts.current_user, 'manager'):
		manager = True
		contributor_bit = g.media_archive.accounts.users.group_name_to_bit('contributor')
		permissions = g.media_archive.accounts.search_permissions(filter={
			'permissions': {
				'global': contributor_bit,
				'media': contributor_bit,
			}
		})
		for permission in permissions:
			contributors.append(permission.user)

	fields = {
		'groups': [],

		'generate_summaries': g.media_archive.config['upload_defaults']['generate_summaries'],
		'owner_id': g.media_archive.accounts.current_user.id,
		'searchability': g.media_archive.config['upload_defaults']['searchability'],
		'protection': g.media_archive.config['upload_defaults']['protection'],
		'creation_date': '',

		'author_tag': g.media_archive.config['upload_defaults']['author_tag'],
		'filename_tag': g.media_archive.config['upload_defaults']['filename_tag'],
		'tags': '',

		'upload_uri': '',
	}

	errors = []
	if 'POST' != request.method:
		return render_template(
			'upload.html',
			errors=errors,
			manager=manager,
			contributors=contributors,
			fields=fields,
			groups=g.media_archive.config['requirable_groups'],
			medium=None,
		)

	errors, medium = g.media_archive.upload_from_request()

	if 0 == len(errors):
		return redirect(url_for('media_archive.view_medium', medium_id=medium.id), 302)

	for field in ['generate_summaries', 'author_tag', 'filename_tag']:
		fields[field] = (field in request.form)

	form_fields = [
		'owner_id',
		'searchability',
		'protection',
		'creation_date',
		'tags',
		'upload_uri',
	]
	for field in form_fields:
		if field in request.form:
			fields[field] = request.form[field]

	for group in g.media_archive.accounts.users.available_groups:
		field = 'groups[' + group + ']'
		if field in request.form:
			fields['groups'].append(group)

	return render_template(
		'upload.html',
		errors=errors,
		manager=manager,
		contributors=contributors,
		fields=fields,
		groups=g.media_archive.config['requirable_groups'],
		medium=medium,
	)

@media_archive.route('/help')
def help():
	return render_template('help.html')

def search(current_endpoint, overrides={}, search_field=True, manage=False, omit_future=True, **kwargs):
	tags_query = ''
	if 'tags' in request.args:
		tags_query = request.args['tags']

	tags = g.media_archive.tag_string_to_list(tags_query)
	limited_tags = []
	for tag in tags:
		if g.media_archive.config['maximum_search_tags'] == len(limited_tags):
			break
		limited_tags.append(tag)
	tags = limited_tags

	if 'sort:random' in tags:
		tags.remove('sort:random')
		import random, string
		seed = ''.join(random.choices(string.ascii_letters + string.digits, k=6)).upper()
		tags.append('sort:random:' + seed)
		return redirect(url_for(current_endpoint, tags='#'.join(tags), **kwargs), 302)

	if 0 < len(overrides):
		if 'tags' in overrides:
			tags = overrides['tags']
		else:
			if 'add_tags' in overrides:
				tags += overrides['add_tags']
			if 'remove_tags' in overrides:
				for tag in overrides['remove_tags']:
					if tag in tags:
						tags.remove(tag)

	if omit_future:
		from datetime import datetime, timezone
		import time
		current_datetime_atom = datetime.fromtimestamp(
			time.time(),
			timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f%z'
		)
		tags.append('created before:' + current_datetime_atom)


	filter = {}
	if tags:
		filter = g.media_archive.parse_search_tags(tags, manage)

	pagination = {
		'page': 0,
		'sort': 'creation',
		'order': 'desc',
		'perpage': 32,
	}
	if 'page' in request.args:
		pagination['page'] = int(request.args['page'])
	if 'sort' in filter:
		pagination['sort'] = filter['sort']
	if 'order' in filter:
		pagination['order'] = filter['order']
	if 'perpage' in filter:
		pagination['perpage'] = int(filter['perpage'])

	if 0 < len(overrides) and 'filter' in overrides:
		for key, value in overrides['filter'].items():
			filter[key] = value

	media = g.media_archive.search_media(filter=filter, **pagination)
	total_media = g.media_archive.media.count_media(filter=filter)

	# strip medium ids from protected media if not managing
	if not manage:
		for medium in media:
			if (
					(
							0 < int.from_bytes(medium.group_bits, 'big')
							or MediumProtection.NONE != medium.protection
						)
					and (
						not g.media_archive.accounts.current_user
						or not g.media_archive.accounts.current_user_has_permissions(
								medium.group_bits,
								'global'
							)
						)
				):
					medium.id = ''

	tags_this_page = []
	for medium in media:
		if 0 < len(medium.tags):
			for tag in medium.tags:
				if tag not in tags_this_page:
					tags_this_page.append(tag)

	tag_suggestion_lists = g.media_archive.get_tag_suggestion_lists(manage=manage, search=True)

	import math
	import re

	return render_template(
		'search.html',
		media=media,
		tags_query=tags_query,
		search_field=search_field,
		tag_suggestion_lists=tag_suggestion_lists,
		manage=manage,
		tags_this_page=tags_this_page,
		pagination=pagination,
		total_media=total_media,
		total_pages=math.ceil(total_media / pagination['perpage']),
		current_endpoint=current_endpoint,
		kwargs=kwargs,
		re=re,
	)

@media_archive.route('/tags')
def manage_tags():
	search = {
		'tag': '',
	}
	if 'tag' in request.args:
		search['tag'] = request.args['tag']

	filter = {}
	escape = lambda value: (
		value
			.replace('\\', '\\\\')
			.replace('_', '\_')
			.replace('%', '\%')
			.replace('-', '\-')
	)
	if search['tag']:
		filter['tags'] = '%' + escape(search['tag']) + '%'

	pagination = pagination_from_request('count', 'desc', 0, 32)

	if not g.media_archive.accounts.current_user_has_global_group('manager'):
		g.media_archive.accounts.require_global_group('contributor')
		filter['owner_uuid'] = g.media_archive.accounts.current_user.uuid

	total_tags = g.media_archive.media.count_tags(filter=filter, group=True)
	tags = g.media_archive.media.search_tags(filter=filter, **pagination, group=True)

	import math

	return render_template(
		'tags_list.html',
		tags=tags,
		search=search,
		pagination=pagination,
		total_tags=total_tags,
		total_pages=math.ceil(total_tags / pagination['perpage']),
	)

@media_archive.route('/tags/<mode>', methods=['GET', 'POST'])
def edit_tag(mode):
	owner_uuid = None
	if not g.media_archive.accounts.current_user_has_global_group('manager'):
		g.media_archive.accounts.require_global_group('contributor')
		owner_uuid = g.media_archive.accounts.current_user.uuid

	if mode not in ['remove', 'replace', 'accompany']:
		abort(400)

	tag = ''
	if 'tag' in request.args:
		tag = request.args['tag']

	tag2 = ''
	for key in ['replacement', 'accompaniment']:
		if key in request.args:
			tag2 = request.args[key]

	if 'POST' != request.method:
		return render_template(
			'edit_tag.html',
			mode=mode,
			tag=tag,
			tag2=tag2,
		)

	if 'tag' in request.form and request.form['tag']:
		if 'remove' == mode:
			g.media_archive.media.remove_tag(tag, owner_uuid)
		elif 'tag2' in request.form and request.form['tag2']:
			if 'replace' == mode:
				g.media_archive.media.replace_tag(
					request.form['tag'],
					request.form['tag2'],
					owner_uuid
				)
			elif 'accompany' == mode:
				filter = {
					'with_tags': request.form['tag'],
				}
				if owner_uuid:
					filter['owner_uuids'] = owner_uuid
				media = g.media_archive.search_media(filter=filter)
				if media:
					g.media_archive.media.add_tags(media, request.form['tag2'])

	return redirect(url_for('media_archive.manage_tags'), 302)

@media_archive.route('/manage')
def manage_media():
	filter = {}

	if not g.media_archive.accounts.has_global_group(g.media_archive.accounts.current_user, 'manager'):
		# contributor manage self
		g.media_archive.accounts.require_global_group('contributor')
		filter['owner_uuids'] = g.accounts.current_user.uuid

	return search('media_archive.manage_media', overrides={'filter': filter}, manage=True, omit_future=False)

@media_archive.route('/api/fetch/<medium_filename>')
def api_fetch(medium_filename):
	#TODO check for json request field
	g.json_request = True

	import os

	filename_pieces = medium_filename.split('.')
	if 2 > len(filename_pieces):
		abort(404, {'message': 'medium_not_found'})

	medium_id = filename_pieces[0]
	medium = g.media_archive.require_medium(id_to_md5(medium_id))

	# trying to access nonprotected medium through protected medium path
	if MediumProtection.NONE == medium.protection:
		abort(400)

	if 2 == len(filename_pieces):
		medium_extension = filename_pieces[1]
		# reencode
		if (
				'video' == medium.category
				and 'webm' == medium_extension
				and not is_websafe_video(medium.mime)
			):
			media_path = os.path.join(g.media_archive.config['summaries_path'], 'protected')
		else:
			media_path = os.path.join(g.media_archive.config['media_path'], 'protected')
	else:
		media_path = os.path.join(g.media_archive.config['summaries_path'], 'protected')

	g.media_archive.require_access(medium)

	if not os.path.exists(os.path.join(media_path, medium_filename)):
		abort(404, {'message': 'medium_not_found'})

	g.no_store = True

	from flask import send_from_directory

	return send_from_directory(media_path, medium_filename, mimetype=medium.mime, conditional=True)

@media_archive.route('/file/media/<medium_filename>')
def medium_file(medium_filename):
	import os

	summary_file = os.path.join(
		g.media_archive.config['summaries_path'],
		'nonprotected',
		medium_filename
	)
	medium_file = os.path.join(
		g.media_archive.config['media_path'],
		'nonprotected',
		medium_filename
	)
	if os.path.exists(summary_file):
		directory = os.path.join(
			g.media_archive.config['summaries_path'],
			'nonprotected'
		)
	elif os.path.exists(medium_file):
		directory = os.path.join(
			g.media_archive.config['media_path'],
			'nonprotected'
		)
	else:
		abort(404, {'message': 'medium_not_found'})

	from flask import send_from_directory

	return send_from_directory(directory, medium_filename, conditional=True)

@media_archive.route('/file/tags/<tags_filename>')
def tags_file(tags_filename):
	import os

	tags_file = os.path.join(
		g.media_archive.config['tags_path'],
		tags_filename
	)
	if not os.path.exists(tags_file):
		abort(404, {'message': 'tags_not_found'})

	from flask import send_from_directory

	return send_from_directory(
		g.media_archive.config['tags_path'],
		tags_filename,
		conditional=True
	)

@media_archive.route('/' + "<regex('([a-zA-Z0-9_\-]+)'):medium_id>", methods=['GET', 'POST'])
def view_medium(medium_id):
	from statuspages import PaymentRequired

	medium = g.media_archive.require_medium(id_to_md5(medium_id))

	try:
		g.media_archive.require_access(medium)
	except PaymentRequired as e:
		slideshow = g.media_archive.get_slideshow(medium)
		groups = []
		if 'groups' in e.description:
			groups = e.description['groups']
		return render_template('premium.html', groups=groups, slideshow=slideshow)

	edit_medium = False
	edit_tags = False
	tag_suggestion_lists = []

	if (
			g.media_archive.accounts.current_user
			and (
				medium.owner_uuid == g.media_archive.accounts.current_user.uuid
				or g.media_archive.accounts.current_user_has_global_group('manager')
			)
		):
		edit_medium = True
		edit_tags = True
		tag_suggestion_lists = g.media_archive.get_tag_suggestion_lists(manage=True, search=False)

	if edit_tags and 'POST' == request.method:
		tags = g.media_archive.tag_string_to_list(request.form['tags'])
		g.media_archive.media.remove_tags(medium)
		if 0 < len(tags):
			#TODO clearing tags to force tag addition works
			#TODO but probably should be handled inside the media module
			medium.tags = []
			g.media_archive.media.add_tags(medium, tags)
		g.media_archive.build_tag_suggestion_lists()
		if 'tags' in request.args and request.args['tags']:
			return redirect(
				url_for(
					'media_archive.view_medium',
					medium_id=medium_id,
					tags=request.args['tags']
				),
				302
			)
		return redirect(
			url_for(
				'media_archive.view_medium',
				medium_id=medium_id
			),
			302
		)

	visible_tags = 0
	for tag in medium.tags:
		if (
				'filename:' == tag[:9]
				or 'set:' == tag[:4]
				or 'cover:' == tag[:6]
				or 'mirror:' == tag[:7]
				or 'superior of:' == tag[:12]
				or 'inferior of:' == tag[:12]
				or 'next:' == tag[:5]
				or 'prev:' == tag[:5]
				or 'suppress:' == tag[:9]
			):
			continue
		visible_tags += 1

	return render_template(
		'view_medium.html',
		medium=medium,
		edit_medium=edit_medium,
		edit_tags=edit_tags,
		tag_suggestion_lists=tag_suggestion_lists,
		slideshow=g.media_archive.get_slideshow(medium),
		search_endpoint=g.media_archive.config['search_endpoint'],
		visible_tags=visible_tags,
	)

@media_archive.route('/' + "<regex('([a-zA-Z0-9_\-]+)'):medium_id>/edit", methods=['GET', 'POST'])
def edit_medium(medium_id):
	manager = False
	contributors = []
	if g.media_archive.accounts.has_global_group(g.media_archive.accounts.current_user, 'manager'):
		manager = True
		contributor_bit = g.media_archive.accounts.users.group_name_to_bit('contributor')
		permissions = g.media_archive.accounts.search_permissions(filter={
			'permissions': {
				'global': contributor_bit,
				'media': contributor_bit,
			}
		})
		for permission in permissions:
			contributors.append(permission.user)

	medium = g.media_archive.get_medium(id_to_md5(medium_id))

	if not manager:
		if not medium or MediumStatus.ALLOWED != medium.status:
			abort(403, {'message': 'manager_required'})

		g.media_archive.accounts.require_global_group('contributor')
		if medium.owner_uuid != g.media_archive.accounts.current_user.uuid:
			abort(403, {'message': 'not_medium_owner'})
	elif not medium:
		abort(404, {'message': 'medium_not_found'})

	fields = {
		'groups': [],

		'owner_id': medium.owner_id,
		'searchability': medium.searchability.name.lower(),
		'protection': medium.protection.name.lower(),
		'creation_time': medium.creation_time,
		'creation_date': medium.creation_time.strftime('%Y-%m-%dT%H:%M:%S.%f%z'),

		'file_uri': '',
	}

	for group in g.media_archive.accounts.users.available_groups:
		if g.media_archive.accounts.users.contains_all_group_bits(
				medium.group_bits,
				g.media_archive.accounts.users.group_name_to_bit(group)
			):
			fields['groups'].append(group)

	errors = []
	if 'POST' != request.method:
		return render_template(
			'edit_medium.html',
			errors=errors,
			manager=manager,
			contributors=contributors,
			fields=fields,
			groups=g.media_archive.config['requirable_groups'],
			medium=medium,
		)

	updates = {}

	# manager can set medium owner directly
	if manager:
		if 'owner_id' in request.form and request.form['owner_id'] != medium.owner_id:
			owner = g.media_archive.accounts.get_user(id_to_uuid(request.form['owner_id']))
			if not owner:
				errors.append('owner_not_found')
				return errors, None
			#TODO only allow contributors to be assigned as owner?
			#self.accounts.users.populate_user_permissions(owner)
			#if not self.accounts.users.has_global_group(owner, 'contributor'):
				#TODO warning for owner not set
			#else:
			updates['owner_uuid'] = owner.uuid

	if 'searchability' in request.form:
		#TODO add exception handling here for ValueErrors
		updates['searchability'] = request.form['searchability'].upper()

	place_files = False
	if 'protection' in request.form:
		protection = request.form['protection'].upper()
		if protection != medium.protection.name:
			#TODO add exception handling here for ValueErrors
			updates['protection'] = protection
			place_files = True
			

	if 'creation_date' in request.form:
		import dateutil.parser
		try:
			creation_time = dateutil.parser.parse(request.form['creation_date'])
		except ValueError:
			#TODO warning for creation time not set
			pass
		else:
			updates['creation_time'] = creation_time.timestamp()

	fields['groups'] = []
	for group in g.media_archive.accounts.users.available_groups:
		field = 'groups[' + group + ']'
		if field in request.form:
			fields['groups'].append(group)
	updates['group_bits'] = 0
	if 0 < len(fields['groups']):
		updates['group_bits'] = int.from_bytes(
			g.media_archive.accounts.users.combine_groups(names=fields['groups']),
			'big'
		)

	#TODO maybe compare updates['group_bits'] to medium.group_bits and remove it if they're the same
	# otherwise this isn't necessary since it'll always have group_bits in update
	if 0 < len(updates):
		g.media_archive.media.update_medium(medium, **updates)

	medium = g.media_archive.get_medium(medium.md5)

	if place_files:
		g.media_archive.place_medium_file(medium)
		g.media_archive.place_medium_summaries(medium)

	#TODO replace medium

	if 0 == len(errors):
		return redirect(url_for('media_archive.edit_medium', medium_id=medium.id), 302)

	form_fields = [
		'owner_id',
		'searchability',
		'protection',
		'creation_date',
		'upload_uri',
	]
	for field in form_fields:
		if field in request.form:
			fields[field] = request.form[field]

	#TODO get creation datetime from request.form['creation_date'] string

	return render_template(
		'edit_medium.html',
		errors=errors,
		manager=manager,
		contributors=contributors,
		fields=fields,
		groups=g.media_archive.config['requirable_groups'],
		medium=medium,
	)

@media_archive.route('/' + "<regex('([a-zA-Z0-9_\-]+)'):medium_id>/build")
def generate_summaries(medium_id):
	medium = g.media_archive.require_medium(id_to_md5(medium_id))

	if not g.media_archive.accounts.current_user_has_global_group('manager'):
		if MediumStatus.ALLOWED != medium.status:
			abort(403)
		if medium.owner_uuid != g.media_archive.accounts.current_user.uuid:
			abort(403)

	g.media_archive.generate_medium_summaries(medium)

	return redirect(url_for('media_archive.edit_medium', medium_id=medium.id), 302)

@media_archive.route('/' + "<regex('([a-zA-Z0-9_\-]+)'):medium_id>/remove/summaries")
def remove_summaries(medium_id):
	medium = g.media_archive.require_medium(id_to_md5(medium_id))

	if not g.media_archive.accounts.current_user_has_global_group('manager'):
		if MediumStatus.ALLOWED != medium.status:
			abort(403)
		if medium.owner_uuid != g.media_archive.accounts.current_user.uuid:
			abort(403)

	g.media_archive.remove_medium_summaries(medium)

	return redirect(url_for('media_archive.edit_medium', medium_id=medium.id), 302)

@media_archive.route('/' + "<regex('([a-zA-Z0-9_\-]+)'):medium_id>/remove/original")
def remove_file(medium_id):
	medium = g.media_archive.require_medium(id_to_md5(medium_id))

	if not g.media_archive.accounts.current_user_has_global_group('manager'):
		if MediumStatus.ALLOWED != medium.status:
			abort(403)
		if medium.owner_uuid != g.media_archive.accounts.current_user.uuid:
			abort(403)

	g.media_archive.remove_medium_file(medium)

	return redirect(url_for('media_archive.edit_medium', medium_id=medium.id), 302)

@media_archive.route('/' + "<regex('([a-zA-Z0-9_\-]+)'):medium_id>/remove")
def remove_medium(medium_id):
	medium = g.media_archive.require_medium(id_to_md5(medium_id))

	if not g.media_archive.accounts.current_user_has_global_group('manager'):
		if MediumStatus.ALLOWED != medium.status:
			abort(403)
		if medium.owner_uuid != g.media_archive.accounts.current_user.uuid:
			abort(403)

	g.media_archive.remove_medium(medium)

	return redirect(url_for('media_archive.manage_media'), 302)
