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

@media_archive.route('/search')
def search():
	filter = {
		'without_searchabilities': MediumSearchability.HIDDEN,
		'without_protections': MediumProtection.PRIVATE,
	}
	if g.media_archive.accounts.current_user:
		user_group_bits = []
		if 'global' in g.media_archive.accounts.current_user.permissions:
			user_group_bits.append(g.media_archive.accounts.current_user.permissions['global'].group_bits)
		if 'media' in g.media_archive.accounts.current_user.permissions:
			user_group_bits.append(g.media_archive.accounts.current_user.permissions['media'].group_bits)
		user_inverse_permissions = ~int.from_bytes(
			g.media_archive.accounts.users.combine_groups(bits=user_group_bits),
			'big'
		)
		filter['without_group_bits'] = user_inverse_permissions

	media = g.media_archive.search_media(filter=filter)

	#TODO loop through media and any the current user doesn't have permissions for remove the media id

	return render_template(
		'search.html',
		media=media,
	)

@media_archive.route('/manage')
def manage():
	filter = {}

	if not g.media_archive.accounts.has_global_group(g.media_archive.accounts.current_user, 'manager'):
		# contributor manage self
		g.media_archive.accounts.require_global_group('contributor')
		filter['owner_uuids'] = g.accounts.current_user.uuid

	media = g.media_archive.search_media(filter=filter)

	return render_template(
		'search.html',
		media=media,
	)

@media_archive.route('/fetch/<medium_filename>')
def protected_medium_file(medium_filename):
	import os

	if 1 == medium_filename.count('.'):
		media_path = os.path.join(g.media_archive.config['media_path'], 'protected')
	else:
		media_path = os.path.join(g.media_archive.config['summaries_path'], 'protected')

	pieces = medium_filename.split('.')
	if 2 > len(pieces):
		abort(404, {'message': 'medium_not_found'})

	medium_id = pieces[0]
	medium = g.media_archive.require_medium(id_to_md5(medium_id))

	# trying to access nonprotected medium through protected medium path
	if MediumProtection.NONE == medium.protection:
		abort(400)

	g.media_archive.require_access(medium)

	media_path = os.path.join(g.media_archive.config['media_path'], 'protected')

	if not os.path.exists(os.path.join(media_path, medium_filename)):
		abort(404, {'message': 'medium_not_found'})

	g.no_store = True

	from flask import send_from_directory

	return send_from_directory(media_path, medium_filename, mimetype=medium.mime, conditional=True)

@media_archive.route('/file/<medium_filename>')
def medium_file(medium_filename):
	import os

	if 1 == medium_filename.count('.'):
		media_path = os.path.join(g.media_archive.config['media_path'], 'nonprotected')
	else:
		media_path = os.path.join(g.media_archive.config['summaries_path'], 'nonprotected')

	if not os.path.exists(os.path.join(media_path, medium_filename)):
		abort(404, {'message': 'medium_not_found'})

	from flask import send_from_directory

	return send_from_directory(media_path, medium_filename, conditional=True)

@media_archive.route('/' + "<regex('([a-zA-Z0-9_\-]+)'):medium_id>")
def view_medium(medium_id):
	medium = g.media_archive.require_medium(id_to_md5(medium_id))

	g.media_archive.require_access(medium)

	edit_medium = False
	edit_tags = False

	if (
			medium.owner_uuid == g.media_archive.accounts.current_user.uuid
			or g.media_archive.accounts.current_user_has_global_group('manager')
		):
		edit_medium = True
		edit_tags = True
	elif g.media_archive.accounts.current_user_has_global_group('taxonomist'):
		edit_tags = True

	return render_template(
		'view_medium.html',
		medium=medium,
		edit_medium=edit_medium,
		edit_tags=edit_tags,
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

	if 'generate_summaries' in request.form:
		#TODO rebuild summaries
		pass

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

	if 'protection' in request.form:
		#TODO add exception handling here for ValueErrors
		updates['protection'] = request.form['protection'].upper()

	if 'creation_date' in request.form:
		import dateutil.parser
		try:
			creation_time = dateutil.parser.parse(request.form['creation_date'])
		except ValueError:
			#TODO warning for creation time not set
			pass
		else:
			updates['creation_time'] = creation_time.timestamp()

	groups = []
	for group in g.media_archive.accounts.users.available_groups:
		field = 'groups[' + group + ']'
		if field in request.form:
			fields['groups'].append(group)
	if 0 < len(groups):
		updates['group_bits'] = int.from_bytes(
			self.accounts.users.combine_groups(names=groups),
			'big'
		)

	if 0 < len(updates):
		g.media_archive.media.update_medium(medium, **updates)

	#TODO replace medium

	if 0 == len(errors):
		return redirect(url_for('media_archive.edit_medium', medium_id=medium.id), 302)

	for field in ['generate_summaries', 'author_tag', 'filename_tag']:
		fields[field] = (field in request.form)

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

	return redirect(url_for('media_archive.manage'), 302)

@media_archive.route('/mediatest')
def mediatest():
	import os
	from PIL import Image

	source_file = os.path.join('d:/', 'home', 'secretisdead', 'archive', 'programming', 'bomb', 'test.png')
	thumbnail_file = os.path.join('d:/', 'home', 'secretisdead', 'archive', 'programming', 'bomb', 'test.128.png')

	img = Image.open(source_file)
	width = img.width
	height = img.height
	img.thumbnail((128, 128), Image.BICUBIC)
	img.save(thumbnail_file, 'PNG')

	output = 'test.png<br>'
	output += 'original dimensions: ' + str(width) + 'x' + str(height) + '<br>'
	output += 'thumbnail dimensions: ' + str(img.width) + 'x' + str(img.height) + '<br>'

	return output
