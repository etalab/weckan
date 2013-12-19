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
        $('a.membership-accept').click(function() {
            var $this = $(this),
                api_url = $this.data('api');

            Utils.ensure_user(Utils.i18n('login-for-pending'));

            $.post(api_url, {}, function(data) {
                var msg = Utils.i18n('membership-accepted', mapping);
                Utils.success(msg, msg_container);
                $this.closest('.pending-request').remove();
                if ($('.pending-request').length == 0) {
                    $('.empty').removeClass('hide');
                }
            }).error(function(e) {
                var msg = Utils.i18n('membership-response-error', mapping);
                console.error(e.responseJSON);
                Utils.error(msg, msg_container);
            });

            return false;
        });

        $('a.membership-refuse').click(function() {
            var $this = $(this),
                api_url = $this.data('api'),
                $modal = $('#refusal-modal'),
                $form = $modal.find('form');

            Utils.ensure_user(Utils.i18n('login-for-pending'));

            $modal.modal();
            $form.validate(Config.rules);
            $form[0].reset();
            $('#refusal-submit').off('click').click(function() {
                if ($modal.find('form').valid()) {
                    var data = {comment: $modal.find('#comment').val()};
                    $.post(api_url, data, function(data) {
                        var msg = Utils.i18n('membership-refused', mapping);
                        Utils.success(msg, msg_container);
                        $this.closest('.pending-request').remove();
                        if ($('.pending-request').length == 0) {
                            $('.empty').removeClass('hide');
                        }
                    }).error(function(e) {
                        var msg = Utils.i18n('membership-response-error', mapping);
                        Utils.error(msg, msg_container);
                        console.error(e.responseJSON);
                    }).always(function() {
                        $modal.modal('hide');
                    });
                }
                return false;
            });

            return false;
        });
    });

}(window.jQuery, window.Utils, window.EtalabConfig));
