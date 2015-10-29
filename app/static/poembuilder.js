'use strict';

$(document).ready(function () {

    var uiState = 'normal';
    var poemData = {};
    var selectedWordID;
    var selectedDevice;

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

    $('#ui-clear-words').click(function (event) {
        $('#ui-spec').empty();
    });

    $('#ui-change-state').click(function (event) {
        if (uiState === 'word_select') {
            uiState = 'normal';
        } else {
            uiState = 'word_select';
        }
    });

    $('#ui-generate-poem').click(function (event) {
        $.post('/generate', JSON.stringify(poemData), null, 'application/json');
    });

    // NB: When binding to elements that are created dynamically you need to
    // use jQuery.fn.on on an ancestor element that exists at the time the
    // event is bound.
    $('#ui-spec').on('click', '.dropdown .dropdown-toggle', function (event) {
        if (uiState === 'normal') {
            $(this).dropdown('toggle');
            // Switch off event handlers on the dropdowns to prevent the
            // bootstrap event interfering with custom event.
            $('.dropdown-toggle').unbind();
        }
        else {
            var id = $(this).attr('id');
            if ( id === selectedWordID ) {
                uiState = 'normal';
                $(this).dropdown('toggle');
                $(this).text('Word');
            }
            else {
                if ( selectedDevice in poemData ) {
                    if ( poemData[selectedDevice].indexOf(id) < 0 ) {
                        poemData[selectedDevice].push(id);
                    }
                }
                else {
                    poemData[selectedDevice] = [id];
                }
                console.log(poemData);
            }
        }
    });

    // Bind event handlers for word control menu options
    $('#ui-spec').on('click', '.dropdown  #word-rhyme', function (event) {
        uiState = 'word_select';
        $('.dropdown-toggle').unbind();
        var parentButton = $(this).closest('.dropdown-menu').prev();
        var wordID = parentButton.attr('id');
        selectedWordID = wordID;
        selectedDevice = 'rhyme';
        parentButton.text('Done');
    });

    $('#ui-spec').on('click', '.dropdown #word-alliterate', function (event) {
        uiState = 'word_select';
        $('.dropdown-toggle').unbind();
        var parentButton = $(this).closest('.dropdown-menu').prev();
        var wordID = parentButton.attr('id');
        selectedWordID = wordID;
        selectedDevice = 'alliteration';
        parentButton.text('Done');
    });

});
