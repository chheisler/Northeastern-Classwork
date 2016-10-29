$(document).ready(function() {
	$("#yes").click(labelYes);
	$("#no").click(labelNo);
});

function labelYes() {
	labelRegion(true);
}

function labelNo() {
	labelRegion(false);
}

function labelRegion(label) {
	id = $('#id').html();
	token = $('input[name="csrfmiddlewaretoken"]').val()
	$.ajax(
		{
			method: 'POST',
			url: next_url,
			data: {id: id, label: label, csrfmiddlewaretoken: token},
			dataType: "json",
			success: labelOnSuccess,
			error: labelOnError,
			xhrFields: {withCredentials: true}
		}
	);
}

function labelOnSuccess(json) {
	if (json.id) {
		$('#id').html(json.id);
		$('#factbook').html(json.factbook);
		$('#tags').html(json.tags);
		$('#embassies').html(json.embassies)
	} else {
		alert('Nothing left to label!');
	}
}

function labelOnError() {
	alert('Something went wrong!');
}