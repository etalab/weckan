/**
 * Membership requests specific features
 */
(function($, Utils, Config) {

    "use strict";

    var msg_container = 'section.form .container',
        group_title = $('section.form').data('group-title'),
        group_id = $('section.form').data('group-id'),
        mapping = {'{org}': group_title};

    $(function() {

        $('.member-role').editable({
            url: window.location,
            source: [
                {value: 'admin', text: Utils.i18n('role-admin')},
                {value: 'editor', text: Utils.i18n('role-editor')},
                {value: 'member', text: Utils.i18n('role-member')},
            ]
        });
    });

}(window.jQuery, window.Utils, window.EtalabConfig));
