'use strict';

// media preferences
let preferences_link = document.querySelector('.menu .preferences');
preferences_link.addEventListener('click', e => {
	document.body.classList.add('editing_preferences');
});
let preferences_form = document.querySelector('#media_preferences');
let preferences_inputs = preferences_form.querySelectorAll('input:not([type="submit"])');
let preferences_textareas = preferences_form.querySelectorAll('textarea');
// load preferences
for (let i = 0; i < preferences_inputs.length; i++) {
	let input = preferences_inputs[i];
	let value = localStorage.getItem(input.id);
	if ('checkbox' == input.type) {
		if (value) {
			input.checked = true;
		}
	}
	else {
		input.value = value;
	}
}
for (let i = 0; i < preferences_textareas.length; i++) {
	let input = preferences_textareas[i];
	let value = localStorage.getItem(input.id);
	if (value) {
		input.value = value;
	}
}

// save preferences
let save_preferences = function() {
	for (let i = 0; i < preferences_inputs.length; i++) {
		let input = preferences_inputs[i];
		let value = input.value;
		if ('checkbox' == input.type) {
			if (input.checked) {
				localStorage.setItem(input.id, 1);
			}
			else {
				localStorage.removeItem(input.id);
			}
		}
		else {
			localStorage.setItem(input.id, value);
		}
	}
	for (let i = 0; i < preferences_textareas.length; i++) {
		let input = preferences_textareas[i];
		localStorage.setItem(input.id, input.value);
	}
	document.body.classList.remove('editing_preferences');
};
document.querySelector('#dim').addEventListener('click', (e) => {
	document.body.classList.remove('editing_preferences');
	save_preferences();
});
document.querySelector('#media_preferences').addEventListener('submit', e => {
	e.preventDefault();
	save_preferences();
});
