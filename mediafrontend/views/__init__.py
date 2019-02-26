from functools import wraps
import time
import hashlib
import base64
import os
from datetime import datetime, timezone
import math
import re
import json

from flask import Blueprint, render_template, abort, request, redirect
from flask import url_for, g, send_from_directory, make_response
import dateutil.parser

from .. import MediaFrontend
from media import MediumStatus, MediumProtection
from accounts.views import require_sign_in
from pagination_from_request import pagination_from_request
from parse_id import generate_or_parse_id

def initialize(
		config,
		accounts,
		access_log,
		engine,
		install=False,
		connection=None,
	):
	g.media = MediaFrontend(
		config,
		accounts,
		access_log,
		engine,
		install=install,
		connection=connection,
	)

	# use default medium and tags file uris if custom uris aren't specified
	if not g.media.config['medium_file_uri']:
		g.media.config['medium_file_uri'] = url_for(
			'media_static.medium_file',
			medium_filename='MEDIUM_FILENAME',
			_external=True,
		).replace('MEDIUM_FILENAME', '{}')
	if not g.media.config['summary_file_uri']:
		g.media.config['summary_file_uri'] = url_for(
			'media_static.summary_file',
			summary_filename='SUMMARY_FILENAME',
			_external=True,
		).replace('SUMMARY_FILENAME', '{}')
	protected_tags_file_uri = url_for(
			'media_static.tags_file',
			tags_filename='TAGS_FILENAME',
			_external=True,
		).replace('TAGS_FILENAME', '{}')
	g.media.config['protected_tags_file_uri'] = protected_tags_file_uri
	if not g.media.config['tags_file_uri']:
		g.media.config['tags_file_uri'] = protected_tags_file_uri

	#TODO limit maximum upload filesize by determining min of server capability and config capability
	pass

# require objects or abort
def require_medium(id):
	try:
		medium = g.media.require_medium(id)
	except ValueError as e:
		abort(404, str(e))
	else:
		return medium

media_static = Blueprint(
	'media_static',
	__name__,
	static_folder='static',
	static_url_path='/static',
)

@media_static.route('/files/<medium_filename>')
def medium_file(medium_filename):
	nonprotected_media_path = os.path.join(
		g.media.config['media_path'],
		'nonprotected',
	)
	if not os.path.exists(
			os.path.join(
				nonprotected_media_path,
				medium_filename,
			)
		):
		abort(404)
	return send_from_directory(
		nonprotected_media_path,
		medium_filename,
		conditional=True,
	)

@media_static.route('/summaries/<summary_filename>')
def summary_file(summary_filename):
	nonprotected_summary_path = os.path.join(
		g.media.config['summaries_path'],
		'nonprotected',
	)
	if not os.path.exists(
			os.path.join(
				nonprotected_summary_path,
				summary_filename,
			)
		):
		abort(404)
	return send_from_directory(
		nonprotected_summary_path,
		summary_filename,
		conditional=True,
	)

@media_static.route('/tags/<tags_filename>')
def tags_file(tags_filename):
	if not os.path.exists(
			os.path.join(
				g.media.config['tags_path'],
				tags_filename,
			)
		):
		abort(404)

	if 'signed_out.json' != tags_filename:
		if not g.media.accounts.current_user:
			abort(401)
		if (
				(
					'contributor.json' == tags_filename
					or 'semantic.json' == tags_filename
				)
				and not g.media.accounts.current_user.has_permission(
					group_names='contributor',
				)
			):
			abort(403)
		if (
				'manager.json' == tags_filename
				and not g.media.accounts.current_user.has_permission(
					group_names='manager',
				)
			):
			abort(403)

	return send_from_directory(
		g.media.config['tags_path'],
		tags_filename,
		conditional=True,
	)

media_supplemental = Blueprint(
	'media_supplemental',
	__name__,
	template_folder='templates',
)

@media_supplemental.route('/media/help')
def help():
	return render_template('media_help.html')

media_api = Blueprint(
	'media_api',
	__name__,
	template_folder='templates',
)

def api_access_not_allowed(medium, owner_or_manager_only=False):
	# return regular non-allowed response code
	# to not expose private or forbidden media
	if 200 != medium.current_user_response_code:
		return '', medium.current_user_response_code
	if owner_or_manager_only:
		# owner or manager only
		if (
				g.media.accounts.current_user != medium.owner_id
				and not g.media.accounts.current_user.has_permission(
					group_names='manager',
				)
			):
			return '', 403
	return False

