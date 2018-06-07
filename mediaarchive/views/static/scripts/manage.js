'use strict';

document.documentElement.classList.add('scripts_enabled');

class Manage {
	constructor(drawer) {
		this.drawer = drawer;
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

		// move drawer into body
		document.body.append(this.drawer);

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
		this.thumbnails = document.querySelectorAll('.thumbnail');
		for (let i = 0; i < this.thumbnails.length; i++) {
			this.thumbnails[i].addEventListener('click', (e) => {
				if (!document.body.classList.contains('managing_media')) {
					return;
				}
				e.preventDefault();
				e.stopPropagation();
				e.currentTarget.classList.toggle('selected');
				this.update_selection_total();
			});
		}

		// manage topmenu link listener
		let manage_link = document.querySelector('#top_manage');
		manage_link.addEventListener('click', () => {
			this.toggle_management();
		});

		// manage action buttons
		let actions = [
			'build',
			'remove',
			'generate_set',
			'copy_tags',
			'select_all',
			'select_none',
		];
		for (let i = 0; i < actions.length; i++) {
			let action = actions[i];
			this.drawer.querySelector('#manage_' + action).addEventListener('click', () => {
				console.log(action);
				console.log('context of:');
				console.log(this);
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
		for (let i = 0; i < this.thumbnails.length; i++) {
			let thumbnail = this.thumbnails[i];
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
		}
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
		//TODO
	}
	generate_set() {
		//TODO
	}
	select_all() {
		for (let i = 0; i < this.thumbnails.length; i++) {
			this.thumbnails[i].classList.add('selected');
		}
		this.update_selection_total();
	}
	select_none() {
		let selected = document.querySelectorAll('.selected');
		for (let i = selected.length - 1; i >= 0; i--) {
			selected[i].classList.remove('selected');
		}
		this.update_selection_total();
	}
	update_selection_total() {
		let selected = document.querySelectorAll('.selected');
		if (selected.length == this.thumbnails.length) {
			document.body.dataset.selection_total = 'all';
			this.selection_total.innerText = this.selection_total.dataset.all;
		}
		else {
			document.body.dataset.selection_total = selected.length;
			this.selection_total.innerText = document.body.dataset.selection_total;
		}
	}
};

let manage = new Manage(document.querySelector('#manage_drawer'));
