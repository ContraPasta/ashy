$(document).ready(function () {
    var uiState = 'normal';
    // Load HTML for word control from server
    var wordUiElement;
    $.get('/static/word_ui_element.html', function (data) {
	wordUiElement = data;
    });
    var nwords = 0;
    var testClickCounter = 0;

     // Make it so dropdowns are exclusively controlled via JavaScript
    $(document).off('.dropdown.data-api')

    $('#ui-add-word').click(function (event) {
	var control = wordUiElement.replace(/wx/g, 'w' + nwords.toString());
	$('#ui-spec').append(control);
	nwords++;
    });

    $('#ui-change-state').click(function (event) {
	if (uiState === 'word_select') {
	    uiState = 'normal';
	} else {
	    uiState = 'word_select';
	    // Switch off event handlers on the dropdowns to prevent the
	    // bootstrap event interfering with custom event
	}
    });

    // NB: When binding to elements that are created dynamically you need to
    // use jQuery.fn.on on an ancestor element that exists at the time the
    // event is bound.
    $('#ui-spec').on('click', '.dropdown .dropdown-toggle', function () {
	if (uiState === 'normal') {
	    $(this).dropdown('toggle');
	    // Switch off event handlers on the dropdowns to prevent the
	    // bootstrap event interfering with custom event.
	    $('.dropdown-toggle').unbind();
	}
	else {
	    testClickCounter ++;
	    console.log('testclick incremented');
	}
    });


});