def api_response_thumbnails(media, response_data=None):
	if not response_data:
		response_data = {'media': {}}
	for medium in media.values():
		response_data['media'][medium.id] = {
			'thumbnail': render_template(
				'medium_thumbnail.html',
				medium=medium,
				no_thumbnail_link=True,
				tiles=True,
				kwargs={},
			).replace(
				'\r',
				'',
			).replace(
				'\n',
				'',
			).replace(
				'\t',
				'',
			),
		}
	return response_data

@media_api.route('/fetch_medium/<medium_filename>')
@require_sign_in
def api_fetch_medium(medium_filename):
	protected_media_path = os.path.join(
		g.media.config['media_path'],
		'protected',
	)
	if not os.path.exists(
			os.path.join(protected_media_path, medium_filename)
		):
		return '', 404
	medium_id = medium_filename.split('.')[0]
	medium = require_medium(medium_id)
	response = api_access_not_allowed(medium)
	if response:
		return '', response
	return send_from_directory(
		protected_media_path,
		medium_filename,
		conditional=True,
	)

@media_api.route('/fetch_summary/<summary_filename>')
@require_sign_in
def api_fetch_summary(summary_filename):
	protected_summaries_path = os.path.join(
		g.media.config['summaries_path'],
		'protected',
	)
	if not os.path.exists(
			os.path.join(protected_summaries_path, summary_filename)
		):
		return '', 404
	medium_id = summary_filename.split('.')[0]
	medium = require_medium(medium_id)
	response = api_access_not_allowed(medium)
	if response:
		return '', response
	return send_from_directory(
		protected_summaries_path,
		summary_filename,
		conditional=True,
	)

@media_api.route('/tags/build', methods=['POST'])
@require_sign_in
def api_build_tag_suggestions():
	if (
			not g.media.accounts.current_user.has_permission(
				group_names='contributor',
			)
			and not g.media.accounts.current_user.has_permission(
				group_names='manager',
			)
		):
		return '', 403
	g.media.build_tag_suggestions()
	return '', 200

@media_api.route('/tags/<mode>', methods=['POST'])
@require_sign_in
def api_tags(mode):
	if mode not in ['set', 'add', 'remove']:
		return '', 400
	for field in ['medium_ids', 'tags']:
		if field not in request.form:
			return '', 400
	medium = require_medium(request.form['medium_ids'].split(',')[0])
	response = api_access_not_allowed(medium, owner_or_manager_only=True)
	tags = g.media.tag_string_to_list(request.form['tags'])
	if response:
		return '', response
	if 'set' == mode:
		g.media.set_tags(medium.id, tags)
	elif 'add' == mode:
		g.media.add_tags(medium.id, tags)
	elif 'remove' == mode:
		g.media.remove_tags(medium.id, tags)
	# refetch after changes
	media = g.media.search_media(filter={'ids':medium.id_bytes})
	g.media.populate_media_covers(media)
	response_data = api_response_thumbnails(media)
	r = make_response(json.dumps(response_data))
	r.mimetype = 'application/json'
	return r, 200

@media_api.route('/medium/upload', methods=['POST'])
@require_sign_in
def api_upload_medium():
	if not g.media.accounts.current_user.has_permission(
			group_names='contributor',
		):
		return '', 403
	if 'view_endpoint' not in request.form:
		return '', 400
	return upload_media(request.form['view_endpoint'], api_request=True)

@media_api.route('/medium/edit', methods=['POST'])
@require_sign_in
def api_edit_medium():
	if 'medium_ids' not in request.form:
		return '', 400
	medium = require_medium(request.form['medium_ids'].split(',')[0])
	response = api_access_not_allowed(medium, owner_or_manager_only=True)
	if response:
		return '', response
	errors, medium = process_edit_medium(medium)
	if errors:
		# no need to return robust errors since only thumbnail class changes
		return '', 400
	# refetch after changes
	media = g.media.search_media(filter={'ids': medium.id_bytes})
	g.media.populate_media_covers(media)
	response_data = api_response_thumbnails(media)
	r = make_response(json.dumps(response_data))
	r.mimetype = 'application/json'
	return r, 200

