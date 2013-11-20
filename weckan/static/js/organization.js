/**
 * Dataset page specific features
 */
(function($, swig){

    "use strict";

    var message_template = swig.compile($('#message-template').html());

    var display_message = function(message, type, container) {
        container = container || '.organization-container';
        $(container).prepend(message_template({
            level: type == 'error' ? 'danger' : type,
            message: message
        }));
    };

    var translate = function(key) {
        return $('meta[name="'+key+'-translation"]').attr('content');
    };

    $(function() {
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
