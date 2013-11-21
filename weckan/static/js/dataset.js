/**
 * Dataset page specific features
 */
(function($, Utils) {

    "use strict";

    var default_container = '.dataset-container',
        community_container = '.community_container > div.container';

    $(function() {
        // Async feature handling
        $('a.featured').click(function() {
            var $this = $(this),
                api_url = $this.data('api');

            $.get(api_url, function(data) {
                if (data.featured) {
                    $this.removeClass('btn-default').addClass('btn-success');
                    $this.attr('title', $this.data('featured-title'));
                    Utils.success(Utils.translate('is-featured'), community_container);
                } else {
                    $this.removeClass('btn-success').addClass('btn-default');
                    $this.attr('title', $this.data('unfeatured-title'));
                    Utils.success(Utils.translate('is-unfeatured'), community_container);
                }
            }).error(function(e) {
                console.error(e);
                Utils.error(Utils.translate('featured-error'), community_container);
            });

            return false;
        });

        // Async follow handling
        $('a.follow').click(function() {
            var $this = $(this),
                following = $this.data('is-following'),
                api_url = following ? $this.data('unfollow-api') : $this.data('follow-api'),
                payload = JSON.stringify({id: $this.data('organization-id')});

            Utils.ensure_user(Utils.translate('login-to-follow-org'));

            $.post(api_url, payload, function(data) {
                var msg = following ? Utils.translate('unfollowing-org') : Utils.translate('following-org'),
                    label = following ? $this.data('follow-label') : $this.data('unfollow-label'),
                    icon = following ? 'eye-open': 'eye-close';

                $this.data('is-following', !following)
                    .attr('title', label)
                    .html('<span class="glyphicon glyphicon-' + icon + '"></span> ' + label);

                Utils.success(msg.replace('{org}',$this.data('organization-title')), default_container);
            }).error(function(e) {
                console.error(e.responseJSON.error.message);
                Utils.error(Utils.translate('follow-org-error'), default_container);
            });

            return false;
        });
    });

}(window.jQuery, window.Utils));