@media_api.route('/medium/generate_summaries', methods=['POST'])
@require_sign_in
def api_generate_medium_summaries():
	if 'medium_ids' not in request.form:
		return '', 400
	medium = require_medium(request.form['medium_ids'].split(',')[0])
	response = api_access_not_allowed(medium, owner_or_manager_only=True)
	if response:
		return '', response
	# catch everything here and return generic error if something goes wrong
	try:
		g.media.generate_medium_summaries(medium)
	except:
		return '', 400
	# refetch after changes
	media = g.media.search_media(filter={'ids':medium.id_bytes})
	g.media.populate_media_covers(media)
	response_data = api_response_thumbnails(media)
	r = make_response(json.dumps(response_data))
	r.mimetype = 'application/json'
	return r, 200

@media_api.route('/generate_set', methods=['POST'])
def api_generate_media_set():
	if 'medium_ids' not in request.form:
		return '', 400
	medium_ids = request.form['medium_ids'].split(',')
	if not medium_ids:
		return '', 400
	media = g.media.search_media(filter={'ids': medium_ids})
	for medium in media.values():
		response = api_access_not_allowed(medium, owner_or_manager_only=True)
		if response:
			return '', response
	set_tags = []
	if 'sync' not in request.form:
		new_set_tag, new_set_tag_bytes = generate_or_parse_id(None)
		set_tags = 'set:' + new_set_tag
	else:
		if not media:
			return '', 400
		for medium in media.values():
			if 'sets' in medium.semantic_tags:
				for set in medium.semantic_tags['sets']:
					if 'set:' + set not in set_tags:
						set_tags.append('set:' + set)
	g.media.remove_tags(medium_ids, set_tags)
	g.media.add_tags(medium_ids, set_tags)
	g.media.build_tag_suggestions()
	# refetch after changes
	media = g.media.search_media(filter={'ids': medium_ids})
	g.media.populate_media_covers(media)
	response_data = api_response_thumbnails(media)
	r = make_response(json.dumps(response_data))
	r.mimetype = 'application/json'
	return r, 200

@media_api.route('/medium/remove', methods=['POST'])
@require_sign_in
def api_remove_medium():
	if 'medium_ids' not in request.form:
		return '', 400
	medium = require_medium(request.form['medium_ids'].split(',')[0])
	response = api_access_not_allowed(medium, owner_or_manager_only=True)
	if response:
		return '', response
	g.media.remove_medium(medium)
	r = make_response(
		json.dumps(
			{
				'media': {
					medium.id: {
						'remove': True,
					}
				}
			}
		)
	)
	r.mimetype = 'application/json'
	return r, 200

#TODO i don't really need these but maybe add later for completeness
#TODO api delete summary files
#TODO api delete original file

def parse_submitted_groups():
	groups = []
	for group in g.media.config['requirable_groups']:
		field = 'group_' + group
		if field in request.form:
			groups.append(group)
	return groups

