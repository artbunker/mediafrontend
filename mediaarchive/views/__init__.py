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
		return redirect(url_for('media_archive.view_medium', medium_id=medium.id))

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

	media = g.media_archive.media.search_media(filter=filter)

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
	g.media_archive.accounts.require_sign_in()

	import os

	media_path = os.path.join(g.media_archive.config['media_path'], 'protected')

	pieces = medium_filename.split('.')
	if 2 > len(pieces):
		abort(404, {'message': 'medium_not_found'})
	medium_id = pieces[0]
	medium = g.media_archive.require_medium(id_to_md5(medium_id))
	if medium.group_bits:
		if not (
				g.media_archive.accounts.users.has_permissions(
					g.media_archive.accounts.current_user,
					'global',
					medium.group_bits
				)
			):
			for premium_group in g.media_archive.config['premium_groups']:
				premium_group_bit = g.media_archive.accounts.users.group_name_to_bit(premium_group)
				if (
						g.media_archive.accounts.users.contains_all_group_bits(
							medium.group_bits,
							premium_group_bit
						)
					):
					if (
							not g.media_archive.accounts.has_global_group(
								g.media_archive.accounts.current_user,
								premium_group
							)
						):
						abort(402, {'message': 'premium_media', 'group': premium_group})
			abort(403, {'message': 'medium_protected'})

	media_path = os.path.join(g.media_archive.config['media_path'], 'protected')

	if not os.path.exists(os.path.join(media_path, medium_filename)):
		abort(404, {'message': 'medium_not_found'})

	from flask import send_from_directory

	return send_from_directory(media_path, medium_filename)

@media_archive.route('/file/<medium_filename>')
def medium_file(medium_filename):
	import os

	media_path = os.path.join(g.media_archive.config['media_path'], 'nonprotected')

	if not os.path.exists(os.path.join(media_path, medium_filename)):
		abort(404, {'message': 'medium_not_found'})

	from flask import send_from_directory

	return send_from_directory(media_path, medium_filename)

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
		'view.html',
		medium=medium,
		edit_medium=edit_medium,
		edit_tags=edit_tags,
	)

@media_archive.route('/' + "<regex('([a-zA-Z0-9_\-]+)'):medium_id>/edit", methods=['GET', 'POST'])
def edit_medium(medium_id):
	medium = g.media_archive.require_medium(id_to_md5(medium_id))

	if not g.media_archive.accounts.has_global_group(g.media_archive.accounts.current_user, 'manager'):
		g.media_archive.accounts.require_global_group('contributor')
		if medium.owner_uuid != g.media_archive.accounts.current_user.uuid:
			abort(404, {'message': 'medium_not_found'})

	return 'edit ' + medium_id

@media_archive.route('/' + "<regex('([a-zA-Z0-9_\-]+)'):medium_id>/remove")
def remove_medium(medium_id):
	g.media_archive.require_medium(id_to_md5(medium_id))

	return 'remove ' + medium_id

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
