'use strict';

import { autocopy } from './autocopy.js';

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
			generate_set: 's',
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
			}
			else if (this.keys.add_tags == e.key) {
				this.show_panel('add_tags');
			}
			else if (this.keys.generate_set == e.key) {
				this.generate_set();
			}
			else if (this.keys.select_all == e.key) {
				this.select_all();
			}
			else if (this.keys.select_none == e.key) {
				this.select_none();
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
				e.currentTarget.classList.toggle('selected');
				this.update_selection_total();
			});
		});

		// manage topmenu link listener
		let manage_link = document.querySelector('#top_manage');
		manage_link.addEventListener('click', () => {
			this.toggle_management();
		});

		this.panels['tags'] = document.querySelector('#manage_panel_tags');
		//TODO set up tags panel tag editor
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
			this.drawer.querySelector('#manage_' + action).addEventListener('click', () => {
				this[action]();
			});
		}

		// drag to select
		this.drag_origin = {
			x: 0,
			y: 0,
		};
		this.blank = document.createElement('img');
		this.blank.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
		this.blank.id = 'blank';
		this.selection_box = document.createElement('span');
		this.selection_box.id = 'selection_box';
		this.hide_selection_box();
		document.body.appendChild(this.blank);
		document.body.appendChild(this.selection_box);
		document.body.addEventListener('dragstart', (e) => {
			if (!document.body.classList.contains('managing_media')) {
				return;
			}
			this.show_selection_box();
			e.dataTransfer.setDragImage(this.blank, 0, 0);
			this.drag_origin.x = e.pageX;
			this.drag_origin.y = e.pageY;
		});
		document.body.addEventListener('drag', (e) => {
			this.update_selection_box(e.pageX, e.pageY);
		});
		document.body.addEventListener('dragend', (e) => {
			e.preventDefault();
			if (document.body.classList.contains('managing_media')) {
				this.update_selection_box(e.pageX, e.pageY);
				this.selection_from_drag();
			}
			this.hide_selection_box();
		});

		this.form.addEventListener('submit', (e) => {
			e.preventDefault();
			//TODO if tags input convert tag editor current tags list to string
			//TODO and set tags input value to it
			this.api_request(
				'POST',
				this.form.action,
				new FormData(this.form),
				document.querySelectorAll('.selected')
			);
			this.hide_panels();
		});

		// move drawer into body and get initial size
		document.body.append(this.drawer);

		window.addEventListener('resize', () => {
			this.calculate_drawer_spacing();
		});
		this.calculate_drawer_spacing();
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
					thumbnail.classList.remove('selected');
				}
				else {
					thumbnail.classList.add('selected');
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
		document.body.classList.add('managing_media');
		this.set_drawer_height();
	}
	exit_management() {
		document.body.classList.remove('managing_media');
		this.select_none();
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
		this.form.appendChild(this.panels.querySelector('#manage_panel_' + panel));
		this.active_panel.classList.add('active');
	}
	hide_panels() {
		this.active_panel.classList.remove('active');
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
	/** /
	lock_form(form) {
		let elements = form.elements;
		for (let i = 0; i < elements.length; i++) {
			elements[i].readOnly = true;
		}
	}
	unlock_form(form) {
		let elements = form.elements;
		for (let i = 0; i < elements.length; i++) {
			elements[i].readOnly = false;
		}
	}
	batch_finished(left_in_batch, cb) {
		//TODO locking and unlocking form for batches maybe?
		left_in_batch--;
		if (0 == left_in_batch) {
			cb();
		}
	}
	/**/
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
	api_request(method, action, fd, thumbnails) {
		console.log(thumbnails);
		let xhr = new XMLHttpRequest();
		if (1 == thumbnails.length) {
			fd.append('medium_id', thumbnails[0].dataset.id);
		}
		else {
			let medium_ids = [];
			this.iterate_thumbnails(thumbnails, (thumbnail) => {
				medium_ids.push(thumbnail.dataset.id);
			});
			fd.append('medium_ids', medium_ids);
		}
		xhr.thumbnails = thumbnails;
		fd.append('response_type', 'json');
		xhr.responseType = 'json';
		xhr.onreadystatechange = () => {
			if (xhr.readyState == XMLHttpRequest.DONE) {
				this.iterate_thumbnails(xhr.thumbnails, (thumbnail) => {
					thumbnail.classList.remove('processing');
				});
				//TODO check for batch finished?
				//TODO e.g. all add/remove tags finished
				//TODO to make additional call to rebuild tags
				if (200 == xhr.status) {
					if (!xhr.response) {
						return;
					}
					if (xhr.response.hasOwnProperty('remove')) {
						this.iterate_thumbnails(xhr.thumbnails, (thumbnail) => {
							thumbnail.parentNode.removeChild(thumbnail);
						});
						return;
					}
					if (xhr.response.hasOwnProperty('thumbnail')) {
						// replace thumbnail innerHTML with response thumbnail innerHTML
						// to retain listeners
						let temp = document.createElement('div');
						temp.innerHTML = xhr.response.thumbnail;
						xhr.thumbnails[0].innerHTML = temp.querySelector('.thumbnail').innerHTML;
					}
					if (xhr.response.hasOwnProperty('group_tiles')) {
						//TODO replace group tiles with new group tiles
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
						setTimeout(() => {
							thumbnail.classList.remove('failure');
						}, 2000);
					});
				}
			}
		};
		this.iterate_thumbnails(xhr.thumbnails, (thumbnail) => {
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
		this.api_request(
			'POST',
			this.panels.dataset.actionBuild,
			new FormData(),
			document.querySelectorAll('.selected')
		);
	}
	remove() {
		console.log('removing');
		this.hide_panels();
		this.api_request(
			'POST',
			this.panels.dataset.actionRemove,
			new FormData(),
			document.querySelectorAll('.selected')
		);
	}
	groups() {
		this.form.action = this.panels.dataset.actionRemove;
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
		this.api_request(
			'POST',
			this.panels.dataset.actionGenerateSet,
			new FormData(),
			document.querySelectorAll('.selected')
		);
	}
	copy_tags() {
		this.hide_panels();
		//TODO allow copying aggregate of all tags from multiple selected media?
		let medium = document.querySelector('.selected');
		let tags_panel = this.panels.querySelector('#manage_panel_tags');
		if (!medium || !medium.title) {
			alert(tags_panel.dataset.noTags);
			return;
		}
		autocopy(
			medium.title,
			tags_panel.dataset.autocopyAlert,
			tags_panel.dataset.copyAlert
		);
	}
	add_tags() {
		this.form.action = this.form.dataset.actionAdd;
		console.log('add tags');
		//this.toggle_panel('tags');
	}
	remove_tags() {
		this.form.action = this.form.dataset.actionRemove;
		console.log('remove tags');
		//this.toggle_panel('tags');
	}
	select_all() {
		let thumbnails = document.querySelectorAll('.thumbnail');
		this.iterate_thumbnails(thumbnails, (thumbnail) => {
			thumbnail.classList.add('selected');
		});
		this.update_selection_total();
	}
	select_none() {
		let selected = document.querySelectorAll('.selected');
		this.iterate_thumbnails(selected, (thumbnail) => {
			thumbnail.classList.remove('selected');
		});
		this.update_selection_total();
	}
	update_selection_total() {
		let selected = document.querySelectorAll('.selected');
		let thumbnails = document.querySelectorAll('.thumbnails');
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
