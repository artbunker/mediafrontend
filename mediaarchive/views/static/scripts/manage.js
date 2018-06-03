'use strict';

class Manage {
	constructor(drawer) {
		this.drawer = drawer;
		this.keys = {
			exit: 'Escape',
			toggle: 'e',
			add_tags: 't',
			generate_set: 's',
			select_all: 'a',
			select_none: 'd',
			remove: 'Delete',
		};
		// move drawer into body
		document.body.append(this.drawer);

		// listener for shortcut keys
		window.addEventListener('keydown', e => {
			if (this.keys.exit == e.key) {
				this.exit();
				return;
			}
			// ignore other management keys if in an input
			if ('INPUT' == document.activeElement.tagName) {
				return;
			}
			if (this.keys.toggle == e.key) {
				this.toggle();
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
		this.selection_total = this.drawer.querySelector('#selection_total');
		this.selection_total.dataset.count = 0;

		// select/deselect listeners to thumbnails
		this.thumbnails = document.querySelectorAll('.thumbnail');
		for (let i = 0; i < this.thumbnails.length; i++) {
			this.thumbnails[i].addEventListener('click', (e) => {
				if (!document.body.classList.contains('editing_media')) {
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
			this.toggle();
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

		window.addEventListener('resize', () => {
			this.calculate_drawer_spacing();
		});
		this.calculate_drawer_spacing();
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
		if (document.body.classList.contains('editing_media')) {
			this.drawer.style.height = this.drawer.height;
		}
		else {
			this.drawer.style.height = '0';
		}
	}
	enter() {
		this.select_none();
		document.body.classList.add('editing_media');
		this.set_drawer_height();
	}
	exit() {
		document.body.classList.remove('editing_media');
		this.select_none();
		this.set_drawer_height();
	}
	toggle() {
		document.body.classList.toggle('editing_media');
		if (document.body.classList.contains('editing_media')) {
			this.enter();
		}
		else {
			this.exit();
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
