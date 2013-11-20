/**
 * Dataset page specific features
 */
(function($, swig){

    "use strict";

    var message_template = swig.compile($('#message-template').html()),
        community_container = '.community_container > div.container';

    var display_message = function(message, type, container) {
        container = container || '.dataset-container';
        $(container).prepend(message_template({
            level: type == 'error' ? 'danger' : type,
            message: message
        }));
    };

    var translate = function(key) {
        return $('meta[name="'+key+'-translation"]').attr('content');
    };

    $(function() {
        // Async feature handling
        $('a.featured').click(function() {
            var $this = $(this),
                api_url = $this.data('api');

            $.get(api_url, function(data) {
                if (data.featured) {
                    $this.removeClass('btn-default').addClass('btn-success');
                    $this.attr('title', $this.data('featured-title'));
                    display_message(translate('is-featured'), 'success', community_container);
                } else {
                    $this.removeClass('btn-success').addClass('btn-default');
                    $this.attr('title', $this.data('unfeatured-title'));
                    display_message(translate('is-unfeatured'), 'success', community_container);
                }
            }).error(function(e) {
                console.error(e);
                display_message(translate('featured-error'), 'error', community_container);
            });

            return false;
        });

        // Async follow handling
        $('a.follow').click(function() {
            var $this = $(this),
                following = $this.data('is-following'),
                api_url = following ? $this.data('unfollow-api') : $this.data('follow-api'),
                payload = JSON.stringify({id: $this.data('organization-id')});

            $.post(api_url, payload, function(data) {
                var msg = following ? translate('unfollowing-org') : translate('following-org'),
                    label = following ? $this.data('follow-label') : $this.data('unfollow-label'),
                    icon = following ? 'eye-open': 'eye-close';

                $this.data('is-following', !following)
                    .attr('title', label)
                    .html('<span class="glyphicon glyphicon-' + icon + '"></span> ' + label);

                display_message(msg.replace('{org}',$this.data('organization-title')), 'success');
            }).error(function(e) {
                console.error(e.responseJSON.error.message);
                display_message(translate('follow-org-error'), 'error');
            });

            return false;
        });
    });

}(window.jQuery, window.swig));