def upload_media(view_endpoint, api_request=False):
	fields = {
		'upload_uri': '',

		'groups': [],

		'generate_summaries': g.media.config['upload_defaults']['generate_summaries'],
		'owner_id': g.media.accounts.current_user.id,
		'status': 'allowed',
		'searchability': g.media.config['upload_defaults']['searchability'],
		'protection': g.media.config['upload_defaults']['protection'],
		'creation_date': '',

		'author_tag': g.media.config['upload_defaults']['author_tag'],
		'filename_tag': g.media.config['upload_defaults']['filename_tag'],
		'tags': '',
	}
	contributors = []
	if (
			g.media.accounts.current_user
			and g.media.accounts.current_user.has_permission(
				group_names='manager',
			)
		):
		contributors = g.media.get_contributors()
	if 'POST' != request.method:
		if api_request:
			return '', 405
		return render_template(
			'upload_media.html',
			fields=fields,
			contributors=contributors,
			medium=None,
			view_endpoint=view_endpoint,
		)
	uploader_id = ''
	if g.media.accounts.current_user:
		uploader_id = g.media.accounts.current_user.id
	upload_opts = {}
	if 'file_uri' in request.form and request.form['file_uri']:
		upload_opts['file_uri'] = request.form['file_uri']
	elif 'file_upload' in request.files:
		upload_opts['file_upload'] = request.files['file_upload']
	errors, filename, medium = g.media.upload(
		request.remote_addr,
		uploader_id,
		**upload_opts,
	)

	if not errors:
		errors, medium = process_edit_medium(medium)

	if errors:
		# api request
		if api_request:
			if 'Medium already exists' in errors:
				r = make_response(
					json.dumps(
						{
							'errors': errors,
							'view_uri': url_for(view_endpoint, medium_id=medium.id),
						}
					)
				)
				r.mimetype = 'application/json'
				return r, 409
			r = make_response(json.dumps({'errors': errors}))
			r.mimetype = 'application/json'
			return r, 400
		fields['groups'] = parse_submitted_groups()
		for key in fields.keys():
			if key in request.form:
				fields[key] = request.form[key]
		return render_template(
			'upload_media.html',
			errors=errors,
			fields=fields,
			contributors=contributors,
			medium=medium,
			view_endpoint=view_endpoint,
		)
	medium.owner = g.media.accounts.get_user(medium.owner_id)

	# initial tags
	tags = []
	if (
			'author_tag' in request.form
			and medium.owner
			and medium.owner.display
		):
		tags.append('author:' + medium.owner.display)

	if 'filename_tag' in request.form and filename:
		tags.append('filename:' + filename)

	if 'tags' in request.form:
		tags += g.media.tag_string_to_list(request.form['tags'])

	if tags:
		g.media.add_tags(medium.id_bytes, tags)
		# non-api upload should build tags after upload
		# api will call build tags separately after all uploads finish
		if not api_request:
			g.media.build_tag_suggestions()

	# api request
	if api_request:
		thumbnail = render_template(
			'medium_thumbnail.html',
			medium=medium,
			override_endpoint=view_endpoint,
			tags_query='',
			tiles=False,
			kwargs={},
		)
		r = make_response(json.dumps({'thumbnail': thumbnail}))
		r.mimetype = 'application/json'
		return r, 200
	return redirect(
		url_for(view_endpoint, medium_id=medium.id),
		code=303,
	)

def process_edit_medium(medium, ignore_replacement=True):
	if not ignore_replacement:
		# process edit media replacement file
		replacement_opts = {}
		if 'file_uri' in request.form and request.form['file_uri']:
			replacement_opts['file_uri'] = request.form['file_uri']
		elif 'file_upload' in request.files:
			replacement_opts['file_upload'] = request.files['file_upload']
		if replacement_opts:
			errors, filename, replacement_medium = g.media.upload(
				request.remote_addr,
				medium.owner_id,
				**replacement_opts,
			)
			if errors:
				return errors, replacement_medium
			# update with existing medium properties
			g.media.update_medium(
				replacement_medium.id_bytes,
				creation_time=medium.creation_time,
				owner_id=medium.owner_id,
				status=medium.status,
				protection=medium.protection,
				searchability=medium.searchability,
				group_bits=medium.group_bits,
				focus=medium.focus,
			)
			# copy existing tags from original medium
			g.media.add_tags(replacement_medium.id, medium.tags)
			#TODO get likes for original medium
			#TODO add them to replacement medium
			g.media.remove_medium(medium)
			medium = replacement_medium

	errors = []
	updates = {}
	# no need for manager checks here
	# since the actual media.update_medium does it
	if 'owner_id' in request.form:
		if not request.form['owner_id']:
			owner = g.media.accounts.current_user
		else:
			owner = g.media.accounts.get_user(request.form['owner_id'])
		if not owner:
			#TODO warning about owner not set?
			#errors.append('Specified owner user not found')
			pass
		else:
			#TODO only allow contributors to be assigned as owner?
			#TODO probably it's fine if any valid user id is allowed
			#TODO even if the select in the upload form is only contributors
			updates['owner_id'] = owner.id_bytes
	for field in [
			'status',
			'searchability',
			'protection',
		]:
		if field in request.form:
			updates[field] = request.form[field].upper()
	if 'creation_date' in request.form:
		if not request.form['creation_date']:
			creation_time = int(time.time())
		else:
			try:
				parsed = creation_time = dateutil.parser.parse(
					request.form['creation_date']
				)
			except ValueError:
				#TODO warning about creation date not set?
				#errors.append('Invalid creation date format')
				pass
			else:
				updates['creation_time'] = int(parsed.timestamp())
	if 'focus' in request.form:
		updates['focus'] = float(request.form['focus'])

	if errors:
		return errors, medium

	groups = parse_submitted_groups()
	updates['group_bits'] = 0
	if groups:
		updates['group_bits'] = int.from_bytes(
			g.media.accounts.combine_groups(names=groups),
			'big'
		)

	# catch everything here and return generic error if something goes wrong
	try:
		g.media.update_medium(medium.id, **updates)
	except:
		errors.append('Problem updating medium')
		return errors, medium

	# refetch updated medium
	medium = g.media.get_medium(medium.id_bytes)

	if 'generate_summaries' in request.form:
		# catch everything here and return generic error if something goes wrong
		try:
			g.media.generate_medium_summaries(medium)
		except:
			#TODO actually return error back up
			pass

	# refetch updated medium again to populate uris?
	medium = g.media.get_medium(medium.id_bytes)

	#TODO mass management would flood the logs if edits are logged
	#TODO think of some better way to log manual edits and maybe single log for mass edits?
	#subject_id = ''
	#if g.media.accounts.current_user:
	#	subject_id = g.media.accounts.current_user.id_bytes
	#g.media.access_log.create_log(
	#	scope='edit_medium',
	#	subject_id=subject_id,
	#	object_id=medium.id_bytes,
	#)

	return errors, medium

