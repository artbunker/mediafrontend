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

@media_archive.route('/upload')
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

		'generate_summaries': g.media_archive.config['defaults']['generate_summaries'],
		'owner_id': g.media_archive.accounts.current_user.id,
		'searchability': g.media_archive.config['defaults']['searchability'],
		'protection': g.media_archive.config['defaults']['protection'],
		'creation_date': '',

		'author_tag': g.media_archive.config['defaults']['author_tag'],
		'filename_tag': g.media_archive.config['defaults']['filename_tag'],
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
		)

	#TODO upload processing

	medium_id = 'what'

	if 0 == len(errors):
		return redirect(url_for('media_archive.view_medium', medium_id=medium_id))

	return render_template(
		'upload.html',
		errors=errors,
		manager=manager,
		contributors=contributors,
		fields=fields,
		groups=g.media_archive.config['requirable_groups'],
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
	print(media)

	return 'regular media search'

@media_archive.route('/manage')
def manage():
	filter = {}

	output = 'manage media'

	if not g.media_archive.accounts.has_global_group(g.media_archive.accounts.current_user, 'manager'):
		output = 'contributor manage self'
		g.media_archive.accounts.require_global_group('contributor')
		filter['owner_uuids'] = g.accounts.current_user.uuid

	media = g.media_archive.media.search_media(filter=filter)
	print('media:')
	print(media)

	return output

@media_archive.route('/' + "<regex('([a-zA-Z0-9_\-]+)'):medium_id>")
def view_medium(medium_id):
	medium = g.media_archive.require_medium(id_to_md5(medium_id))

	return 'view ' + medium.id

@media_archive.route('/' + "<regex('([a-zA-Z0-9_\-]+)'):medium_id>/edit", methods=['GET', 'POST'])
def edit_medium(medium_id):
	medium = g.media_archive.require_medium(medium_id)

	if not g.media_archive.accounts.has_global_group(g.media_archive.accounts.current_user, 'manager'):
		g.media_archive.accounts.require_global_group('contributor')
		if medium.owner_uuid != g.media_archive.accounts.current_user.uuid:
			abort(404, {'message': 'medium_not_found'})

	return 'edit ' + medium_id

@media_archive.route('/' + "<regex('([a-zA-Z0-9_\-]+)'):medium_id>/remove")
def remove_medium(medium_id):
	#g.media_archive.require_medium(medium_id)

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
