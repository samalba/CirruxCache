/*
 * This file is part of the CirruxCache project
 * http://code.google.com/p/cirruxcache/
 */

$(document).ready(function() {
		$("#flush > span").hide();
		var t = $("#tabs");
		t.tabs({ show: function(event, ui) {
			var i = t.tabs('option', 'selected');
			if (i == 1)
				initStore();
			}});
		$("#flush > input").bind("click", flush);
		$("#store > fieldset > form").bind("change", newStore);
		$("#store > fieldset > input[type=text]").bind("blur", checkStorePath);
		});

var flush = function() {
	var data = $("#flush > textarea")[0].value.split("\n");
	for (var i = 0; i < data.length; ++i)
	{
		var req = jQuery.trim(data[i]);
		if (req[0] != "/")
			req = "/" + req;
		$.ajax({type: "DELETE", url: req, dataType: "text"});
	}
	var result = $("#flush > span");
	result.html(data.length + " flush request" + (data.length > 1 ? "s" : "") + " sent");
	result.slideDown("fast");
	setTimeout(function() { result.slideUp("fast") }, 3000);
}

var initStore = function() {

}

var checkStorePath = function() {
	var url = $("#store > fieldset > input[type=text]")[0];
	if (url.value[url.value.length - 1] == "/" || url.value[0] != "/") {
		alert("Bad path syntax");
		url.focus();
	}
}

var newStore = function() {
	var url = $("#store > fieldset > input[type=text]")[0].value;
	url += "/new";
	$.ajax({
		type: "GET",
		url: url,
		dataType: "text",
		success: addStore,
		error: function(XMLHttpRequest, textStatus, errorThrown) {
			var result = $("#store > span");
			result.html(textStatus + " (" + XMLHttpRequest.status + " " + XMLHttpRequest.statusText + ")");
			result.slideDown("fast");
			setTimeout(function() { result.slideUp("fast") }, 3000);
		}
		});
}

var addStore = function(data, textStatus, XMLHttpRequest) {
	alert('good');
	$("#store > fieldset > form").ajaxSubmit({
			url: data,
			dataType: "text",
			success: initStore
			});
}