def view_medium(
		medium,
		tags_query='',
		management_mode=False,
		prev_medium_id='',
		next_medium_id='',
		**kwargs
	):
	g.media.populate_medium_like_data(medium)
	g.media.populate_media_covers(medium)
	# manually turn on management mode if user is owner or manager
	if (
			not management_mode
			and g.media.accounts.current_user
			and g.media.accounts.current_user.id == medium.owner_id
		):
		management_mode = True
	if not management_mode and 200 != medium.current_user_response_code:
		if 402 == medium.current_user_response_code:
			return render_template(
				'view_premium_medium.html',
				medium=medium,
				prev_medium_id=prev_medium_id,
				next_medium_id=next_medium_id,
				kwargs=kwargs,
			), 402
		elif 403 == medium.current_user_response_code:
			return render_template(
				'view_protected_medium.html',
				medium=medium,
				prev_medium_id=prev_medium_id,
				next_medium_id=next_medium_id,
				kwargs=kwargs,
			), 403
		elif 404 == medium.current_user_response_code:
			abort(404, 'Medium not found')
		else:
			abort(medium.current_user_response_code)
	else:
		if 'mode' in request.args:
			if 'edit' == request.args['mode']:
				g.media.populate_media_users(medium)
				fields = {
					'focus': medium.focus,
					'groups': medium.groups,
					'owner_id': medium.owner_id,
					'status': str(medium.status).lower(),
					'searchability': str(medium.searchability).lower(),
					'protection': str(medium.protection).lower(),
					'creation_date': medium.creation_datetime.strftime(
						'%Y-%m-%dT%H:%M:%S.%f%z'
					),
				}
				contributors = []
				if (
						g.media.accounts.current_user
						and g.media.accounts.current_user.has_permission(
							group_names='manager',
						)
					):
					contributors = g.media.get_contributors()
				if 'POST' != request.method:
					return render_template(
						'edit_medium.html',
						fields=fields,
						medium=medium,
						tags_query=tags_query,
						contributors=contributors,
						kwargs=kwargs,
					)
				errors, edited_medium = process_edit_medium(
					medium,
					ignore_replacement=False,
				)
				if errors:
					return render_template(
						'edit_medium.html',
						errors=errors,
						fields=fields,
						medium=medium,
						tags_query=tags_query,
						contributors=contributors,
						kwargs=kwargs,
					)
				medium = edited_medium
			elif 'delete_summaries' == request.args['mode']:
				g.media.delete_medium_summaries(medium)
			elif 'delete_original' == request.args['mode']:
				if 'confirm' not in request.args:
					return render_template(
						'confirm_delete_medium_original_file.html',
						medium_id=medium.id,
						tags_query=tags_query,
						kwargs=kwargs,
					)
				g.media.delete_medium_file(medium)
			elif 'remove' == request.args['mode']:
				if 'confirm' not in request.args:
					return render_template(
						'confirm_remove_medium.html',
						medium_id=medium.id,
						tags_query=tags_query,
						kwargs=kwargs,
					)
				g.media.remove_medium(medium)
				# return to current search
				return redirect(
					url_for(
						request.endpoint,
						tags_query=tags_query,
						**kwargs
					),
					code=303,
				)
			# return to edit page
			return redirect(
				url_for(
					request.endpoint,
					medium_id=medium.id,
					tags_query=tags_query,
					mode='edit',
					**kwargs
				),
				code=303,
			)
		# edit tags manual submit
		if 'POST' == request.method and 'edit_tags' in request.form:
			g.media.set_tags(
				medium.id_bytes,
				g.media.tag_string_to_list(request.form['edit_tags']),
			)
			g.media.build_tag_suggestions()
			return redirect(request.url, code=303)

		# add like
		if 'like' in request.args:
			if not g.accounts.current_user:
				abort(401)
			if 'add' == request.args['like']:
				if g.media.per_medium_like_cooldown(
						medium.id,
						g.accounts.current_user.id,
					):
					abort(
						429,
						'Please wait a bit before adding another like to this medium',
					)
				g.media.create_like(medium.id_bytes, g.media.accounts.current_user.id_bytes)
			else:
				# attempt to remove the most recent like from this medium by the current user
				likes = g.media.search_likes(
					filter={
						'user_ids': g.media.accounts.current_user.id_bytes,
						'medium_ids': medium.id_bytes,
					},
					perpage=1,
				)
				if not likes.values():
					abort(400)
				g.media.delete_like(
					likes.values()[0].id,
					subject_id=g.accounts.current_user.id,
				)
			if 'redirect_uri' in request.args:
				return redirect(request.args['redirect_uri'], code=303)
			return redirect(
				url_for(
					request.endpoint,
					medium_id=medium.id,
					tags_query=tags_query,
					**kwargs
				),
				code=303,
			)
	g.media.populate_medium_contents(medium)
	g.media.populate_medium_sets(medium)
	visible_tags = 0
	clutter_tags = []
	for tag in medium.tags:
		clutter_tag = False
		for clutter_tag_prefix in g.media.config['clutter_tag_prefixes']:
			if clutter_tag_prefix == tag[:len(clutter_tag_prefix)]:
				clutter_tag = True
				clutter_tags.append(tag)
				break
		if not clutter_tag:
			visible_tags += 1
	return render_template(
		'view_medium.html',
		medium=medium,
		tags_query=tags_query,
		management_mode=management_mode,
		prev_medium_id=prev_medium_id,
		next_medium_id=next_medium_id,
		visible_tags=visible_tags,
		clutter_tags=clutter_tags,
		tag_suggestion_lists=g.media.get_tag_suggestion_lists(
			management_mode=management_mode,
		),
		kwargs=kwargs,
	)

