/**
 * Dataset page specific features
 */
(function($, Utils, VALIDATION_RULES) {

    "use strict";

    var msg_container = '.organization-container',
        org_title = $('.organization-container').data('organization-title'),
        org_id = $('.organization-container').data('organization-id'),
        mapping = {'{org}': org_title};

    $(function() {
        // Async follow handling
        $('a.follow').click(function() {
            var $this = $(this),
                following = $this.data('is-following'),
                api_url = following ? $this.data('unfollow-api') : $this.data('follow-api'),
                payload = JSON.stringify({id: org_id});

            Utils.ensure_user(Utils.i18n('login-to-follow-org'));

            $.post(api_url, payload, function(data) {
                var msg = Utils.i18n(following ? 'unfollowing-org' : 'following-org', mapping),
                    label = following ? $this.data('follow-label') : $this.data('unfollow-label'),
                    icon = following ? 'eye-open': 'eye-close';

                $this.data('is-following', !following)
                    .attr('title', label)
                    .html('<span class="glyphicon glyphicon-' + icon + '"></span> ' + label);

                Utils.success(msg, msg_container);
            }).error(function(e) {
                console.error(e.responseJSON.error.message);
                Utils.error(Utils.i18n('follow-org-error'), msg_container);
            });

            return false;
        });

        // Async membership request
        $('a.membership').click(function() {
            var $this = $(this),
                api_url = $this.data('api'),
                $modal = $('#membership-modal'),
                click_handler;

            Utils.ensure_user(Utils.i18n('login-for-membership'));

            click_handler = function() {
                var data = {comment: $modal.find('#comment').val()};
                $.post(api_url, data, function(data) {
                    var msg = Utils.i18n('membership-requested', mapping);
                    Utils.success(msg, msg_container);
                    $this.remove();
                    $('#pending-button').removeClass('hide');
                }).error(function(e) {
                    var msg = Utils.i18n('membership-request-error', mapping);
                    Utils.error(msg, msg_container);
                    console.error(e.responseJSON);
                }).always(function() {
                    $modal.modal('hide');
                    $('#membership-submit').off('click', click_handler);
                });
                return false;
            };

            $modal.modal();
            $('#membership-submit').click(click_handler);

            return false;
        });

        $('a.membership-accept').click(function() {
            var $this = $(this),
                api_url = $this.data('api');

            Utils.ensure_user(Utils.i18n('login-for-pending'));

            $.post(api_url, {}, function(data) {
                var msg = Utils.i18n('membership-accepted', mapping);
                Utils.success(msg, msg_container);
                $this.closest('.pending-request').remove();
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
                click_handler;

            Utils.ensure_user(Utils.i18n('login-for-pending'));

            click_handler = function() {
                if ($modal.find('form').valid()) {
                    var data = {comment: $modal.find('#comment').val()};
                    $.post(api_url, data, function(data) {
                        var msg = Utils.i18n('membership-refused', mapping);
                        Utils.success(msg, msg_container);
                        $this.closest('.pending-request').remove();
                    }).error(function(e) {
                        var msg = Utils.i18n('membership-response-error', mapping);
                        Utils.error(msg, msg_container);
                        console.error(e.responseJSON);
                    }).always(function() {
                        $modal.modal('hide');
                        $('#refusal-submit').off('click', click_handler);
                    });
                }
                return false;
            };

            $modal.modal().find('form').validate(VALIDATION_RULES);
            $('#refusal-submit').click(click_handler);

            return false;
        });
    });

}(window.jQuery, window.Utils, window.ETALAB_VALIDATION_RULES));
