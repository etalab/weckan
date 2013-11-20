/**
 * Dataset page specific features
 */
(function($, Utils) {

    "use strict";

    var msg_container = '.organization-container';

    $(function() {
        // Async follow handling
        $('a.follow').click(function() {
            var $this = $(this),
                following = $this.data('is-following'),
                api_url = following ? $this.data('unfollow-api') : $this.data('follow-api'),
                payload = JSON.stringify({id: $this.data('organization-id')});

            $.post(api_url, payload, function(data) {
                var msg = following ? Utils.translate('unfollowing-org') : Utils.translate('following-org'),
                    label = following ? $this.data('follow-label') : $this.data('unfollow-label'),
                    icon = following ? 'eye-open': 'eye-close';

                $this.data('is-following', !following)
                    .attr('title', label)
                    .html('<span class="glyphicon glyphicon-' + icon + '"></span> ' + label);

                Utils.success(msg.replace('{org}',$this.data('organization-title')), msg_container);
            }).error(function(e) {
                console.error(e.responseJSON.error.message);
                Utils.error(Utils.translate('follow-org-error'), msg_container);
            });

            return false;
        });
    });

}(window.jQuery, window.Utils));