def search_results_rss(results, media_endpoint='', tags_query='', **kwargs):
	if tags_query:
		page_uri = url_for(
			media_endpoint,
			tags=tags_query,
			_external=True,
			**kwargs
		)
	else:
		page_uri = url_for(
			media_endpoint,
			_external=True,
			**kwargs
		)
	#TODO a more robust description with selected filters goes here
	feed_description = 'what'
	rss = (
		'<?xml version="1.0" encoding="UTF-8" ?>'
			+ '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">'
			+ '<channel>'
				+ '<title>persephone media archive</title>'
				+ '<generator>persephone (0.0.1; @secretisdead)</generator>'
				+ '<link>' + page_uri + '</link>'
				+ '<atom:link href="'
					+ request.url + '" rel="self" type="application/rss+xml" />'
				+ '<description>' + feed_description + '</description>'
	)
	for result in results.values():
		if 200 != result.current_user_response_code:
			continue
		description = render_template(
			'medium_summary.html',
			medium=result,
			media_endpoint=media_endpoint,
			kwargs=kwargs,
		)
		tags = []
		for tag in result.tags:
			if (
					'title:' != tag[:6]
					and 'author:' != tag[:7]
				):
				tags.append('#' + tag)
			#rss += '<category>' + tag + '</category>'
		if tags:
			description += '<p>' + ' '.join(tags) + '</p>'
		link = url_for(
			media_endpoint,
			medium_id=result.id,
			_external=True,
			**kwargs
		)
		guid = result.id
		pubdate = result.creation_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f%z')
		rss += (
			'<item>'
				+ '<link>' + link + '</link>'
				+ '<description><![CDATA[' + description + ']]></description>'
				+ '<guid>' + guid + '</guid>'
				+ '<pubDate>' + pubdate + '</pubDate>'
		)
		if 'title' in result.semantic_tags:
			rss += '<title>' + result.semantic_tags['title'] + '</title>'
		rss += '<author>'
		if 'author' in result.semantic_tags:
			rss += result.semantic_tags['author']
		rss += '</author>'
		rss += '</item>'
	rss += '</channel></rss>'
	r = make_response(rss, 200)
	r.headers['Content-type'] = 'text/xml; charset=utf-8'
	return r

