'use strict';

import { TagsField } from './tagsfield.js';
import { disallowed_edit_tag_prefixes } from './disallowed_edit_tag_prefixes.js';
import { autocopy } from './autocopy.js';
import { add_hover_preview } from './add_hover_preview.js';

document.documentElement.classList.add('scripts_enabled');

class Manage {
	constructor() {
		this.drawer = document.querySelector('#manage_drawer');
		this.panels = document.querySelector('#manage_panels');
		this.active_panel = document.querySelector('#manage_active_panel');
		this.form = document.querySelector('#manage_form');
		this.keys = {
			exit_management: 'Escape',
			toggle_management: 'e',
			add_tags: 't',
			searchability: 'v',
			generate_set: 'g',
			select_all: 'a',
			select_none: 'd',
			remove: 'Delete',
			select_add: 'Shift',
			select_negate: 'Control',
		};
		this.select_add = false;
		this.select_negate = false;

		// listener for shortcut keys
		window.addEventListener('keydown', e => {
			if (this.keys.exit_management == e.key) {
				if (document.body.classList.contains('active_panel')) {
					this.hide_panels();
					return;
				}
				this.exit_management();
				return;
			}
			if (this.keys.select_add == e.key) {
				this.select_add = true;
			}
			if (this.keys.select_negate == e.key) {
				this.select_negate = true;
			}
			// ignore other management keys if in an input
			if ('INPUT' == document.activeElement.tagName) {
				return;
			}
			if (this.keys.toggle_management == e.key) {
				this.toggle_management();
				return;
			}
			// ignore following shortcut keys if not in management mode
			if (!document.body.classList.contains('managing_media')) {
				return;
			}
			if (this.keys.select_all == e.key) {
				this.select_all();
				return;
			}
			if (this.keys.select_none == e.key) {
				this.select_none();
				return;
			}
			// ignore following shortcut keys if no media are selected
			if (0 == document.body.dataset.selection_total) {
				return;
			}
			if (this.keys.add_tags == e.key) {
				this.add_tags();
			}
			else if (this.keys.searchability == e.key) {
				this.searchability();
			}
			else if (this.keys.generate_set == e.key) {
				this.generate_set();
			}
			else if (this.keys.remove == e.key) {
				this.remove();
			}
		});
		window.addEventListener('keyup', e => {
			if (this.keys.select_add == e.key) {
				this.select_add = false;
			}
			if (this.keys.select_negate == e.key) {
				this.select_negate = false;
			}
		});
		this.selection_total = this.drawer.querySelector('#selection_total');
		this.selection_total.dataset.count = 0;

		// select/deselect listeners to thumbnails
		let thumbnails = document.querySelectorAll('.thumbnail');
		this.iterate_thumbnails(thumbnails, (thumbnail) => {
			thumbnail.addEventListener('click', (e) => {
				if (!document.body.classList.contains('managing_media')) {
					return;
				}
				e.preventDefault();
				e.stopPropagation();
				if (document.body.classList.contains('active_panel')) {
					this.hide_panels();
					return;
				}
				this.toggle_select(e.currentTarget)
				this.update_selection_total();
			});
		});

		// manage topmenu link listener
		let manage_link = document.querySelector('#top_manage');
		manage_link.addEventListener('click', () => {
			this.toggle_management();
		});

		// create tags field
		this.tags_field = new TagsField(
			disallowed_edit_tag_prefixes,
			this.panels.dataset.placeholder,
			this.panels.dataset.removeTag
		);
		// add classes to tags field components
		this.tags_field.preview.classList.add('tags_preview');
		// wrap tags field preview
		this.tags_field.preview_wrapper = document.createElement('div');
		this.tags_field.preview_wrapper.classList.add('tags_preview_wrapper');
		this.tags_field.preview_wrapper.append(this.tags_field.preview);
		// store reference to management in tags field
		this.tags_field.manage = this;
		// save handler
		this.tags_field.save = function() {
			if (this.input.value) {
				// commit any tag still in input
				this.add_tags(this.to_list(this.input.value));
				this.clear_input();
			}
			// current tags in current form tags input
			this.input.parentNode.querySelector('[name="tags"]').value = this.to_string(this.tags_list);
		}.bind(this.tags_field);

		// manage action buttons
		let actions = [
			'owner',
			'creation',
			'build',
			'remove',
			'groups',
			'searchability',
			'protection',
			'generate_set',
			'copy_tags',
			'add_tags',
			'remove_tags',
			'select_all',
			'select_none',
		];
		for (let i = 0; i < actions.length; i++) {
			let action = actions[i];
			let action_button = this.drawer.querySelector('#manage_' + action);
			if (!action_button) {
				continue;
			}
			action_button.addEventListener('click', () => {
				this[action]();
			});
		}
		document.querySelector('#dim').addEventListener('click', (e) => {
			this.hide_panels();
		});

		// drag to select
		this.drag_origin = {
			x: 0,
			y: 0,
		};
		this.blank = document.createElement('img');
		// transparent pixel to hide generated ghost while dragging
		this.blank.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
		this.blank.id = 'blank';
		this.selection_box = document.createElement('span');
		this.selection_box.id = 'selection_box';
		this.hide_selection_box();
		document.body.appendChild(this.blank);
		document.body.appendChild(this.selection_box);
		document.body.addEventListener('dragstart', (e) => {
			if (
				!document.body.classList.contains('managing_media')
				|| document.body.classList.contains('active_panel')
			) {
				return;
			}
			this.show_selection_box();
			e.dataTransfer.setDragImage(this.blank, 0, 0);
			this.drag_origin.x = e.pageX;
			this.drag_origin.y = e.pageY;
		});
		document.body.addEventListener('drag', (e) => {
			if (document.body.classList.contains('active_panel')) {
				return;
			}
			this.update_selection_box(e.pageX, e.pageY);
		});
		document.body.addEventListener('dragend', (e) => {
			e.preventDefault();
			if (document.body.classList.contains('active_panel')) {
				return;
			}
			if (document.body.classList.contains('managing_media')) {
				this.update_selection_box(e.pageX, e.pageY);
				this.selection_from_drag();
			}
			this.hide_selection_box();
		});

		this.form.addEventListener('submit', (e) => {
			e.preventDefault();
			let tags_input = this.form.querySelector('input[name="tags"]');
			if (tags_input) {
				this.tags_field.save();
			}
			let selected = document.querySelectorAll('.selected');
			this.iterate_thumbnails(selected, (thumbnail) => {
				this.api_request(
					'POST',
					this.form.action,
					new FormData(this.form),
					thumbnail
				);
			});
			this.hide_panels();
		});

		// move drawer into body and get initial size
		document.body.append(this.drawer);

		window.addEventListener('resize', () => {
			this.calculate_drawer_spacing();
		});
		this.calculate_drawer_spacing();

		// add listener for leaving page to check if any requests are still processing
		window.addEventListener('beforeunload', e => {
			if (document.querySelector('.processing')) {
				(e || window.event).returnValue = true;
				return true;
			}
		});
	}
	clear_result(thumbnail) {
		thumbnail.classList.remove('success');
		thumbnail.classList.remove('failure');
	}
	toggle_select(thumbnail) {
		this.clear_result(thumbnail);
		thumbnail.classList.toggle('selected');
	}
	select(thumbnail) {
		this.clear_result(thumbnail);
		thumbnail.classList.add('selected');
	}
	deselect(thumbnail) {
		this.clear_result(thumbnail);
		thumbnail.classList.remove('selected');
	}
	hide_selection_box() {
		let items = [
			'blank',
			'selection_box',
		];
		for (let i = 0; i < items.length; i++) {
			let item = items[i];
			this[item].style.display = 'none';
			this[item].style.left = '0';
			this[item].style.top = '0';
			this[item].style.width = '0';
			this[item].style.height = '0';
		}
	}
	show_selection_box() {
		this.blank.style.display = 'inline-block';
		this.blank.style.width = '2px';
		this.blank.style.height = '2px';
		this.selection_box.style.display = 'inline-block';
	}
	update_selection_box(page_x, page_y) {
		if (page_x < this.drag_origin.x) {
			this.selection_box.style.left = page_x + 'px';
			this.selection_box.style.width = this.drag_origin.x - page_x + 'px';
		}
		else {
			this.selection_box.style.left = this.drag_origin.x + 'px';
			this.selection_box.style.width = page_x - this.drag_origin.x + 'px';
		}
		if (page_y < this.drag_origin.y) {
			this.selection_box.style.top = page_y + 'px';
			this.selection_box.style.height = this.drag_origin.y - page_y + 'px';
		}
		else {
			this.selection_box.style.top = this.drag_origin.y + 'px';
			this.selection_box.style.height = page_y - this.drag_origin.y + 'px';
		}
	}
	selection_from_drag() {
		// replace
		if (
			!this.select_add
			&& !this.select_negate
		) {
			this.select_none();
		}
		let r1 = this.selection_box.getBoundingClientRect();
		let thumbnails = document.querySelectorAll('.thumbnail');
		this.iterate_thumbnails(thumbnails, (thumbnail) => {
			let r2 = thumbnail.getBoundingClientRect()
			if (
				!(
					r2.left > r1.right
					|| r2.right < r1.left
					|| r2.top > r1.bottom
					|| r2.bottom < r1.top
				)
			) {
				if (this.select_negate) {
					this.deselect(thumbnail);
				}
				else {
					this.select(thumbnail);
				}
			}
		})
		this.update_selection_total();
	}
	calculate_drawer_spacing() {
		this.drawer.classList.remove('loaded');
		this.drawer.style.height = '';
		let rect = this.drawer.getBoundingClientRect();
		let content = document.querySelector('#content');
		content.style.paddingBottom = 'calc(1em + ' + rect.height + 'px)';
		this.drawer.height = rect.height + 'px';
		this.active_panel.style.bottom = 'calc(1.5em + ' + rect.height + 'px)';
		this.drawer.classList.add('loaded');
		this.set_drawer_height();
	}
	set_drawer_height() {
		if (document.body.classList.contains('managing_media')) {
			this.drawer.style.height = this.drawer.height;
		}
		else {
			this.drawer.style.height = '0';
		}
	}
	enter_management() {
		this.select_none();
		this.hide_panels();
		document.body.classList.add('managing_media');
		this.set_drawer_height();
	}
	exit_management() {
		document.body.classList.remove('managing_media');
		this.select_none();
		this.hide_panels();
		this.set_drawer_height();
	}
	toggle_management() {
		document.body.classList.toggle('managing_media');
		if (document.body.classList.contains('managing_media')) {
			this.enter_management();
		}
		else {
			this.exit_management();
		}
	}
	show_panel(panel) {
		this.hide_panels();
		let panel_el = this.panels.querySelector('#manage_panel_' + panel);
		if (!panel_el) {
			return;
		}
		this.form.insertBefore(panel_el, this.form.firstChild);
		document.body.classList.add('active_panel');
	}
	hide_panels() {
		document.body.classList.remove('active_panel');
		let panels = this.active_panel.querySelectorAll('.manage_panel');
		for (let i = panels.length - 1; 0 <= i; i--) {
			this.panels.appendChild(panels[i]);
		}
	}
	toggle_panel(panel) {
		if (this.panels.querySelector('#manage_panel_' + panel)) {
			this.show_panel(panel);
			return;
		}
		this.hide_panels();
	}
	iterate_thumbnails(thumbnails, cb) {
		let reversed_array = [];
		for (let i = thumbnails.length - 1; 0 <= i; i--) {
			reversed_array.push(thumbnails[i]);
		}
		reversed_array = reversed_array.reverse();
		for (let i = 0; i < reversed_array.length; i++) {
			cb(reversed_array[i]);
		}
	}
	api_request(method, action, fd, thumbnails, cb) {
		let xhr = new XMLHttpRequest();
		if (NodeList !== thumbnails.constructor) {
			thumbnails = [thumbnails];
		}
		let medium_ids = [];
		this.iterate_thumbnails(thumbnails, (thumbnail) => {
			medium_ids.push(thumbnail.dataset.id);
		});
		fd.append('medium_ids', medium_ids);
		xhr.thumbnails = thumbnails;
		xhr.cb = cb;
		fd.append('response_type', 'json');
		xhr.responseType = 'json';
		xhr.onreadystatechange = () => {
			if (xhr.readyState == XMLHttpRequest.DONE) {
				this.iterate_thumbnails(xhr.thumbnails, (thumbnail) => {
					thumbnail.classList.remove('processing');
				});
				if (xhr.cb) {
					xhr.cb();
				}
				if (200 == xhr.status) {
					if (!xhr.response) {
						return;
					}
					if (xhr.response.hasOwnProperty('media')) {
						for (let medium_id in xhr.response.media) {
							let thumbnail = document.querySelector('[data-id="' + medium_id + '"]');
							if (!thumbnail) {
								continue;
							}
							let response_medium = xhr.response.media[medium_id];
							if (response_medium.hasOwnProperty('failure')) {
								thumbnail.classList.add('failure');
								continue;
							}
							if (response_medium.hasOwnProperty('remove')) {
								thumbnail.parentNode.removeChild(thumbnail);
								continue;
							}
							if (response_medium.hasOwnProperty('thumbnail')) {
								// replace thumbnail innerHTML with response thumbnail innerHTML
								// to retain listeners
								let temp = document.createElement('div');
								temp.innerHTML = response_medium.thumbnail;
								//TODO set thumbnail class title style and all data attributes
								thumbnail.innerHTML = temp.querySelector('.thumbnail').innerHTML;
								// if thumbnail has preview then add hover preview listener
								if (thumbnail.dataset.hasOwnProperty('preview')) {
									add_hover_preview(thumbnail);
								}
								continue;
							}
							if (response_medium.hasOwnProperty('summary')) {
								let temp = document.createElement('div');
								temp.innerHTML = response_medium.summary;
								let summary = thumbnail.querySelector('.summary');
								thumbnail.insertAfter(temp.querySelector('.summary'), summary);
								thumbnail.removeChild(summary);
								// if thumbnail has preview then add hover preview listener
								if (thumbnail.dataset.hasOwnProperty('preview')) {
									add_hover_preview(thumbnail);
								}
							}
							if (response_medium.hasOwnProperty('tags')) {
								thumbnail.title = response_medium.tags;
								//TODO modify tags this page to reflect overall tags on all thumbnails
							}
							if (response_medium.hasOwnProperty('set_tiles')) {
								//TODO replace just sets
							}
							if (response_medium.hasOwnProperty('group_tiles')) {
								//TODO replace just group tiles
							}
						}
					}
					this.iterate_thumbnails(xhr.thumbnails, (thumbnail) => {
						thumbnail.classList.add('success');
						setTimeout(() => {
								thumbnail.classList.remove('success');
						}, 2000);
					});
				}
				else {
					this.iterate_thumbnails(xhr.thumbnails, (thumbnail) => {
						thumbnail.classList.add('failure');
					});
				}
			}
		};
		this.iterate_thumbnails(xhr.thumbnails, (thumbnail) => {
			thumbnail.classList.remove('failure');
			thumbnail.classList.add('processing');
		});
		xhr.open(
			method,
			action + (-1 != action.indexOf('?') ? '&' : '?') + '_' + new Date().getTime(),
			true
		);
		xhr.withCredentials = true;
		xhr.send(fd);
	}
	owner() {
		this.form.action = this.panels.dataset.actionEdit;
		this.toggle_panel('owner');
	}
	creation() {
		this.form.action = this.panels.dataset.actionEdit;
		this.toggle_panel('creation');
	}
	build() {
		this.hide_panels();
		let selected = document.querySelectorAll('.selected');
		this.iterate_thumbnails(selected, (thumbnail) => {
			this.api_request(
				'POST',
				this.panels.dataset.actionBuild,
				new FormData(),
				thumbnail
			);
		});
	}
	remove() {
		if (!confirm(this.panels.dataset.confirmRemove)) {
			return;
		}
		this.hide_panels();
		let selected = document.querySelectorAll('.selected');
		this.iterate_thumbnails(selected, (thumbnail) => {
			this.api_request(
				'POST',
				this.panels.dataset.actionRemove,
				new FormData(),
				thumbnail
			);
		});
	}
	groups() {
		this.form.action = this.panels.dataset.actionEdit;
		this.toggle_panel('groups');
	}
	searchability() {
		this.form.action = this.panels.dataset.actionEdit;
		this.toggle_panel('searchability');
	}
	protection() {
		this.form.action = this.panels.dataset.actionEdit;
		this.toggle_panel('protection');
	}
	generate_set() {
		if (!confirm(this.panels.dataset.confirmGenerateSet)) {
			return;
		}
		this.hide_panels();
		this.api_request(
			'POST',
			this.panels.dataset.actionGenerateSet,
			new FormData(),
			document.querySelectorAll('.selected')
		);
	}
	copy_tags() {
		this.hide_panels();
		let selected = document.querySelectorAll('.selected');
		let tags = [];
		this.iterate_thumbnails(selected, (thumbnail) => {
			if (!thumbnail.title) {
				return;
			}
			let current_tags = thumbnail.title.split('#');
			for (let i = 0; i < current_tags.length; i++) {
				let current_tag = current_tags[i];
				if (!current_tag || -1 != tags.indexOf(current_tag)) {
					continue;
				}
				tags.push(current_tag);
			}
		});
		if (0 == tags.length) {
			alert(this.panels.dataset.noTags);
			return;
		}
		tags.sort();
		let tags_string = '#' + tags.join('#');
		autocopy(
			tags_string,
			this.panels.dataset.autocopyAlert,
			this.panels.dataset.copyAlert
		);
	}
	add_tags() {
		this.form.action = this.panels.dataset.actionAddTags;
		this.move_tags_field('add');
		this.toggle_panel('add_tags');
	}
	remove_tags() {
		this.form.action = this.panels.dataset.actionRemoveTags;
		this.move_tags_field('remove');
		this.toggle_panel('remove_tags');
	}
	move_tags_field(mode) {
		this.tags_field.clear();
		let tags_panel = this.panels.querySelector('#manage_panel_' + mode + '_tags')
		tags_panel.insertBefore(this.tags_field.input, tags_panel.firstChild);
		tags_panel.insertBefore(this.tags_field.preview_wrapper, tags_panel.firstChild);
		setTimeout(() => {
			this.tags_field.input.focus();
		}, 1);
	}
	select_all() {
		let thumbnails = document.querySelectorAll('.thumbnail');
		this.iterate_thumbnails(thumbnails, (thumbnail) => {
			this.select(thumbnail);
		});
		this.update_selection_total();
	}
	select_none() {
		let selected = document.querySelectorAll('.selected');
		this.iterate_thumbnails(selected, (thumbnail) => {
			this.deselect(thumbnail);
		});
		this.update_selection_total();
	}
	update_selection_total() {
		let selected = document.querySelectorAll('.selected');
		let thumbnails = document.querySelectorAll('.thumbnail');
		if (selected.length == thumbnails.length) {
			document.body.dataset.selection_total = 'all';
			this.selection_total.innerText = this.selection_total.dataset.all;
		}
		else {
			document.body.dataset.selection_total = selected.length;
			this.selection_total.innerText = document.body.dataset.selection_total;
		}
	}
};

let manage = new Manage();
