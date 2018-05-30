'use strict';
// restricts tags wrapper on view pages to the width of their associated medium
let tags = document.querySelectorAll('.tags');
for (let i = 0; i < tags.length; i++) {
	tags[i].style.display = 'none';
	tags[i].style.width = tags[i].parentNode.querySelector('.medium').clientWidth + 'px';
	tags[i].style.display = '';
}
