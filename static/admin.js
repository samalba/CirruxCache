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
		$("#flush > input[type=button]").bind("click", flush);
		$("#store > fieldset > form").bind("change", newStore);
		$("#store > fieldset > input[type=text]").bind("blur", checkStorePath);
		$("#stats > input[type=button]").bind("click", function() { fetchStats(true) });
		$("#config > fieldset > input").bind("click", configNewFile);
		$("#config > div > input + input[type=button]").bind("click", configClose);
		$("#config > div > fieldset:eq(0) > input[type=button]").bind("click", configMappingAdd);
		$("#configMapping > div > select").bind("mousedown", configMappingSelect);
		$("#config > div > fieldset:eq(1) > input[type=button]").bind("click", configServicesAdd);
		test();
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

var configClose = function() {
	if (!confirm("All this configuration will be lost!"))
		return;
	document.location.href = document.location.pathname + "#config";
	document.location.reload();
}

var test = function() {
	// Test to load config
	configServicesAdd("Test", "redirect");
	configServicesVarAdd("foo", "bar");
	configMappingAdd("/(.*)", "Test");
}

var configMappingAdd = function(name, type) {
	fromEvent = (this.type != undefined);
	if (fromEvent || $("#configMapping").children().length > 1)
	{
		$("#configMapping").append("<div>" + $("#configMapping > div:first-child").html() + "</div>");
		$("#configMapping > div:last-child > select").bind("mousedown", configMappingSelect);
		$("#configMapping > div:last-child > input[type=button]").bind("click", function() {
				var div = this.parentNode;
				div.parentNode.removeChild(div);
				});
	}
	if (fromEvent)
		return;
	var select = $("#configMapping > div:last-child > select");
	configMappingSelect(select);
	$("#configMapping > div:last-child > input[type=text]").val(name);
	select.val(type);
}

var configMappingSelect = function(target) {
	if (this.type != undefined) {
		target = $(this);
	}
	var html = "<option>&lt;Service Name&gt;</option>";
	var legend = $("#configServices > div > fieldset > legend");
	for (var i = 0; i < legend.length; ++i) {
		var v = legend[i].innerHTML;
		if (v == "")
			continue;
		var value = v.substr(0, v.indexOf(" ("));
		html += "<option value=\"" + value + "\">" + value + "</option>";
	}
	target.html(html);
}

var configServicesAdd = function(title, type) {
	if (this.type != undefined)
	{
		type = $("#config > div > fieldset:eq(1) > select").val();
		title = $("#config > div > fieldset:eq(1) > input[type=text]").val();
	}
	if (type == "" || title == "") {
		alert("Select a type AND set a service name.");
		return;
	}
	$("#configServices").append("<div>" + $("#configServices > div:first-child").html() + "</div>");
	$("#configServices > div:last-child > fieldset > legend").text(title + " (" + type + ")");
	$("#configServices > div:last-child > input[type=button]").bind("click", function() {
			var div = this.parentNode;
			div.parentNode.removeChild(div);
			});
	$("#configServices > div:last-child > fieldset > input[type=button]").bind("click", configServicesVarAdd);
	configServicesVarBind($("#configServices > div:last-child > fieldset > div"));
}

var configServicesVarAdd = function(type, value) {
	fromEvent = (this.type != undefined);
	var target = $(this);
	if (!fromEvent)
		target = $("#configServices > div:last-child > fieldset > input[type=button]");
	var html = target.next().html();
	target.parent().append("<div>" + html + "</div>");
	target.parent().find("div:last-child > input[type=button]").bind("click", function() {
			var div = this.parentNode;
			div.parentNode.removeChild(div);
			});
	configServicesVarBind(target.parent().find("div:last-child"));
	if (!fromEvent) {
		var select = target.parent().find("div:last-child > select");
		select.html(select.html() + "<option value=\"" + type + "\">" + type + "</option>");
		select.val(type);
		target.parent().find("div:last-child > input[type=text]").val(value);
		if ($("#configServices").children().length <= 1)
			return;
	}
}

var parseServiceType = function(legend) {
	var service = legend.text();
	var i = service.indexOf(" (") + 2;
	return service.substr(i, service.length - i - 1);
}

var configServicesVarBind = function(div) {
	var select = div.find("select");
	var type = parseServiceType(div.parent().find("legend"));
	select.bind("mousedown", function() {
			$.ajax({
				url: document.location.pathname + "configvars?" + type,
				dataType: "text",
				async: false,
				success: function(data, textStatus, XMLHttpRequest) {
					var a = eval(data);
					select.html("<option value=\"\">&lt;Variable&gt;</option>");
					for (var i in a) {
						select.append("<option value=\"" + a[i] + "\">" + a[i] + "</option>");
					}
				}
			});
			});
	var getConfigHelp = function(tooltip) {
		var type = div.find("select").val();
		var service = parseServiceType(div.parent().find("legend"));
		if (type == "") {
			$(tooltip).html("No help available");
			return;
		}
		$.ajax({
			url: document.location.pathname + "confighelp?" + service + "_" + type,
			dataType: "text",
			async: false,
			success: function(data, textStatus, XMLHttpRequest) {
				$(tooltip).html(data);
			}
		});
	}
	div.find("p").wTooltip({callBefore: getConfigHelp, content: true});
}
