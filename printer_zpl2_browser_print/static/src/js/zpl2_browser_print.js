odoo.define('printer_zpl2_browser_print.BrowserPrint', function (require) {
"use strict";

var widgetRegistry = require('web.widget_registry');
var core = require('web.core');
var Widget = require('web.Widget');

var _t = core._t;

var ZPL2BrowserPrint = Widget.extend({
    template: 'printer_zpl2_browser_print.BrowserPrint',
    events: {
        "change #zpl2_browser_print_selected_device": "_onDeviceSelected",
        "click .js_zpl2_browser_print_button": "_onPrintButtonClick"
    },

    _onPrintButtonClick: function (ev) {
        var label = $(".js_zpl2_browser_print_label_id");
        if (label[0].value == "") {
            alert(_("No label selected"));
            return;
        }
        if (this.selected_device == "") {
            alert(_("No printer selected"));
            return;
        }
        var self = this;
        this._rpc({
            model: 'printing.label.zpl2',
            method: 'browser_print_label',
            args: [parseInt(label[0].value)],
            context: this.options.context,
        }).then(function (result) {
            var labels = result;
            for (var i = 0; i < labels.length; i++) {
                self._writeToSelectedPrinter(labels[i]);
            }
        });
    },

    _onDeviceSelected: function (ev) {
        var select = ev.currentTarget;
        for(var i = 0; i < this.devices.length; ++i){
            if(select.value == this.devices[i].uid)
            {
                this.selected_device = this.devices[i];
                return;
            }
        }
    },

    _writeToSelectedPrinter: function (dataToWrite) {
        this.selected_device.send(dataToWrite, undefined, this.errorCallback);
    },

    errorCallback: function(errorMessage) {
        alert(_t("Error: ") + errorMessage);
    },

    init: function (parent, options) {
        this._super.apply(this, arguments);
        this.devices = [];
        this.options = options;
        this.selected_device = "";
    },

    start: function () {
        this._super.apply(this, arguments);
        var self = this;
        //Get the default device from the application as a first step. Discovery takes longer to complete.
	    BrowserPrint.getDefaultDevice("printer", function(device)
			{
				//Add device to list of devices and to html select element
				self.selected_device = device;
				self.devices.push(device);
				var html_select = self.$('#zpl2_browser_print_selected_device');
				var option = document.createElement("option");
				option.text = device.name;
				html_select[0].add(option);

				//Discover any other devices available to the application
				BrowserPrint.getLocalDevices(function(device_list){
					for(var i = 0; i < device_list.length; i++)
					{
						//Add device to list of devices and to html select element
						var device = device_list[i];
						if(!self.selected_device || device.uid != self.selected_device.uid)
						{
							self.devices.push(device);
							var option = document.createElement("option");
							option.text = device.name;
							option.value = device.uid;
							html_select[0].add(option);
						}
					}

				}, function() {
				    alert(_t("Error getting local devices"));
                }, "printer");

			}, function(error){
			    if (error == "") {
			        alert(_t("Error getting local devices"))
			    }
			    else {
				    alert(error);
                }
        })
    },
});

widgetRegistry.add('zpl2_browser_print', ZPL2BrowserPrint);
return ZPL2BrowserPrint;

});
