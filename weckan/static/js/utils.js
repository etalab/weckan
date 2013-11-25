/**
 * Dataset page specific features
 */
(function($, swig){

    "use strict";

    var message_template = swig.compile($('#message-template').html());

    var Utils = window.Utils = {

        message: function(message, type, container) {
            container = container || 'section.default .container:first';
            $(container).prepend(message_template({
                level: type == 'error' ? 'danger' : type,
                message: message
            }));
        },

        error: function(message, container) {
            this.message(message, 'error', container);
        },

        success: function(message, container) {
            this.message(message, 'success', container);
        },

        i18n: function(key, replacements) {
            var msg = $('meta[name="'+key+'-i18n"]').attr('content');
            if (replacements) {
                for (var key in replacements) {
                    msg = msg.replace(key, replacements[key]);
                }
            }
            return msg;
        },

        ensure_user: function(reason) {
            var $sso = $('#sso-link');
            if ($sso.length) {
                var url = $sso.attr('href');
                if (reason) {
                    url += url.indexOf('?') > 0 ? '&' : '?';
                    url += 'message=' + encodeURIComponent(reason);
                }
                window.location = url;
            }
        }
    }

    // jQuery validate
    $.extend($.validator.messages, {
        required: Utils.i18n('valid-required'),
        remote: Utils.i18n('valid-remote'),
        email: Utils.i18n('valid-email'),
        url: Utils.i18n('valid-url'),
        date: Utils.i18n('valid-date'),
        dateISO: Utils.i18n('valid-date-iso'),
        number: Utils.i18n('valid-number'),
        digits: Utils.i18n('valid-digits'),
        creditcard: Utils.i18n('valid-creditcard'),
        equalTo: Utils.i18n('valid-equal-to'),
        maxlength: $.validator.format(Utils.i18n('valid-maxlength')),
        minlength: $.validator.format(Utils.i18n('valid-minlength')),
        rangelength: $.validator.format(Utils.i18n('valid-range-length')),
        range: $.validator.format(Utils.i18n('valid-range')),
        max: $.validator.format(Utils.i18n('valid-max')),
        min: $.validator.format(Utils.i18n('valid-min'))
    });

    return Utils;


}(window.jQuery, window.swig));