def search_media(
		header=None,
		search_field=True,
		hide_tags_this_page=False,
		management_mode=False,
		medium_id=None,
		omit_future=True,
		override_tags={},
		override_filters={},
		rss=False,
		rss_endpoint='',
		rss_media_endpoint='',
		**kwargs
	):
	tags_query = ''
	slideshow = False
	if 'tags' in request.args:
		tags_query = request.args['tags']
		slideshow = True

	tags = g.media.tag_string_to_list(tags_query)
	limited_tags = []
	for tag in tags:
		if g.media.config['maximum_search_tags'] == len(limited_tags):
			break
		limited_tags.append(tag)
	tags = limited_tags
	if 'sort:random' in tags:
		sort_tags = []
		for tag in tags:
			if 'sort:' == tag[:5]:
				sort_tags.append(tag)
		for tag in sort_tags:
			tags.remove(tag)
		seed = g.media.generate_random_seed()
		tags.append('sort:random:' + seed)
		return redirect(url_for(request.endpoint, tags='#'.join(tags)), code=303)
	if override_tags:
		if 'tags' in override_tags:
			tags = override_tags['tags']
		else:
			if 'remove_tags' in override_tags:
				for tag in override_tags['remove_tags']:
					if tag in tags:
						tags.remove(tag)
			if 'add_tags' in override_tags:
				tags += override_tags['add_tags']
	if omit_future:
		current_atom_datetime = datetime.fromtimestamp(
			time.time(),
			timezone.utc
		).strftime('%Y-%m-%dT%H:%M:%S.%f%z')
		tags.append('created before:' + current_atom_datetime)
	filter = {}
	if tags:
		filter = g.media.parse_search_tags(tags, management_mode)

	default_sort = 'creation_time'
	if 'default_sort' in override_filters:
		default_sort = override_filters['default_sort']
		
	pagination = {
		'sort': default_sort,
		'order': 'desc',
		'page': 0,
		'perpage': 32,
	}
	if 'sort' in filter:
		pagination['sort'] = filter['sort']
	if 'order' in filter:
		pagination['order'] = filter['order']
	if 'perpage' in filter:
		pagination['perpage'] = filter['perpage']
	if 'page' in request.args:
		pagination['page'] = int(request.args['page'])

	for key, value in override_filters.items():
		filter[key] = value

	# view medium/slideshow mode for this search
	if medium_id:
		medium = require_medium(medium_id)
		# get adjacent media ids
		prev_medium_id = ''
		next_medium_id = ''
		if slideshow:
			prev_medium, next_medium = g.media.get_adjacent_media(
				medium,
				filter=filter,
				sort=pagination['sort'],
				order=pagination['order'],
				page=pagination['page'],
				perpage=pagination['perpage'],
			)
			if prev_medium:
				prev_medium_id = prev_medium.id
			if next_medium:
				next_medium_id = next_medium.id
		return view_medium(
			medium,
			tags_query=tags_query,
			management_mode=management_mode,
			prev_medium_id=prev_medium_id,
			next_medium_id=next_medium_id,
			**kwargs
		)

	if 'random' in request.args:
		seed = g.media.generate_random_seed()
		media = g.media.search_media(
			filter=filter,
			sort='random:' + seed,
			page=0,
			perpage=1,
		)
		if not media.values():
			return redirect(
				url_for(
					request.endpoint,
					tags=tags_query,
					**kwargs
				),
				code=303,
			)

		return redirect(
			url_for(
				request.endpoint,
				medium_id=media.values()[0].id,
				tags=tags_query + '#sort:random:' + seed,
				**kwargs
			),
			code=303,
		)

	# use external uris for rss readers
	if rss:
		g.media.external_uris = True

	results = g.media.search_media(filter=filter, **pagination)
	total_results = g.media.count_media(filter=filter)

	if rss:
		return search_results_rss(
			results,
			media_endpoint=rss_media_endpoint,
			tags_query=tags_query,
			**kwargs
		)

	g.media.populate_media_covers(results)

	contributors = []
	if management_mode:
		contributors = g.media.get_contributors()
	else:
		#TODO can conditionally do things here for some tiny efficiency?
		pass

	tags_this_page = []
	if not hide_tags_this_page:
		for medium in results.values():
			for tag in medium.tags:
				if tag in tags_this_page:
					continue
				clutter_tag = False
				for clutter_tag_prefix in g.media.config['clutter_tag_prefixes']:
					if clutter_tag_prefix == tag[:len(clutter_tag_prefix)]:
						clutter_tag = True
						break
				if not clutter_tag:
					tags_this_page.append(tag)

	tag_suggestion_lists = g.media.get_tag_suggestion_lists(
		management_mode=management_mode,
		search=True,
	)

	rss_url = ''
	if rss_endpoint:
		if tags_query:
			rss_url = url_for(rss_endpoint, tags=tags_query, **kwargs)
		else:
			rss_url = url_for(rss_endpoint, **kwargs)

	return render_template(
		'search_media.html',
		results=results,
		pagination=pagination,
		total_results=total_results,
		total_pages=math.ceil(total_results / pagination['perpage']),
		tags_query=tags_query,
		header=header,
		search_field=search_field,
		tag_suggestion_lists=tag_suggestion_lists,
		tags_this_page=tags_this_page,
		management_mode=management_mode,
		contributors=contributors,
		re=re,
		rss_url=rss_url,
		kwargs=kwargs,
	)

