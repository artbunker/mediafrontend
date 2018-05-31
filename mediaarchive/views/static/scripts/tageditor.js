'use strict';
export class TagEditor {
	constructor() {
		this.tags_list = [];
		this.copy_alert = 'Copy raw tags manually';
		this.autocopy_alert = 'Tags copied to clipboard';
		this.input = document.createElement('input');
		this.input.type = 'text';
		this.input.placeholder = 'Enter a tag to add, click a tag to remove';
		// listener for input finish
		this.input.addEventListener('keydown', e => {
			//TODO maybe debounce this
			// not finishing input
			if ('Enter' != e.key) {
				this.refresh_suggestions();
				return;
			}
			this.add_tags(this.to_list(this.input.value));
			setTimeout(() => {
					this.clear_input();
			}, 1);
		});
		this.preview = document.createElement('div');
		// add reference to this tag editor on its preview and input
		this.input.tag_editor = this;
		this.preview.tag_editor = this;
	}
	show_suggestions() {
		//TODO
	}
	hide_suggestions() {
		//TODO
	}
	refresh_suggestions() {
		//TODO
	}
	add_suggestion(suggestion) {
		this.add_suggestions([suggestion])
	}
	add_suggestions(suggestions_list) {
		//TODO
	}
	clear() {
		this.clear_tags();
		this.clear_preview();
		this.clear_input();
	}
	clear_tags() {
		this.tags_list = [];
	}
	clear_preview() {
		this.preview.innerHTML = '';
	}
	clear_input() {
		this.input.value = '';
	}
	discard() {
		this.clear();
	}
	to_list(tags_string) {
		if ('' == tags_string) {
			return [];
		}
		// single tag
		if (-1 == tags_string.indexOf('#')) {
			return [tags_string];
		}
		// strip leading and trailing hashes and split on hashes
		return tags_string.replace(/^#+|#+$/g, '').split('#');
	}
	add_tag(tag) {
		this.add_tags([tag]);
	}
	create_tag_element(tag) {
		let el = document.createElement('span');
		el.classList.add('tag');
		el.dataset.tag = tag;
		let inner_el = document.createElement('span');
		// for negation tag text shouldn't include the hyphen
		inner_el.innerText = '#' + ('-' == tag[0] ? tag.substring(1) : tag);
		el.appendChild(inner_el);
		return el;
	}
	add_tags(tags_list) {
		for (let i = 0; i < tags_list.length; i++) {
			let tag = tags_list[i];
			if (-1 != this.tags_list.indexOf(tag)) {
				continue;
			}
			this.tags_list.push(tag);
			let el = this.create_tag_element(tag)
			el.addEventListener('click', e => {
				this.remove_tag(e.currentTarget.dataset.tag);
			});
			this.preview.appendChild(el);
			this.hide_suggestions();
			// dispatch add event
			this.input.dispatchEvent(
				new CustomEvent(
					'added',
					{
						detail:
						{
							tag: tag,
							el: el,
						}
					}
				)
			);
		}
	}
	remove_tag(tag) {
		console.log('trying to remove tag: ' + tag);
		this.remove_tags([tag]);
	}
	remove_tags(tags_list) {
		for (let i = 0; i < tags_list.length; i++) {
			let tag = tags_list[i];
			let tag_index = this.tags_list.indexOf(tag)
			if (-1 == tag_index) {
				continue;
			}
			this.tags_list.splice(tag_index, 1)
			let tag_el = this.preview.querySelector('.tag[data-tag="' + tag.replace('\\', '\\\\') + '"]');
			tag_el.parentNode.removeChild(tag_el);
			// dispatch remove event
			this.input.dispatchEvent(
				new CustomEvent(
					'removed',
					{
						detail:
						{
							tag: tag,
						}
					}
				)
			);
		}
		this.input.focus();
	}
	to_string(tags_list) {
		return tags_list.join('#');
	}
	copy() {
		let tag_string = this.to_string(this.tags_list).replace(' #', '#');
		// autocopy to clipboard
		try {
			// create temp input
			let temp_input = document.createElement('input');
			temp_input.type = 'text';
			temp_input.value = tag_string;
			document.body.appendChild(temp_input);
			temp_input.select();
			if (document.execCommand('copy')) {
				alert(this.autocopy_alert);
			}
			else {
				// fallback to prompt
				prompt(this.copy_alert, tag_string);
			}
			// destroy temp input
			document.body.removeChild(temp_input);
		}
		catch (err) {
			// fallback to prompt
			prompt(this.copy_alert, tag_string);
		}
		this.input.focus();
	}
}
