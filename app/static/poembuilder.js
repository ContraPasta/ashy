$(document).ready(function () {
    var wordBox = '<div class="wordbox" id="w?">Word</div>';
    var lineBox = '<div class="linebox"id="l?"></div>';
    var nlines = 1;

    function newLine() {
	var linediv = lineBox.replace('?', nlines.toString());
	nlines++;
	return linediv;
    }

    $('#add').click(function(){
	$('#1').append(wordBox);
    });

    $('#newline').click(function(){
	$('#spec').append(newLine());
	nlines ++;
    });

    /* Need to perform the event binding inside document ready
       handler so I can attach events to elements created after
       the page loads
    */
    $(document).on('click', '.wordbox', function(){
	alert('wordbox clicked');
    });
});