def tags_list(search_endpoint=''):
	if (
			'mode' in request.args
			and 'tag' in request.args
			and request.args['tag']
		):
		tag = request.args['tag']
		if 'redirect_uri' in request.args:
			redirect_uri = request.args['redirect_uri']
		else:
			redirect_uri = url_for(request.endpoint)
		if 'remove' == request.args['mode']:
			if 'confirm' not in request.args:
				return render_template(
					'confirm_remove_tag.html',
					tag=tag,
					redirect_uri=redirect_uri,
				)
			g.media.delete_tags(tag)
		else:
			media = g.media.search_media(filter={'with_tags': tag})
			medium_ids = list(media.keys())
			if 'replace' == request.args['mode']:
				if (
						'replacement' not in request.args
						or not request.args['replacement']
					):
					return render_template(
						'replace_tag.html',
						tag=request.args['tag'],
						redirect_uri=redirect_uri,
					)
				g.media.delete_tags(tag)
				g.media.add_tags(medium_ids, request.args['replacement'])
			elif 'accompany' == request.args['mode']:
				if (
						'accompaniment' not in request.args
						or not request.args['accompaniment']
					):
					return render_template(
						'accompany_tag.html',
						tag=request.args['tag'],
						redirect_uri=redirect_uri,
					)
				g.media.add_tags(medium_ids, request.args['accompaniment'])
		return redirect(
			redirect_uri,
			code=303,
		)

	search = {
		'tag': '',
	}
	for field in search:
		if field in request.args:
			search[field] = request.args[field]

	filter = {}
	escape = lambda value: (
		value
			.replace('\\', '\\\\')
			.replace('_', '\_')
			.replace('%', '\%')
			.replace('-', '\-')
	)
	for field, value in search.items():
		if not value:
			continue
		if 'tag' == field:
			filter['tags'] = '%' + escape(value) + '%'

	pagination = pagination_from_request('count', 'desc', 0, 32)

	total_results = g.media.count_unique_tags(filter=filter)
	results = g.media.search_tag_counts(filter=filter, **pagination)

	results_dict = {}
	i = 0
	for result in results:
		results_dict.update({i: result})
		i += 1
	return render_template(
		'tags_list.html',
		results=results_dict,
		search=search,
		pagination=pagination,
		total_results=total_results,
		total_pages=math.ceil(total_results / pagination['perpage']),
		search_endpoint=search_endpoint,
	)
