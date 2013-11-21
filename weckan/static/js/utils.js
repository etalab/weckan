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

        translate: function(key) {
            return $('meta[name="'+key+'-translation"]').attr('content');
        },

        ensure_user: function() {
            var $sso = $('#sso-link');
            if ($sso.length) {
                window.location = $sso.attr('href');
            }
        }
    }

    return Utils;


}(window.jQuery, window.swig));
