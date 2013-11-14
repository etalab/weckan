/**
 * Homepage specific features
 */
(function($, swig){

    "use strict";


    var message_template = swig.compile($('#message-template').html());

    var display_message = function(message, type, container) {
        container = container || 'section.default .container';
        $(container).prepend(message_template({
            level: type == 'error' ? 'danger' : type,
            message: message
        }));
    };

    var translate = function(key) {
        return $('meta[name="'+key+'-translation"]').attr('content');
    };

    $(function() {
        // Update carousel ellipsis on change
        $('#home-carousel .title').on('slide.bs.carousel', function() {
            $(this).trigger('update');
        });

        // Async feature handling
        $('a.unfeature').click(function() {
            var $this = $(this),
                api_url = $this.data('api');

            if (!$this.hasClass('disabled')) {
                $.get(api_url, function(data) {
                    $this.removeClass('btn-warning').addClass('btn-danger').addClass('disabled');
                    $this.removeAttr('href').attr('title', translate('is-unfeatured'));
                    display_message(translate('is-unfeatured'), 'success');
                }).error(function(e) {
                    console.error(e);
                    display_message(translate('featured-error'), 'error');
                });
            }


            return false;
        });
    });

}(window.jQuery, window.swig));
