/**
 * Dataset page specific features
 */
(function($, Utils) {

    "use strict";

    var dataset_id = '',
        dataset_name = '',
        dataset_title = '',
        default_container = '.dataset-container',
        community_container = '.community_container > div.container',
        mapping = {'{dataset}': dataset_title};

    $(function() {
        // Async feature handling
        $('a.featured').click(function() {
            var $this = $(this),
                api_url = $this.data('api');

            $.get(api_url, function(data) {
                if (data.featured) {
                    $this.removeClass('btn-default').addClass('btn-success');
                    $this.attr('title', $this.data('featured-title'));
                    Utils.success(Utils.i18n('is-featured'), community_container);
                } else {
                    $this.removeClass('btn-success').addClass('btn-default');
                    $this.attr('title', $this.data('unfeatured-title'));
                    Utils.success(Utils.i18n('is-unfeatured'), community_container);
                }
            }).error(function(e) {
                console.error(e);
                Utils.error(Utils.i18n('featured-error'), community_container);
            });

            return false;
        });

        // Async follow handling
        $('a.follow').click(function() {
            var $this = $(this),
                following = $this.data('is-following'),
                api_url = following ? $this.data('unfollow-api') : $this.data('follow-api'),
                payload = JSON.stringify({id: $this.data('organization-id')});

            Utils.ensure_user(Utils.i18n('login-to-follow-org'));

            $.post(api_url, payload, function(data) {
                var msg = following ? Utils.i18n('unfollowing-org') : Utils.i18n('following-org'),
                    label = following ? $this.data('follow-label') : $this.data('unfollow-label'),
                    icon = following ? 'eye-open': 'eye-close';

                $this.data('is-following', !following)
                    .attr('title', label)
                    .html('<span class="glyphicon glyphicon-' + icon + '"></span> ' + label);

                Utils.success(msg.replace('{org}',$this.data('organization-title')), default_container);
            }).error(function(e) {
                console.error(e.responseJSON.error.message);
                Utils.error(Utils.i18n('follow-org-error'), default_container);
            });

            return false;
        });


        // Async alert send
        $('a.send-alert').click(function() {
            var $this = $(this),
                api_url = $this.data('api'),
                $modal = $('#alert-modal');

            Utils.ensure_user(Utils.i18n('login-to-alert'));

            $modal.modal().find('form')[0].reset();
            $('#alert-submit').off('click').click(function() {
                var data = {
                    type: $modal.find('input[name="type"]:checked').val(),
                    comment: $modal.find('#comment').val()
                };
                console.log(data);
                $.post(api_url, data, function(data) {
                    var msg = Utils.i18n('alert-sent', mapping);
                    Utils.success(msg, default_container);
                }).error(function(e) {
                    var msg = Utils.i18n('alert-send-error', mapping);
                    Utils.error(msg, default_container);
                    console.error(e.responseJSON);
                }).always(function() {
                    $modal.modal('hide');
                });
                return false;
            });

            return false;
        });

        // Display hidden resources
        $('#more-resources').click(function() {
            var $this = $(this);
            $this.fadeOut();
            $('#all-resources').collapse().on('shown.bs.collapse', function() {
                $this.remove();
            });
            return false;
        });

        $('.resources-list div.list-group-item').click(function(e) {
            if (!$(e.target).parents('.tools, .resource-owner').length) {
                if ($(this).data('format') == 'html') {
                    window.open($(this).data('url'));
                } else {
                    window.location = $(this).data('url');
                }
            }
        });

    });

}(window.jQuery, window.Utils));
