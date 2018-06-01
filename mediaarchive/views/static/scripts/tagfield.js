'use strict';
export class TagField {
	constructor(strings) {
		this.tags_list = [];
		// strings
		this.strings = {};
		if ('undefined' == typeof strings) {
			strings = {};
		}
		if (!strings.hasOwnProperty('placeholder')) {
			strings.placeholder = 'Enter a tag to add, click a tag to remove';
		}
		if (!strings.hasOwnProperty('remove_tag_title')) {
			strings.remove_tag_title = 'Remove this tag';
		}
		this.strings.placeholder = strings.placeholder;
		this.strings.remove_tag_title = strings.remove_tag_title;
		// create field input
		this.input = document.createElement('input');
		this.input.type = 'text';
		this.input.placeholder = this.strings.placeholder;
		// listener for input finish
		this.debounce = null;
		this.input.addEventListener('keydown', e => {
			// not finishing input
			if ('Enter' != e.key) {
				if (this.debounce) {
					clearTimeout(this.debounce);
				}
				this.hide_suggestions();
				this.debounce = setTimeout(() => {
					this.show_suggestions();
				}, 500);
				return;
			}
			if ('' == this.input.value) {
				// dispatch submit
				this.input.dispatchEvent(
					new CustomEvent('submit')
				);
				return;
			}
			this.add_tags(this.to_list(this.input.value));
			setTimeout(() => {
				this.clear_input();
				this.hide_suggestions();
			}, 1);
		});
		this.preview = document.createElement('div');
		// suggestions lists
		this.tag_suggestions_limit = 16;
		this.tag_suggestions_empty = document.querySelector('#tag_suggestions_empty');
		if (!this.tag_suggestions_empty) {
			this.tag_suggestions_empty = document.createElement('datalist');
			this.tag_suggestions_empty.id = 'tag_suggestions_empty';
			document.body.appendChild(this.tag_suggestions_empty);
		}
		this.tag_suggestions_limited = document.createElement('datalist');
		this.tag_suggestions_limited.id = 'tag_suggestions_limited' + new Date().getTime();
		document.body.appendChild(this.tag_suggestions_limited);
		// add reference to this tag editor on its preview and input
		this.input.tag_editor = this;
		this.preview.tag_editor = this;
	}
	show_suggestions() {
		let tag_suggestions = document.querySelector('#tag_suggestions');
		if (
			'' == this.input.value
			|| 0 >= this.tag_suggestions_limit
			|| !tag_suggestions
		) {
			return;
		}
		let needle = this.input.value.trim();
		let negation = false;
		if ('-' == needle[0]) {
			negation = true;
			needle = needle.substring(1);
		}
		//TODO loop through full suggestions list checking for matches
		this.tag_suggestions_limited.innerHTML = '';
		let r = new RegExp(needle, 'i');
		let dupe_check = [];
		let options = tag_suggestions.children;
		for (let i = 0; i < options.length; i++) {
			let option = options[i];
			if (
				r.test(option.value)
				&& -1 == dupe_check.indexOf(option.value)
			) {
				dupe_check.push(option.value);
				let cloned = option.cloneNode(true);
				if (negation) {
					cloned.value = '-' + cloned.value;
				}
				this.tag_suggestions_limited.appendChild(cloned);
				if (this.tag_suggestions_limited.children.length == this.tag_suggestions_limit) {
					break;
				}
			}
		}
		this.input.setAttribute('list', this.tag_suggestions_limited.id);
		//TODO firefox doesn't show the dropdown automatically for some reason
	}
	hide_suggestions() {
		console.log('hiding suggestions');
		this.input.setAttribute('list', this.tag_suggestions_empty.id);
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
	create_tag_element(tag, title, link_uri) {
		let el = document.createElement('span');
		el.classList.add('tag');
		el.dataset.tag = tag.replace('"', '&quot;');
		if ('undefined' != typeof title) {
			el.title = title;
		}
		let inner_el = null;
		if ('undefined' == typeof link_uri) {
			inner_el = document.createElement('span');
		}
		else {
			inner_el = document.createElement('a');
			inner_el.href = link_uri.replace('{}', encodeURIComponent(tag));
		}
		// for negation tag text shouldn't include the hyphen
		inner_el.innerText = '#' + ('-' == tag[0] ? tag.substring(1) : tag);
		el.appendChild(inner_el);
		return el;
	}
	add_tag(tag) {
		this.add_tags([tag]);
	}
	add_tags(tags_list) {
		for (let i = 0; i < tags_list.length; i++) {
			let tag = tags_list[i];
			if (-1 != this.tags_list.indexOf(tag)) {
				continue;
			}
			this.tags_list.push(tag);
			let el = this.create_tag_element(tag)
			el.title = this.strings.remove_tag_title;
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
		this.remove_tags([tag]);
	}
	remove_tags(tags_list) {
		for (let i = 0; i < tags_list.length; i++) {
			let tag = tags_list[i].replace('&quot;', '"');
			let tag_index = this.tags_list.indexOf(tag)
			if (-1 == tag_index) {
				continue;
			}
			this.tags_list.splice(tag_index, 1)
			let tag_el = this.preview.querySelector('.tag[data-tag="' + tag.replace('"', '&quot;').replace('\\', '\\\\') + '"]');
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
		tags_list.sort();
		return tags_list.join('#');
	}
}

export function fetch_tag_suggestions() {
	let tag_suggestions = document.querySelector('#tag_suggestions');
	if (!tag_suggestions) {
		tag_suggestions = document.createElement('datalist');
		tag_suggestions.id = 'tag_suggestions';
		document.body.appendChild(tag_suggestions);
		let tag_suggestion_lists = document.querySelectorAll('meta[name="tag_suggestion_list"]');
		let completed = 0;
		for (let i = 0; i < tag_suggestion_lists.length; i++) {
			let xhr = new XMLHttpRequest();
			xhr.onreadystatechange = () => {
				if (xhr.readyState == XMLHttpRequest.DONE) {
					if (200 == xhr.status) {
						if (xhr.response) {
							for (let i = 0; i < xhr.response.length; i++) {
								let suggestion = xhr.response[i];
								let option = document.createElement('option');
								option.value = suggestion;
								tag_suggestions.appendChild(option);
							}
						}
					}
					completed++;
					if (completed == tag_suggestion_lists.length) {
						//TODO remove duplicates
					}
				}
			};
			let action = tag_suggestion_lists[i].getAttribute('value');
			xhr.open('GET', action + (-1 != action.indexOf('?') ? '&' : '?') + '_' + new Date().getTime(), true);
			xhr.responseType = 'json';
			xhr.withCredentials = true;
			xhr.send();
		}
	}
}
