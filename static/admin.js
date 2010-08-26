/*
 * This file is part of the CirruxCache project
 * http://code.google.com/p/cirruxcache/
 */

$(document).ready(function() {
		$("#flush > span").hide();
		var t = $("#tabs");
		var tabCallback = [null, fetchStore, fetchStats];
		t.tabs({ show: function(event, ui) {
			var cb = tabCallback[t.tabs("option", "selected")];
			if (cb)
				cb();
			$("div > span:first-child").hide();
			}});
		$("#flush > input").bind("click", flush);
		$("#store > fieldset > form").bind("change", newStore);
		$("#store > fieldset > input[type=text]").bind("blur", checkStorePath);
		$("#stats > input").bind("click", function() { fetchStats(true) });
		$("#config > fieldset > input").bind("click", configNewFile);
		});

var showMessage = function(target, message) {
	var t = $(target);
	t.html(message);
	t.slideDown("fast");
	setTimeout(function() { t.slideUp("fast") }, 3000);
}

var flush = function() {
	var data = $("#flush > textarea")[0].value.split("\n");
	var message = "";
	var j = 0;
	for (var i = 0; i < data.length; ++i)
	{
		var req = jQuery.trim(data[i]);
		$.ajax({type: "DELETE",
				url: req,
				dataType: "text",
				complete: function(XMLHttpRequest, textStatus) {
					message += ++j + ") " + textStatus + "<br />";
					if (i == data.length)
						showMessage("#flush > span", message);
				}});
	}
}

var fetchStore = function(force) {
	var target = $("#store > ul");
	if (!force && target.html())
		return;
	$.ajax({
		url: document.location.pathname + "store",
		dataType: "text",
		success: function(data, textStatus, XMLHttpRequest) {
			if (!data)
				data = " ";
			target.html(data);
			}
		});
}

var checkStorePath = function() {
	var url = $("#store > fieldset > input[type=text]")[0];
	if (url.value[url.value.length - 1] == "/" || url.value[0] != "/") {
		alert("Bad path syntax");
		url.focus();
		return false;
	}
	return true;
}

var newStore = function() {
	if (!checkStorePath())
		return false;
	var url = $("#store > fieldset > input[type=text]")[0].value;
	url += "/new";
	$.ajax({
		type: "GET",
		url: url,
		dataType: "text",
		success: addStore,
		error: function(XMLHttpRequest, textStatus, errorThrown) {
			showMessage("#store > span", "Error. Is billing mode enabled on this AppEngine account?");
			}
		});
}

var addStore = function(data, textStatus, XMLHttpRequest) {
	var form = $("#store > fieldset > form");
	form.ajaxSubmit({
		url: data,
		dataType: "text",
		success: function() {
			fetchStore(true);
			form[0].reset();
			showMessage("#store > span", "Upload successful");
			}
		});
}

var delStore = function(url) {
	var c = confirm("Remove this file?");
	if (!c)
		return;
	$.ajax({
		type: "GET",
		url: url + "/delete",
		dataType: "text",
		complete: function() { fetchStore(true); }
	});
}

var fetchStats = function(force) {
	var target = $("#stats > ul");
	if (!force && target.html())
		return;
	$.ajax({
		url: document.location.pathname + "stats",
		dataType: "text",
		success: function(data, textStatus, XMLHttpRequest) {
			if (!data)
				data = " ";
			target.html(data);
			}
		});
}

var configNewFile = function() {
	$("#config > fieldset").slideUp("fast");
	$("#config > div").slideDown("fast");
}
